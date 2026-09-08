from dataclasses import dataclass, field
from typing import Any


@dataclass
class TextBlock:
    text: str
    page_number: int

    font_size: float | None = None
    font_name: str | None = None

    is_bold: bool = False
    is_italic: bool = False

    x0: float | None = None
    y0: float | None = None
    x1: float | None = None
    y1: float | None = None

    vertical_gap_before: float | None = None
    vertical_gap_after: float | None = None

    indent: float | None = None

    is_header: bool = False
    is_footer: bool = False

    block_id: int | None = None
    is_continuation: bool = False


@dataclass
class BlockFeatures:
    text: str
    page_number: int

    text_length: int
    word_count: int

    is_uppercase: bool
    ends_with_punctuation: bool

    font_size: float
    is_bold: bool
    is_italic: bool

    x0: float
    y0: float
    x1: float
    y1: float

    vertical_gap_before: float
    vertical_gap_after: float
    indent: float

    numbering: str | None = None
    numbering_level: int | None = None

    looks_like_heading: bool = False


@dataclass
class HeadingStyle:
    level: int

    font_size: float
    is_bold: bool
    is_italic: bool

    indent: float
    avg_gap_before: float
    avg_gap_after: float

    examples: list[str] = field(default_factory=list)


@dataclass
class StructureNode:
    node_type: str
    title: str
    text: str = ""

    number: str | None = None
    level: int = 0
    page_start: int | None = None
    page_end: int | None = None

    children: list["StructureNode"] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentSchema:
    numbering_patterns: dict[int, str] = field(default_factory=dict)

    max_depth: int = 0

    heading_font_threshold: float = 0.0

    heading_styles: dict[int, HeadingStyle] = field(
        default_factory=dict
    )

@dataclass(frozen=True)
class ChunkIdentity:
    document_id: str
    session_id: str


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str

    text: str

    page_start: int
    page_end: int

    section_number: str | None = None
    section_title: str | None = None
    session_id: str | None = None
    parent_number: str | None = None
    parent_title: str | None = None

    structure_path: list[str] = field(
        default_factory=list
    )

    chunk_index: int = 0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )