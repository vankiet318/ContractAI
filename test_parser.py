from app.ingestion.pdf_parser import PDFParser
from app.ingestion.layout_analyzer import LayoutAnalyzer


PDF_PATH = "data/raw/Hop_Dong_Dich_Vu_Mau.pdf"


def main():
    parser = PDFParser()

    blocks = parser.parse(PDF_PATH)

    print(f"Raw blocks: {len(blocks)}")

    analyzer = LayoutAnalyzer()

    blocks = analyzer.analyze(blocks)

    print("\n===== LAYOUT ANALYSIS =====\n")

    for block in blocks:

        print(
            f"[Page {block.page_number}] "
            f"[ID={block.block_id}] "
            f"[Header={block.is_header}] "
            f"[Footer={block.is_footer}] "
            f"[Continue={block.is_continuation}] "
            f"[Gap={block.vertical_gap_before}] "
            f"[Indent={block.indent:.2f}] "
            f"{block.text}"
        )


if __name__ == "__main__":
    main()