"""
Offline answer evaluation on one contract PDF: does the full pipeline
(retrieval -> relevance gate -> Gemini) answer correctly without inventing
facts?

The PDF is indexed into an in-memory Qdrant (same as `retrieval`), each
question runs through the production QuerySessionUseCase, and every answer
is scored three ways:

    facts         required phrases present ("must_contain"), wrong ones
                  absent ("must_not_contain") - deterministic
    faithfulness  share of the answer's claims supported by the context the
                  generator saw, as judged by a second LLM call
    refusal       says "not in the document" exactly when it should
                  ("expect_refusal")

Run inside the backend container, or locally with the venv:

    python -m app.eval.answers --pdf data/raw/Hop_Dong_Dich_Vu_Mau.pdf \\
        --questions data/eval/questions.json --out data/eval/answers_report.json

Each question costs two Gemini calls (answer + judge), one when the
relevance gate blocks it. Extra question fields: see app/eval/answer_scoring.py.
A question may also carry "history": [{"question": ..., "answer": ...}] to
test follow-ups in a conversation.
"""

import argparse
import json
import statistics
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, TypeVar
from uuid import uuid4

from app import dependencies as deps
from app.documents.models import Document, DocumentStatus
from app.eval.answer_judge import JUDGE_INSTRUCTION, AnswerJudge, Judgement
from app.eval.answer_scoring import AnswerVerdict, build_verdict
from app.eval.retrieval import EVAL_SESSION_ID, Corpus, load_questions
from app.generation.base import LLM
from app.generation.context_builder import ContextBuilder, ContextItem
from app.generation.gemini_client import GeminiClient
from app.generation.prompt_builder import PromptBuilder
from app.messages.models import ChatMessage
from app.messages.service import ChatMessageService
from app.query.use_case import (
    AnswerDelta,
    AnswerStarted,
    QuerySessionUseCase,
)
from app.retrieval.dense_retriever import DenseRetriever
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.sparse_retriever import SparseRetriever

GATE_EXPLANATION = "Bị chặn bởi ngưỡng liên quan, không gọi LLM."

Result = TypeVar("Result")


# -------------------------------------------------------------
# Pipeline wiring (in-memory stand-ins for the database)
# -------------------------------------------------------------


class InMemoryMessageRepository:

    def __init__(self, messages: list[ChatMessage]):
        self.messages = list(messages)

    def create(self, message: ChatMessage) -> None:
        self.messages.append(message)

    def list_by_session(self, session_id: str) -> list[ChatMessage]:
        return [m for m in self.messages if m.session_id == session_id]


class ReadyDocumentService:

    def list_by_session(self, session_id: str) -> list[Document]:
        return [
            Document(
                document_id="eval",
                session_id=session_id,
                filename="eval.pdf",
                file_path="",
                status=DocumentStatus.READY,
                created_at=datetime.now(),
            )
        ]


class RecordingContextBuilder(ContextBuilder):
    """Keeps the exact context handed to the LLM so the judge sees it too."""

    def __init__(self):
        self.last_context: str | None = None

    def format(self, items: list[ContextItem]) -> str:
        self.last_context = super().format(items)
        return self.last_context


@dataclass
class GeneratedAnswer:
    answer: str
    context: str | None
    cited_sections: list[str]

    @property
    def is_gated(self) -> bool:
        return self.context is None


class AnswerPipeline:

    def __init__(self, corpus: Corpus, llm: LLM, top_k: int):
        self.llm = llm
        self.top_k = top_k
        self.hybrid_retriever = HybridRetriever(
            embedding_model=deps.embedding_model,
            dense_retriever=DenseRetriever(
                embedding_model=deps.embedding_model,
                vector_store=corpus.store,
            ),
            sparse_retriever=SparseRetriever(
                embedding_model=deps.embedding_model,
                vector_store=corpus.store,
            ),
            rrf=deps.rrf,
            min_dense_score=deps.retrieval_config.min_dense_score,
            topic_gate=deps.topic_gate,
        )

    def answer(self, question: str, history: list[dict]) -> GeneratedAnswer:

        context_builder = RecordingContextBuilder()
        use_case = self._build_use_case(context_builder, history)

        answer_parts, cited_sections = [], []

        for event in use_case.stream(EVAL_SESSION_ID, question, self.top_k):
            if isinstance(event, AnswerStarted):
                cited_sections = [c.section_number or "-" for c in event.citations]
            elif isinstance(event, AnswerDelta):
                answer_parts.append(event.text)

        return GeneratedAnswer(
            answer="".join(answer_parts),
            context=context_builder.last_context,
            cited_sections=cited_sections,
        )

    def _build_use_case(
        self,
        context_builder: ContextBuilder,
        history: list[dict],
    ) -> QuerySessionUseCase:

        return QuerySessionUseCase(
            document_service=ReadyDocumentService(),
            message_service=ChatMessageService(
                repository=InMemoryMessageRepository(to_messages(history)),
            ),
            hybrid_retriever=self.hybrid_retriever,
            reranking_service=deps.reranking_service,
            context_builder=context_builder,
            prompt_builder=deps.prompt_builder,
            llm=self.llm,
            citation_builder=deps.citation_builder,
            candidate_limit=deps.retrieval_config.candidate_limit,
            limit=deps.retrieval_config.limit,
            min_relevance_score=deps.reranking_config.min_score,
        )


def to_messages(history: list[dict]) -> list[ChatMessage]:
    return [
        ChatMessage(
            message_id=str(uuid4()),
            session_id=EVAL_SESSION_ID,
            question=turn["question"],
            answer=turn["answer"],
            citations=[],
            created_at=datetime(2000, 1, 1, 0, 0, index),
        )
        for index, turn in enumerate(history)
    ]


# -------------------------------------------------------------
# Evaluation
# -------------------------------------------------------------


@dataclass
class EvaluatedQuestion:
    id: str
    type: str
    question: str
    answer: str
    cited_sections: list[str]
    verdict: AnswerVerdict
    explanation: str


class AnswerEvaluator:

    def __init__(self, pipeline: AnswerPipeline, judge: AnswerJudge, delay: float):
        self.pipeline = pipeline
        self.judge = judge
        self.delay = delay

    def evaluate(self, question: dict) -> EvaluatedQuestion:

        generated = with_retry(lambda: self.pipeline.answer(
            question["question"], question.get("history", []),
        ))
        judgement = self._judge(question, generated)

        return EvaluatedQuestion(
            id=question.get("id", "?"),
            type=question.get("type", "untyped"),
            question=question["question"],
            answer=generated.answer,
            cited_sections=generated.cited_sections,
            verdict=build_verdict(question, generated.answer, judgement),
            explanation=judgement.explanation,
        )

    def _judge(self, question: dict, generated: GeneratedAnswer) -> Judgement:

        reference = question.get("reference")

        # The gate's fixed reply makes no claims; no need to ask the judge.
        if generated.is_gated:
            return Judgement(
                refused=True,
                claims=[],
                correctness="incorrect" if reference else "n/a",
                explanation=GATE_EXPLANATION,
            )

        time.sleep(self.delay)

        return with_retry(lambda: self.judge.judge(
            question=question["question"],
            context=generated.context,
            answer=generated.answer,
            reference=reference,
        ))


class GeminiUnavailableError(Exception):
    """Gemini cannot serve more requests now; the run stops and can resume later."""


def with_retry(call: Callable[[], Result], attempts: int = 5) -> Result:
    """Retries Gemini per-minute limits and overload errors with a growing wait."""

    for attempt in range(1, attempts + 1):
        try:
            return call()
        except Exception as error:
            # Waiting cannot help once the daily quota is gone.
            if "PerDay" in str(error):
                raise GeminiUnavailableError(f"daily quota exhausted: {str(error)[:200]}") from error
            if not is_transient(error):
                raise
            if attempt == attempts:
                raise GeminiUnavailableError(f"still failing after {attempts} attempts: {str(error)[:200]}") from error
            wait = 20 * attempt
            print(f"    transient error ({error.__class__.__name__}), retry in {wait}s")
            time.sleep(wait)

    raise AssertionError("unreachable")


def is_transient(error: Exception) -> bool:
    message = str(error)
    markers = ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "Unreadable judge reply")
    return any(marker in message for marker in markers)


# -------------------------------------------------------------
# Report
# -------------------------------------------------------------

SUMMARY_COLUMNS = ["n", "pass", "refusal", "facts", "no-halluc", "faithful", "correct"]


def summarize(rows: list[EvaluatedQuestion]) -> list[str]:

    verdicts = [row.verdict for row in rows]
    faithfulness = [v.faithfulness for v in verdicts if v.faithfulness is not None]
    graded = [v for v in verdicts if v.correctness != "n/a"]

    return [
        f"{len(rows)}",
        rate(v.is_passed for v in verdicts),
        rate(v.is_refusal_correct for v in verdicts),
        rate(v.has_required_facts for v in verdicts),
        rate(not v.has_hallucination for v in verdicts),
        f"{statistics.fmean(faithfulness):.2f}" if faithfulness else "-",
        rate(v.correctness == "correct" for v in graded) if graded else "-",
    ]


def rate(flags) -> str:
    values = list(flags)
    return f"{sum(values)}/{len(values)}"


def print_summary(rows: list[EvaluatedQuestion]) -> None:

    print("\n" + f"{'type':<16}" + "".join(f"{c:>11}" for c in SUMMARY_COLUMNS))

    groups = defaultdict(list)
    for row in rows:
        groups[row.type].append(row)

    for question_type, group in sorted(groups.items()):
        print(f"{question_type:<16}" + "".join(f"{c:>11}" for c in summarize(group)))

    print(f"{'ALL':<16}" + "".join(f"{c:>11}" for c in summarize(rows)))


def print_failures(rows: list[EvaluatedQuestion]) -> None:

    failures = [row for row in rows if not row.verdict.is_passed]
    print(f"\nFailed: {len(failures)}/{len(rows)}")

    for row in failures:
        verdict = row.verdict
        print(f"\n[{row.id} · {row.type}] {row.question}")
        print(f"  answer : {one_line(row.answer, 300)}")
        print(f"  cited  : {', '.join(row.cited_sections) or '(none)'}")
        if not verdict.is_refusal_correct:
            print(f"  refusal: expected={verdict.expect_refusal} got={verdict.refused}")
        for fact in verdict.missing_facts:
            print(f"  missing: {fact}")
        for phrase in verdict.forbidden_found:
            print(f"  wrong  : contains '{phrase}'")
        for claim in verdict.unsupported_claims:
            print(f"  claim  : {claim}")
        print(f"  judge  : {verdict.correctness} - {row.explanation}")


def one_line(text: str, limit: int) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[:limit] + "…"


@dataclass
class ReportModels:
    answer_model: str
    judge_model: str


def write_report(rows: list[EvaluatedQuestion], models: ReportModels, path: str) -> None:

    report = {
        **asdict(models),
        "results": [
            {**asdict(row), "passed": row.verdict.is_passed, "faithfulness": row.verdict.faithfulness}
            for row in rows
        ],
    }

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def load_report(path: str, models: ReportModels) -> list[EvaluatedQuestion]:

    report = json.loads(Path(path).read_text(encoding="utf-8"))

    if ReportModels(report["answer_model"], report["judge_model"]) != models:
        raise SystemExit(
            f"{path} was produced by {report['answer_model']} / {report['judge_model']}; "
            "use another --out to evaluate different models"
        )

    return [to_evaluated_question(entry) for entry in report["results"]]


def to_evaluated_question(entry: dict) -> EvaluatedQuestion:

    fields = {name: entry[name] for name in EvaluatedQuestion.__dataclass_fields__}
    fields["verdict"] = AnswerVerdict(**entry["verdict"])

    return EvaluatedQuestion(**fields)


# -------------------------------------------------------------
# Entry point
# -------------------------------------------------------------


def build_evaluator(args: argparse.Namespace, models: ReportModels) -> AnswerEvaluator:

    answer_llm = (
        deps.gemini_client
        if models.answer_model == deps.gemini_config.model_name
        else GeminiClient(
            model_name=models.answer_model,
            system_instruction=PromptBuilder.SYSTEM_INSTRUCTION,
            api_key=deps.gemini_config.api_key,
            temperature=deps.gemini_config.temperature,
            max_output_tokens=deps.gemini_config.max_output_tokens,
        )
    )

    judge_llm = GeminiClient(
        model_name=models.judge_model,
        system_instruction=JUDGE_INSTRUCTION,
        api_key=deps.gemini_config.api_key,
        temperature=0.0,
        max_output_tokens=4096,
    )

    return AnswerEvaluator(
        pipeline=AnswerPipeline(Corpus(args.pdf), answer_llm, args.top_k),
        judge=AnswerJudge(judge_llm),
        delay=args.delay,
    )


def select_questions(questions: list[dict], only: str | None) -> list[dict]:

    if not only:
        return questions

    wanted = set(only.split(","))

    return [q for q in questions if q.get("id") in wanted or q.get("type") in wanted]


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--questions", required=True)
    parser.add_argument("--out", help="per-question results (JSON), saved after every question")
    parser.add_argument("--resume", action="store_true", help="skip questions already in --out")
    parser.add_argument("--only", help="comma-separated question ids or types")
    parser.add_argument("--top-k", type=int, default=5, help="chunks given to the LLM (API default: 5)")
    parser.add_argument("--answer-model", help="model that answers (default: GEMINI_MODEL_NAME, as in production)")
    parser.add_argument("--judge-model", help="judge model (default: GEMINI_MODEL_NAME); a different model also spreads free-tier quota")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between Gemini calls")

    args = parser.parse_args()

    if args.resume and not args.out:
        parser.error("--resume needs --out")

    return args


def main() -> None:

    args = parse_args()
    models = ReportModels(
        answer_model=args.answer_model or deps.gemini_config.model_name,
        judge_model=args.judge_model or deps.gemini_config.model_name,
    )

    rows = load_report(args.out, models) if args.resume and Path(args.out).exists() else []
    done = {row.id for row in rows}
    pending = [q for q in select_questions(load_questions(args.questions), args.only) if q.get("id") not in done]

    print(f"answer: {models.answer_model}  judge: {models.judge_model}  done: {len(done)}  pending: {len(pending)}")

    evaluate_all(build_evaluator(args, models), pending, rows, ReportTarget(models, args.out), args.delay)

    print_summary(rows)
    print_failures(rows)


@dataclass
class ReportTarget:
    models: ReportModels
    path: str | None


def evaluate_all(
    evaluator: AnswerEvaluator,
    questions: list[dict],
    rows: list[EvaluatedQuestion],
    target: ReportTarget,
    delay: float,
) -> None:
    """Appends to `rows` and saves after every question, so a quota stop loses nothing."""

    for number, question in enumerate(questions, start=1):
        try:
            row = evaluator.evaluate(question)
        except GeminiUnavailableError as error:
            print(f"\nStopping - {error}\nProgress is saved; re-run with --resume later.")
            return

        rows.append(row)
        print(f"[{number}/{len(questions)}] {'PASS' if row.verdict.is_passed else 'FAIL'}  {row.id}  {row.question}")

        if target.path:
            write_report(rows, target.models, target.path)

        time.sleep(delay)


if __name__ == "__main__":
    main()
