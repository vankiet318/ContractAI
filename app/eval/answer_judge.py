"""
LLM-as-judge for one generated answer: splits the answer into factual
claims and checks each against the exact context the generator saw.
"""

import json
import re
from dataclasses import dataclass

from app.generation.base import LLM

JUDGE_INSTRUCTION = """
You audit answers produced by a question-answering system over a Vietnamese
contract. You receive the user QUESTION, the DOCUMENT CONTEXT the system was
given, the system ANSWER and, sometimes, a REFERENCE answer written by a human.

Do the following:

1. "refused": true if the answer says the document does not contain the
   requested information, or declines to answer (out of scope, greeting
   reply, etc.). An answer that corrects a wrong assumption in the question
   and then gives the right fact is NOT a refusal.

2. "claims": list every factual statement the answer makes about the
   contract (numbers, dates, parties, obligations, conditions, names).
   Skip pure politeness and statements that the document lacks information.
   For each claim give a verdict:
   - "supported": stated in the context, or follows from it by simple
     arithmetic or direct reading.
   - "unsupported": not found in the context (invented or from outside
     knowledge).
   - "contradicted": the context says something different (wrong number,
     wrong party, missing condition that changes the meaning).
   Judge ONLY against the context, never against your own knowledge.

3. "correctness": compare with the REFERENCE if one is given:
   "correct" (all key facts of the reference present and right),
   "partial" (some key facts missing, none wrong), "incorrect" (a key fact
   wrong or the question not answered). Use "n/a" when no reference is given.

4. "explanation": one or two sentences in Vietnamese.

Return only JSON:
{"refused": bool,
 "claims": [{"claim": str, "verdict": "supported|unsupported|contradicted"}],
 "correctness": "correct|partial|incorrect|n/a",
 "explanation": str}
"""

CORRECTNESS_LABELS = {"correct", "partial", "incorrect", "n/a"}


class JudgementParseError(Exception):
    pass


@dataclass
class Claim:
    text: str
    verdict: str


@dataclass
class Judgement:
    refused: bool
    claims: list[Claim]
    correctness: str
    explanation: str

    @property
    def unsupported_claims(self) -> list[str]:
        return [
            f"[{claim.verdict}] {claim.text}"
            for claim in self.claims
            if claim.verdict != "supported"
        ]


class AnswerJudge:

    def __init__(self, llm: LLM):
        self.llm = llm

    def judge(
        self,
        question: str,
        context: str,
        answer: str,
        reference: str | None,
    ) -> Judgement:

        prompt = (
            f"QUESTION\n========\n{question}\n\n"
            f"DOCUMENT CONTEXT\n================\n{context or '(empty)'}\n\n"
            f"ANSWER\n======\n{answer}\n\n"
            f"REFERENCE\n=========\n{reference or '(none)'}"
        )

        return parse_judgement(self.llm.generate(prompt))


def parse_judgement(reply: str) -> Judgement:

    body = re.sub(r"^```(?:json)?|```$", "", reply.strip()).strip()

    try:
        raw = json.loads(body)
        claims = [
            Claim(text=item["claim"], verdict=item["verdict"])
            for item in raw.get("claims", [])
        ]
        correctness = raw.get("correctness", "n/a")
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as error:
        raise JudgementParseError(f"Unreadable judge reply: {reply[:200]}") from error

    if correctness not in CORRECTNESS_LABELS:
        raise JudgementParseError(f"Unknown correctness label: {correctness}")

    return Judgement(
        refused=bool(raw.get("refused", False)),
        claims=claims,
        correctness=correctness,
        explanation=raw.get("explanation", ""),
    )
