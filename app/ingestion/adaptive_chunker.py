import re
from uuid import uuid4

from .models import DocumentChunk, StructureNode


class AdaptiveChunker:
    """
    Convert hierarchical document nodes into retrieval chunks.

    Chunking strategy:
    1. Keep the structural context.
    2. Prefer paragraph boundaries.
    3. If a paragraph is too long, split by sentence.
    4. If a sentence is still too long, split by characters.
    """

    def __init__(
        self,
        max_chars: int = 1500,
        overlap_chars: int = 200,
    ):
        if max_chars <= 0:
            raise ValueError("max_chars must be > 0")

        if overlap_chars < 0:
            raise ValueError("overlap_chars must be >= 0")

        if overlap_chars >= max_chars:
            raise ValueError(
                "overlap_chars must be smaller than max_chars"
            )

        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def chunk(
        self,
        roots: list[StructureNode],
        document_id: str,
    ) -> list[DocumentChunk]:

        chunks: list[DocumentChunk] = []

        for root in roots:
            self._process_node(
                node=root,
                document_id=document_id,
                parents=[],
                chunks=chunks,
            )

        self._assign_chunk_indices(chunks)

        return chunks

    def _process_node(
        self,
        node: StructureNode,
        document_id: str,
        parents: list[StructureNode],
        chunks: list[DocumentChunk],
    ) -> None:

        current_path = parents + [node]

        if node.text.strip():
            node_chunks = self._create_chunks_for_node(
                node=node,
                document_id=document_id,
                path=current_path,
            )

            chunks.extend(node_chunks)

        for child in node.children:
            self._process_node(
                node=child,
                document_id=document_id,
                parents=current_path,
                chunks=chunks,
            )

    def _create_chunks_for_node(
        self,
        node: StructureNode,
        document_id: str,
        path: list[StructureNode],
    ) -> list[DocumentChunk]:

        context = self._build_context(path)
        text = self._normalize_text(node.text)

        if not text:
            return []

        content_limit = self.max_chars - len(context) - 2

        if content_limit <= 0:
            raise ValueError(
                "max_chars is too small for structural context"
            )

        pieces = self._adaptive_split(
            text=text,
            max_chars=content_limit,
        )

        return [
            self._create_chunk(
                node=node,
                document_id=document_id,
                text=f"{context}\n\n{piece}",
                path=path,
            )
            for piece in pieces
        ]

    # ---------------------------------------------------------
    # Adaptive splitting
    # ---------------------------------------------------------

    def _adaptive_split(
        self,
        text: str,
        max_chars: int,
    ) -> list[str]:

        if len(text) <= max_chars:
            return [text]

        paragraphs = self._split_paragraphs(text)

        if len(paragraphs) > 1:
            return self._pack_paragraphs(
                paragraphs,
                max_chars,
            )

        sentences = self._split_sentences(text)

        if len(sentences) > 1:
            return self._pack_sentences(
                sentences,
                max_chars,
            )

        return self._split_by_characters(
            text,
            max_chars,
        )

    # ---------------------------------------------------------
    # Paragraph
    # ---------------------------------------------------------

    @staticmethod
    def _split_paragraphs(
        text: str,
    ) -> list[str]:

        paragraphs = re.split(
            r"\n\s*\n",
            text,
        )

        return [
            paragraph.strip()
            for paragraph in paragraphs
            if paragraph.strip()
        ]

    def _pack_paragraphs(
        self,
        paragraphs: list[str],
        max_chars: int,
    ) -> list[str]:

        chunks: list[str] = []
        current: list[str] = []
        current_length = 0

        for paragraph in paragraphs:

            if len(paragraph) > max_chars:

                if current:
                    chunks.append(
                        "\n\n".join(current)
                    )
                    current = []
                    current_length = 0

                chunks.extend(
                    self._adaptive_split(
                        paragraph,
                        max_chars,
                    )
                )

                continue

            separator_length = (
                2 if current else 0
            )

            if (
                current_length
                + separator_length
                + len(paragraph)
                <= max_chars
            ):
                current.append(paragraph)

                current_length += (
                    separator_length
                    + len(paragraph)
                )

            else:
                chunks.append(
                    "\n\n".join(current)
                )

                current = [paragraph]
                current_length = len(paragraph)

        if current:
            chunks.append(
                "\n\n".join(current)
            )

        return chunks

    # ---------------------------------------------------------
    # Sentence
    # ---------------------------------------------------------

    @staticmethod
    def _split_sentences(
        text: str,
    ) -> list[str]:

        sentences = re.split(
            r"(?<=[.!?;])\s+",
            text,
        )

        return [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

    def _pack_sentences(
        self,
        sentences: list[str],
        max_chars: int,
    ) -> list[str]:

        chunks: list[str] = []
        current: list[str] = []
        current_length = 0

        for sentence in sentences:

            if len(sentence) > max_chars:

                if current:
                    chunks.append(
                        " ".join(current)
                    )
                    current = []
                    current_length = 0

                chunks.extend(
                    self._split_by_characters(
                        sentence,
                        max_chars,
                    )
                )

                continue

            separator_length = (
                1 if current else 0
            )

            if (
                current_length
                + separator_length
                + len(sentence)
                <= max_chars
            ):
                current.append(sentence)

                current_length += (
                    separator_length
                    + len(sentence)
                )

            else:
                chunks.append(
                    " ".join(current)
                )

                current = [sentence]
                current_length = len(sentence)

        if current:
            chunks.append(
                " ".join(current)
            )

        return chunks

    # ---------------------------------------------------------
    # Character fallback
    # ---------------------------------------------------------

    def _split_by_characters(
        self,
        text: str,
        max_chars: int,
    ) -> list[str]:

        chunks: list[str] = []

        start = 0

        while start < len(text):

            end = min(
                start + max_chars,
                len(text),
            )

            chunk = text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= len(text):
                break

            start = max(
                end - self.overlap_chars,
                start + 1,
            )

        return chunks

    # ---------------------------------------------------------
    # Structural context
    # ---------------------------------------------------------

    @staticmethod
    def _build_context(
        path: list[StructureNode],
    ) -> str:

        parts: list[str] = []

        for node in path:

            if node.number:
                parts.append(
                    f"{node.number}. {node.title}"
                )
            elif node.title:
                parts.append(node.title)

        return "\n".join(parts)

    # ---------------------------------------------------------
    # DocumentChunk
    # ---------------------------------------------------------

    def _create_chunk(
        self,
        node: StructureNode,
        document_id: str,
        text: str,
        path: list[StructureNode],
    ) -> DocumentChunk:

        parent = (
            path[-2]
            if len(path) >= 2
            else None
        )

        structure_path = [
            item.number
            for item in path
            if item.number
        ]

        titles = [
            item.title
            for item in path
            if item.title
        ]

        return DocumentChunk(
            chunk_id=str(uuid4()),
            document_id=document_id,
            text=text,
            page_start=node.page_start or 0,
            page_end=node.page_end or 0,
            section_number=node.number,
            section_title=node.title,
            parent_number=(
                parent.number
                if parent
                else None
            ),
            parent_title=(
                parent.title
                if parent
                else None
            ),
            structure_path=structure_path,
            metadata={
                "titles": titles,
                "level": node.level,
            },
        )

    @staticmethod
    def _assign_chunk_indices(
        chunks: list[DocumentChunk],
    ) -> None:

        for index, chunk in enumerate(chunks):
            chunk.chunk_index = index

    @staticmethod
    def _normalize_text(
        text: str,
    ) -> str:

        text = text.strip()

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text