import pymupdf

from .models import TextBlock


class PDFParser:
    """
    Generic PDF parser.

    Responsibilities:
    - Extract text from PDF
    - Preserve page information
    - Preserve text layout information
    - Preserve font/style information
    - Return a normalized list of TextBlock

    This parser does NOT try to determine:
    - heading
    - section
    - clause
    - paragraph
    - document type

    Those decisions belong to later stages.
    """

    def parse(self, file_path: str) -> list[TextBlock]:
        document = pymupdf.open(file_path)

        try:
            blocks: list[TextBlock] = []

            for page_number, page in enumerate(document, start=1):
                page_blocks = self._parse_page(
                    page=page,
                    page_number=page_number,
                )

                blocks.extend(page_blocks)

            return blocks

        finally:
            document.close()

    def _parse_page(
        self,
        page: pymupdf.Page,
        page_number: int,
    ) -> list[TextBlock]:

        text_data = page.get_text("dict")

        blocks: list[TextBlock] = []

        for block in text_data.get("blocks", []):
            # Image / drawing blocks do not contain "lines"
            if block.get("type") != 0:
                continue

            for line in block.get("lines", []):
                text_block = self._parse_line(
                    line=line,
                    page_number=page_number,
                )

                if text_block is not None:
                    blocks.append(text_block)

        return blocks

    def _parse_line(
        self,
        line: dict,
        page_number: int,
    ) -> TextBlock | None:

        spans = line.get("spans", [])

        if not spans:
            return None

        text_parts: list[str] = []

        font_sizes: list[float] = []
        font_names: list[str] = []

        is_bold = False
        is_italic = False

        previous_span_x1: float | None = None

        for span in spans:
            text = span.get("text", "")

            if not text:
                continue

            span_bbox = span.get("bbox", (0, 0, 0, 0))
            span_x0 = float(span_bbox[0])

            previous_text_ends_with_space = (
                bool(text_parts) and text_parts[-1][-1].isspace()
            )

            if (
                not previous_text_ends_with_space
                and not text[0].isspace()
                and self._has_gap_between_spans(
                    previous_span_x1=previous_span_x1,
                    span_x0=span_x0,
                    span_font_size=span.get("size"),
                )
            ):
                text_parts.append(" ")

            text_parts.append(text)

            previous_span_x1 = float(span_bbox[2])

            font_size = span.get("size")
            if font_size is not None:
                font_sizes.append(float(font_size))

            font_name = span.get("font")
            if font_name:
                font_names.append(font_name)

                font_name_lower = font_name.lower()

                if "bold" in font_name_lower:
                    is_bold = True

                if "italic" in font_name_lower or "oblique" in font_name_lower:
                    is_italic = True

        text = "".join(text_parts).strip()

        if not text:
            return None

        bbox = line.get("bbox", (0, 0, 0, 0))

        return TextBlock(
            text=text,
            page_number=page_number,

            font_size=max(font_sizes) if font_sizes else None,
            font_name=self._get_primary_font(font_names),

            is_bold=is_bold,
            is_italic=is_italic,

            x0=float(bbox[0]),
            y0=float(bbox[1]),
            x1=float(bbox[2]),
            y1=float(bbox[3]),
        )

    @staticmethod
    def _has_gap_between_spans(
        previous_span_x1: float | None,
        span_x0: float,
        span_font_size: float | None,
    ) -> bool:

        if previous_span_x1 is None:
            return False

        gap = span_x0 - previous_span_x1

        if gap <= 0:
            return False

        font_size = span_font_size or 10.0

        return gap > font_size * 0.15

    @staticmethod
    def _get_primary_font(font_names: list[str]) -> str | None:
        if not font_names:
            return None

        return font_names[0]