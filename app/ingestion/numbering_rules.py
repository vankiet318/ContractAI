import re
from dataclasses import dataclass
from enum import Enum


class NumberingScope(Enum):
    """Where a numbering pattern is matched against."""

    FIRST_TOKEN = "first_token"
    FULL_TEXT = "full_text"


@dataclass(frozen=True)
class NumberingRule:
    pattern: re.Pattern
    scope: NumberingScope = NumberingScope.FIRST_TOKEN


# Generic, symbol-based numbering conventions.
# These are language-agnostic and safe as a default
# for any document type.
DEFAULT_NUMBERING_RULES: list[NumberingRule] = [
    # 1 / 1.
    NumberingRule(re.compile(r"^(\d+)[.)]?$")),

    # 1.1 / 1.1.
    NumberingRule(re.compile(r"^(\d+(?:\.\d+)+)\.?$")),

    # A. / a.
    NumberingRule(re.compile(r"^([A-Za-z])[.)]$")),

    # (a) / (1)
    NumberingRule(re.compile(r"^\(([a-zA-Z0-9]+)\)$")),

    # I. (Roman numerals)
    NumberingRule(
        re.compile(r"^([IVXLCDM]+)\.$", re.IGNORECASE),
    ),

    # 1.2. Something
    # (numbering embedded in the first sentence,
    # rather than isolated as its own token)
    NumberingRule(
        re.compile(r"^(\d+(?:\.\d+)+)\."),
        scope=NumberingScope.FULL_TEXT,
    ),
]


def keyword_numbering_rules(
    keywords: list[str],
) -> list[NumberingRule]:
    """
    Build numbering rules for "<keyword> <number>" style
    headings, e.g. "Article 1", "Điều 1", "Chương II".

    Callers supply the keyword vocabulary for their own
    document domain/language; this module does not
    hardcode any of them.
    """

    escaped_keywords = "|".join(
        re.escape(keyword) for keyword in keywords
    )

    pattern = re.compile(
        rf"^(?:{escaped_keywords})\s+(\d+|[IVXLCDM]+)",
        re.IGNORECASE,
    )

    return [
        NumberingRule(
            pattern,
            scope=NumberingScope.FULL_TEXT,
        )
    ]
