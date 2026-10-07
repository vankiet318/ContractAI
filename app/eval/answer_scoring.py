"""
Deterministic checks on one generated answer, plus the per-question
verdict that combines them with the LLM judge's findings.

A labeled question may carry:

    "must_contain":     facts the answer has to state. Each item is a
                        phrase or a list of acceptable alternatives
                        (["0,05%", "0.05%"]).
    "must_not_contain": phrases whose presence means a wrong answer
                        (e.g. the false premise repeated as fact).
    "expect_refusal":   true when the contract does not answer the
                        question, so the system must say so.
"""

import re
from dataclasses import dataclass, field

from app.eval.answer_judge import Judgement

FactSpec = str | list[str]


def normalize_answer(text: str) -> str:
    text = re.sub(r"[*_`#]", "", text)
    # "06 tháng" and "6 tháng" state the same fact.
    text = re.sub(r"(?<![\d.,])0+(\d)", r"\1", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def find_missing_facts(answer: str, must_contain: list[FactSpec]) -> list[str]:

    normalized = normalize_answer(answer)

    return [
        " | ".join(alternatives)
        for alternatives in (as_alternatives(fact) for fact in must_contain)
        if not any(normalize_answer(option) in normalized for option in alternatives)
    ]


def find_forbidden_phrases(answer: str, must_not_contain: list[str]) -> list[str]:

    normalized = normalize_answer(answer)

    return [
        phrase
        for phrase in must_not_contain
        if normalize_answer(phrase) in normalized
    ]


def as_alternatives(fact: FactSpec) -> list[str]:
    return [fact] if isinstance(fact, str) else fact


@dataclass
class AnswerVerdict:
    refused: bool
    expect_refusal: bool
    missing_facts: list[str] = field(default_factory=list)
    forbidden_found: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    claim_count: int = 0
    correctness: str = "n/a"

    @property
    def is_refusal_correct(self) -> bool:
        return self.refused == self.expect_refusal

    @property
    def has_hallucination(self) -> bool:
        return bool(self.unsupported_claims)

    @property
    def faithfulness(self) -> float | None:
        if self.claim_count == 0:
            return None
        return 1 - len(self.unsupported_claims) / self.claim_count

    @property
    def has_required_facts(self) -> bool:
        return not self.missing_facts and not self.forbidden_found

    @property
    def is_passed(self) -> bool:
        return (
            self.is_refusal_correct
            and self.has_required_facts
            and not self.has_hallucination
            and self.correctness in ("correct", "n/a")
        )


def build_verdict(
    question: dict,
    answer: str,
    judgement: Judgement,
) -> AnswerVerdict:

    expect_refusal = bool(question.get("expect_refusal", False))

    return AnswerVerdict(
        refused=judgement.refused,
        expect_refusal=expect_refusal,
        # Facts are only required of answers that should state them.
        missing_facts=[] if expect_refusal else find_missing_facts(
            answer, question.get("must_contain", []),
        ),
        forbidden_found=find_forbidden_phrases(
            answer, question.get("must_not_contain", []),
        ),
        unsupported_claims=judgement.unsupported_claims,
        claim_count=len(judgement.claims),
        correctness=judgement.correctness if question.get("reference") else "n/a",
    )
