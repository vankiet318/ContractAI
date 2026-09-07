import re
from collections import Counter, defaultdict

from .models import TextBlock


class LayoutAnalyzer:
    """
    Analyze the visual/layout characteristics of extracted PDF text.

    Responsibilities:
    - Detect repeated headers and footers
    - Calculate vertical spacing
    - Calculate indentation
    - Assign logical block IDs
    - Detect paragraph continuation

    This class does NOT determine document semantics such as:
    - section
    - subsection
    - clause
    - article

    Those decisions belong to later stages.
    """

    def __init__(
        self,
        header_ratio: float = 0.25,
        footer_ratio: float = 0.85,
        repeated_threshold: float = 0.6,
        paragraph_gap_threshold: float = 8.0,
    ):
        self.header_ratio = header_ratio
        self.footer_ratio = footer_ratio
        self.repeated_threshold = repeated_threshold
        self.paragraph_gap_threshold = paragraph_gap_threshold

    def analyze(
        self,
        blocks: list[TextBlock],
        page_heights: dict[int, float] | None = None,
    ) -> list[TextBlock]:

        if not blocks:
            return []

        blocks = sorted(
            blocks,
            key=lambda block: (
                block.page_number,
                block.y0 or 0.0,
                block.x0 or 0.0,
            ),
        )

        self._calculate_vertical_gaps(blocks)
        self._calculate_indentation(blocks)

        repeated_headers, repeated_footers = self._detect_repeated_headers_footers(
            blocks,
            page_heights,
        )

        self._mark_headers_footers(
            blocks,
            repeated_headers,
            repeated_footers,
            page_heights,
        )

        self._assign_block_ids(blocks)

        return blocks

    # ------------------------------------------------------------------
    # Vertical spacing
    # ------------------------------------------------------------------

    def _calculate_vertical_gaps(
        self,
        blocks: list[TextBlock],
    ) -> None:

        previous_by_page: dict[int, TextBlock] = {}

        for block in blocks:

            previous = previous_by_page.get(block.page_number)

            if previous is None:
                block.vertical_gap_before = None
            else:
                previous_bottom = previous.y1 or 0.0
                current_top = block.y0 or 0.0

                gap = current_top - previous_bottom

                block.vertical_gap_before = max(gap, 0.0)

                previous.vertical_gap_after = block.vertical_gap_before

            previous_by_page[block.page_number] = block

    # ------------------------------------------------------------------
    # Indentation
    # ------------------------------------------------------------------

    def _calculate_indentation(
        self,
        blocks: list[TextBlock],
    ) -> None:

        min_x_by_page: dict[int, float] = defaultdict(lambda: float("inf"))

        for block in blocks:

            if block.x0 is None:
                continue

            min_x_by_page[block.page_number] = min(
                min_x_by_page[block.page_number],
                block.x0,
            )

        for block in blocks:

            if block.x0 is None:
                block.indent = None
                continue

            page_min_x = min_x_by_page[block.page_number]

            block.indent = max(
                block.x0 - page_min_x,
                0.0,
            )

    # ------------------------------------------------------------------
    # Header / Footer detection
    # ------------------------------------------------------------------

    def _detect_repeated_headers_footers(
        self,
        blocks: list[TextBlock],
        page_heights: dict[int, float] | None,
    ) -> tuple[set[str], set[str]]:

        page_count = len(
            {
                block.page_number
                for block in blocks
            }
        )

        if page_count <= 1:
            return set(), set()

        header_candidates: defaultdict[str, set[int]] = defaultdict(set)
        footer_candidates: defaultdict[str, set[int]] = defaultdict(set)

        for block in blocks:

            normalized = self._normalize_text(block.text)

            if not normalized:
                continue

            if self._is_header_position(
                block,
                page_heights,
            ):
                header_candidates[normalized].add(
                    block.page_number
                )

            if self._is_footer_position(
                block,
                page_heights,
            ):
                footer_candidates[normalized].add(
                    block.page_number
                )

        threshold = max(
            2,
            int(page_count * self.repeated_threshold),
        )

        repeated_headers = {
            text
            for text, pages in header_candidates.items()
            if len(pages) >= threshold
        }

        repeated_footers = {
            text
            for text, pages in footer_candidates.items()
            if len(pages) >= threshold
        }

        return repeated_headers, repeated_footers

    def _is_header_position(
        self,
        block: TextBlock,
        page_heights: dict[int, float] | None,
    ) -> bool:

        if page_heights is None:
            # Without page dimensions we use an absolute heuristic.
            return (block.y0 or 0.0) < 80.0

        height = page_heights.get(block.page_number)

        if height is None:
            return False

        return (block.y0 or 0.0) < height * self.header_ratio

    def _is_footer_position(
        self,
        block: TextBlock,
        page_heights: dict[int, float] | None,
    ) -> bool:

        if page_heights is None:
            return (block.y1 or 0.0) > 700.0

        height = page_heights.get(block.page_number)

        if height is None:
            return False

        return (block.y1 or 0.0) > height * self.footer_ratio

    def _mark_headers_footers(
        self,
        blocks: list[TextBlock],
        repeated_headers: set[str],
        repeated_footers: set[str],
        page_heights: dict[int, float] | None,
    ) -> None:

        for block in blocks:

            normalized = self._normalize_text(block.text)

            if normalized in repeated_headers:
                if self._is_header_position(
                    block,
                    page_heights,
                ):
                    block.is_header = True

            if normalized in repeated_footers:
                if self._is_footer_position(
                    block,
                    page_heights,
                ):
                    block.is_footer = True

    # ------------------------------------------------------------------
    # Logical block grouping
    # ------------------------------------------------------------------

    def _assign_block_ids(
        self,
        blocks: list[TextBlock],
    ) -> None:

        block_id = 0
        previous: TextBlock | None = None

        for block in blocks:

            if block.is_header or block.is_footer:
                continue

            if previous is None:
                block_id += 1
                block.block_id = block_id
                previous = block
                continue

            if block.page_number != previous.page_number:

                block_id += 1
                block.block_id = block_id

            elif self._starts_new_logical_block(
                previous,
                block,
            ):

                block_id += 1
                block.block_id = block_id

            else:

                block.block_id = block_id
                block.is_continuation = True

            previous = block

    def _starts_new_logical_block(
        self,
        previous: TextBlock,
        current: TextBlock,
    ) -> bool:

        # Large vertical gap usually indicates a new paragraph/heading.
        if (
            current.vertical_gap_before is not None
            and current.vertical_gap_before
            > self.paragraph_gap_threshold
        ):
            return True

        # Different font size can indicate a heading/style change.
        if (
            previous.font_size is not None
            and current.font_size is not None
            and abs(previous.font_size - current.font_size) > 1.5
        ):
            return True

        # Bold/normal transition.
        if previous.is_bold != current.is_bold:
            return True

        # Strong indentation change.
        if (
            previous.indent is not None
            and current.indent is not None
            and abs(previous.indent - current.indent) > 15
        ):
            return True

        # Numbered item usually starts a new logical block.
        if self._looks_numbered(current.text):
            return True

        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = text.lower().strip()

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text

    @staticmethod
    def _looks_numbered(text: str) -> bool:
        patterns = [
            r"^\d+[.)]\s+",
            r"^\d+(?:\.\d+)+[.)]?\s+",
            r"^[a-zA-Z][.)]\s+",
            r"^\([a-zA-Z0-9]+\)\s+",
            r"^[IVXLCDM]+[.)]\s+",
        ]

        return any(
            re.match(pattern, text, re.IGNORECASE)
            for pattern in patterns
        )