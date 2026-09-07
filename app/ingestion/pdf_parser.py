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

        for span in spans:
            text = span.get("text", "")

            if not text:
                continue

            text_parts.append(text)

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
    def _get_primary_font(font_names: list[str]) -> str | None:
        if not font_names:
            return None

        return font_names[0]