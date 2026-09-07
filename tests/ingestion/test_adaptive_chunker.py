from app.ingestion.adaptive_chunker import AdaptiveChunker
from app.ingestion.models import StructureNode


def test_chunk_preserves_structure():

    root = StructureNode(
        node_type="level_1",
        title="BẢO MẬT",
        number="6",
        level=1,
        page_start=3,
        page_end=3,
    )

    child = StructureNode(
        node_type="level_2",
        title="Ngoại lệ",
        number="6.2",
        level=2,
        page_start=3,
        page_end=3,
        text=(
            "Nghĩa vụ bảo mật không áp dụng "
            "trong trường hợp pháp luật yêu cầu "
            "công bố thông tin."
        ),
    )

    root.children.append(child)

    chunker = AdaptiveChunker(
        max_chars=1500,
    )

    chunks = chunker.chunk(
        roots=[root],
        document_id="doc-001",
    )

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk.document_id == "doc-001"
    assert chunk.section_number == "6.2"

    assert chunk.parent_number == "6"

    assert chunk.structure_path == [
        "6",
        "6.2",
    ]

    assert "BẢO MẬT" in chunk.text
    assert "Ngoại lệ" in chunk.text
    assert "Nghĩa vụ bảo mật" in chunk.text