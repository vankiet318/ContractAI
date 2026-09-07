from collections import defaultdict
from statistics import median

from .models import (
    BlockFeatures,
    DocumentSchema,
    HeadingStyle,
)


class SchemaInference:
    """
    Infer document structure schema from extracted block features.

    The goal is to learn structural patterns from the document itself
    instead of assuming a fixed contract format.

    Responsibilities:
    - Infer numbering patterns
    - Infer hierarchy depth
    - Infer heading styles
    - Estimate heading font threshold

    This class does NOT build the actual document tree.
    """

    def infer(
        self,
        features: list[BlockFeatures],
    ) -> DocumentSchema:

        if not features:
            return DocumentSchema()

        heading_features = [
            feature
            for feature in features
            if feature.looks_like_heading
        ]

        numbering_patterns = self._infer_numbering_patterns(
            heading_features
        )

        max_depth = self._infer_max_depth(
            heading_features
        )

        heading_styles = self._infer_heading_styles(
            heading_features
        )

        heading_font_threshold = (
            self._infer_heading_font_threshold(
                heading_features
            )
        )

        return DocumentSchema(
            numbering_patterns=numbering_patterns,
            max_depth=max_depth,
            heading_font_threshold=heading_font_threshold,
            heading_styles=heading_styles,
        )

    # ---------------------------------------------------------
    # Numbering
    # ---------------------------------------------------------

    def _infer_numbering_patterns(
        self,
        features: list[BlockFeatures],
    ) -> dict[int, str]:

        grouped: defaultdict[int, list[str]] = defaultdict(list)

        for feature in features:
            if (
                feature.numbering_level is None
                or feature.numbering is None
            ):
                continue

            grouped[
                feature.numbering_level
            ].append(feature.numbering)

        patterns: dict[int, str] = {}

        for level, values in grouped.items():
            patterns[level] = self._infer_pattern(values)

        return patterns

    def _infer_pattern(
        self,
        values: list[str],
    ) -> str:

        if not values:
            return "unknown"

        # Numeric / hierarchical numeric
        if all(
            value.replace(".", "").isdigit()
            for value in values
        ):
            if any("." in value for value in values):
                return "numeric_hierarchical"

            return "numeric"

        # Roman numerals
        if all(
            self._is_roman(value)
            for value in values
        ):
            return "roman"

        # Alphabetic
        if all(
            len(value) == 1
            and value.isalpha()
            for value in values
        ):
            return "alphabetic"

        return "mixed"

    # ---------------------------------------------------------
    # Depth
    # ---------------------------------------------------------

    def _infer_max_depth(
        self,
        features: list[BlockFeatures],
    ) -> int:

        levels = [
            feature.numbering_level
            for feature in features
            if feature.numbering_level is not None
        ]

        if not levels:
            return 0

        return max(levels)

    # ---------------------------------------------------------
    # Heading style
    # ---------------------------------------------------------

    def _infer_heading_styles(
        self,
        features: list[BlockFeatures],
    ) -> dict[int, HeadingStyle]:

        grouped: defaultdict[
            int,
            list[BlockFeatures]
        ] = defaultdict(list)

        for feature in features:

            if feature.numbering_level is None:
                continue

            grouped[
                feature.numbering_level
            ].append(feature)

        styles: dict[int, HeadingStyle] = {}

        for level, items in grouped.items():

            font_sizes = [
                item.font_size
                for item in items
                if item.font_size > 0
            ]

            indents = [
                item.indent
                for item in items
            ]

            gaps_before = [
                item.vertical_gap_before
                for item in items
            ]

            gaps_after = [
                item.vertical_gap_after
                for item in items
            ]

            bold_count = sum(
                item.is_bold
                for item in items
            )

            italic_count = sum(
                item.is_italic
                for item in items
            )

            examples = [
                item.text
                for item in items[:5]
            ]

            styles[level] = HeadingStyle(
                level=level,

                font_size=(
                    float(median(font_sizes))
                    if font_sizes
                    else 0.0
                ),

                is_bold=(
                    bold_count >= len(items) / 2
                ),

                is_italic=(
                    italic_count >= len(items) / 2
                ),

                indent=(
                    float(median(indents))
                    if indents
                    else 0.0
                ),

                avg_gap_before=(
                    float(median(gaps_before))
                    if gaps_before
                    else 0.0
                ),

                avg_gap_after=(
                    float(median(gaps_after))
                    if gaps_after
                    else 0.0
                ),

                examples=examples,
            )

        return styles

    # ---------------------------------------------------------
    # Font threshold
    # ---------------------------------------------------------

    def _infer_heading_font_threshold(
        self,
        features: list[BlockFeatures],
    ) -> float:

        font_sizes = [
            feature.font_size
            for feature in features
            if (
                feature.looks_like_heading
                and feature.font_size > 0
            )
        ]

        if not font_sizes:
            return 0.0

        return float(min(font_sizes))

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _is_roman(
        value: str,
    ) -> bool:

        if not value:
            return False

        roman_chars = set(
            "IVXLCDMivxlcdm"
        )

        return all(
            char in roman_chars
            for char in value
        )