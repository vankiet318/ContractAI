import re
from statistics import median

from .models import TextBlock, BlockFeatures


class FeatureExtractor:
    """
    Extract structural features from TextBlock.

    This component does NOT decide the final document structure.

    It only answers questions such as:
    - Does this block have numbering?
    - What is its numbering level?
    - Does it look like a heading?
    - How does its visual style compare to the document?
    """

    # ---------------------------------------------------------
    # Numbering patterns
    # ---------------------------------------------------------

    NUMBERING_PATTERNS = [
        # 1.
        # 1)
        re.compile(
            r"^(?P<number>\d+)[.)](?:\s+|$)"
        ),

        # 1.2
        # 1.2.3
        # 1.2.3.
        re.compile(
            r"^(?P<number>\d+(?:\.\d+)+)\.?(?:\s+|$)"
        ),

        # A.
        # A)
        re.compile(
            r"^(?P<number>[A-Z])[.)](?:\s+|$)"
        ),

        # a.
        # a)
        re.compile(
            r"^(?P<number>[a-z])[.)](?:\s+|$)"
        ),

        # (a)
        # (1)
        re.compile(
            r"^\((?P<number>[a-zA-Z0-9]+)\)(?:\s+|$)"
        ),

        # I.
        # IV.
        # XII.
        re.compile(
            r"^(?P<number>[IVXLCDM]+)\.(?:\s+|$)",
            re.IGNORECASE,
        ),
    ]

    ROMAN_PATTERN = re.compile(
        r"^[IVXLCDM]+$",
        re.IGNORECASE,
    )

    ALPHABETIC_PATTERN = re.compile(
        r"^[A-Za-z]$"
    )

    NUMERIC_PATTERN = re.compile(
        r"^\d+$"
    )

    HIERARCHICAL_NUMERIC_PATTERN = re.compile(
        r"^\d+(?:\.\d+)+$"
    )

    def extract(
        self,
        blocks: list[TextBlock],
    ) -> list[BlockFeatures]:

        if not blocks:
            return []

        body_font_size = self._infer_body_font_size(blocks)

        features: list[BlockFeatures] = []

        for block in blocks:

            text = block.text.strip()

            numbering = self._extract_numbering(text)

            numbering_level = (
                self._get_numbering_level(numbering)
                if numbering
                else None
            )

            is_uppercase = self._is_uppercase(text)

            ends_with_punctuation = (
                text.endswith(
                    (
                        ".",
                        ",",
                        ";",
                        ":",
                        "?",
                        "!",
                    )
                )
            )

            looks_like_heading = self._looks_like_heading(
                block=block,
                body_font_size=body_font_size,
                numbering=numbering,
                numbering_level=numbering_level,
            )

            features.append(
                BlockFeatures(
                    text=text,
                    page_number=block.page_number,

                    text_length=len(text),

                    word_count=len(text.split()),

                    is_uppercase=is_uppercase,

                    ends_with_punctuation=ends_with_punctuation,

                    font_size=block.font_size or 0.0,

                    is_bold=block.is_bold,

                    is_italic=block.is_italic,

                    x0=block.x0 or 0.0,
                    y0=block.y0 or 0.0,
                    x1=block.x1 or 0.0,
                    y1=block.y1 or 0.0,

                    vertical_gap_before=block.vertical_gap_before or 0.0,
                    vertical_gap_after=block.vertical_gap_after or 0.0,
                    indent=block.indent or 0.0,

                    numbering=numbering,

                    numbering_level=numbering_level,

                    looks_like_heading=looks_like_heading,
                )
            )

        return features

    # =========================================================
    # Numbering
    # =========================================================

    def _extract_numbering(
        self,
        text: str,
    ) -> str | None:

        if not text:
            return None

        for pattern in self.NUMBERING_PATTERNS:

            match = pattern.match(text)

            if match:
                return match.group("number")

        return None

    def _get_numbering_level(
        self,
        numbering: str,
    ) -> int:

        # 1
        if self.NUMERIC_PATTERN.fullmatch(numbering):
            return 1

        # 1.2
        # 1.2.3
        if self.HIERARCHICAL_NUMERIC_PATTERN.fullmatch(
            numbering
        ):
            return numbering.count(".") + 1

        # Roman numerals
        if self.ROMAN_PATTERN.fullmatch(numbering):
            return 1

        # A / a
        if self.ALPHABETIC_PATTERN.fullmatch(numbering):
            return 4

        return 1

    # =========================================================
    # Heading detection
    # =========================================================

    def _looks_like_heading(
        self,
        *,
        block: TextBlock,
        body_font_size: float,
        numbering: str | None,
        numbering_level: int | None,
    ) -> bool:

        text = block.text.strip()

        if not text:
            return False

        # Header/footer should never become document headings.
        if block.is_header or block.is_footer:
            return False

        # Extremely long text is unlikely to be a heading.
        if len(text) > 200:
            return False

        score = 0.0

        # -----------------------------------------------------
        # Numbering
        # -----------------------------------------------------

        if numbering is not None:

            score += 0.30

            # Deep numbering such as 1.2.1 is useful evidence
            # but should not alone guarantee a heading.
            if numbering_level is not None:
                if numbering_level <= 3:
                    score += 0.05

        # -----------------------------------------------------
        # Bold
        # -----------------------------------------------------

        if block.is_bold:
            score += 0.20

        # -----------------------------------------------------
        # Font size
        # -----------------------------------------------------

        if (
            body_font_size > 0
            and block.font_size is not None
        ):

            if block.font_size >= body_font_size * 1.20:
                score += 0.25

            elif block.font_size >= body_font_size * 1.10:
                score += 0.15

        # -----------------------------------------------------
        # Short text
        # -----------------------------------------------------

        word_count = len(text.split())

        if word_count <= 10:
            score += 0.10

        elif word_count <= 15:
            score += 0.05

        # -----------------------------------------------------
        # Uppercase
        # -----------------------------------------------------

        if self._is_uppercase(text):
            score += 0.10

        # -----------------------------------------------------
        # Vertical spacing
        # -----------------------------------------------------

        if (
            block.vertical_gap_before is not None
            and block.vertical_gap_before > 8
        ):
            score += 0.10

        # -----------------------------------------------------
        # Heading usually doesn't end with punctuation.
        # -----------------------------------------------------

        if not text.endswith(
            (".", ",", ";", ":")
        ):
            score += 0.05

        # -----------------------------------------------------
        # Very long sentence penalty
        # -----------------------------------------------------

        if word_count > 25:
            score -= 0.20

        return score >= 0.50

    # =========================================================
    # Document-level statistics
    # =========================================================

    def _infer_body_font_size(
        self,
        blocks: list[TextBlock],
    ) -> float:

        font_sizes = [
            block.font_size
            for block in blocks
            if (
                block.font_size is not None
                and block.font_size > 0
                and not block.is_header
                and not block.is_footer
            )
        ]

        if not font_sizes:
            return 0.0

        return float(median(font_sizes))

    # =========================================================
    # Helpers
    # =========================================================

    @staticmethod
    def _is_uppercase(
        text: str,
    ) -> bool:

        letters = [
            char
            for char in text
            if char.isalpha()
        ]

        if not letters:
            return False

        return all(
            char.isupper()
            for char in letters
        )