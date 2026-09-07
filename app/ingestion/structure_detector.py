from .models import (
    BlockFeatures,
    DocumentSchema,
    StructureNode,
)


class StructureDetector:
    """
    Convert block-level features into structural nodes.

    Responsibilities:
    - Identify heading blocks
    - Create StructureNode objects
    - Preserve page information
    - Preserve numbering
    - Preserve body text

    This class does NOT build the hierarchy.
    """

    def detect(
        self,
        features: list[BlockFeatures],
        schema: DocumentSchema,
    ) -> list[StructureNode]:

        if not features:
            return []

        nodes: list[StructureNode] = []

        current_node: StructureNode | None = None

        for feature in features:

            if feature.looks_like_heading:

                node = self._create_heading_node(
                    feature=feature,
                    schema=schema,
                )

                nodes.append(node)
                current_node = node

                continue

            # Body text
            if current_node is not None:
                self._append_body_text(
                    node=current_node,
                    feature=feature,
                )

        return nodes

    # ---------------------------------------------------------
    # Heading
    # ---------------------------------------------------------

    def _create_heading_node(
        self,
        feature: BlockFeatures,
        schema: DocumentSchema,
    ) -> StructureNode:

        level = self._resolve_level(
            feature=feature,
            schema=schema,
        )

        node_type = self._resolve_node_type(
            level=level,
        )

        title = self._clean_title(
            feature.text
        )

        return StructureNode(
            node_type=node_type,
            title=title,
            text="",
            number=feature.numbering,
            level=level,
            page_start=feature.page_number,
            page_end=feature.page_number,
            metadata={
                "font_size": feature.font_size,
                "is_bold": feature.is_bold,
                "is_italic": feature.is_italic,
                "indent": feature.indent,
            },
        )

    # ---------------------------------------------------------
    # Level
    # ---------------------------------------------------------

    def _resolve_level(
        self,
        feature: BlockFeatures,
        schema: DocumentSchema,
    ) -> int:

        if feature.numbering_level is not None:
            return feature.numbering_level

        return self._infer_level_from_style(
            feature=feature,
            schema=schema,
        )

    def _infer_level_from_style(
        self,
        feature: BlockFeatures,
        schema: DocumentSchema,
    ) -> int:

        if not schema.heading_styles:
            return 1

        best_level = 1
        best_score = float("inf")

        for level, style in schema.heading_styles.items():

            score = 0.0

            score += abs(
                feature.font_size
                - style.font_size
            )

            score += abs(
                feature.indent
                - style.indent
            ) * 0.5

            if feature.is_bold != style.is_bold:
                score += 2.0

            if feature.is_italic != style.is_italic:
                score += 1.0

            if score < best_score:
                best_score = score
                best_level = level

        return best_level

    # ---------------------------------------------------------
    # Node type
    # ---------------------------------------------------------

    @staticmethod
    def _resolve_node_type(
        level: int,
    ) -> str:

        return f"level_{level}"

    # ---------------------------------------------------------
    # Body
    # ---------------------------------------------------------

    def _append_body_text(
        self,
        node: StructureNode,
        feature: BlockFeatures,
    ) -> None:

        text = feature.text.strip()

        if not text:
            return

        if node.text:
            node.text += "\n" + text
        else:
            node.text = text

        node.page_end = feature.page_number

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _clean_title(
        text: str,
    ) -> str:

        return text.strip()