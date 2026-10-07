import pytest

from app.eval.answer_judge import (
    Claim,
    Judgement,
    JudgementParseError,
    parse_judgement,
)
from app.eval.answer_scoring import (
    build_verdict,
    find_forbidden_phrases,
    find_missing_facts,
    normalize_answer,
)


def judgement(refused=False, verdicts=(), correctness="correct"):
    return Judgement(
        refused=refused,
        claims=[Claim(text=f"claim {i}", verdict=v) for i, v in enumerate(verdicts)],
        correctness=correctness,
        explanation="",
    )


def test_normalize_drops_markdown_and_leading_zeros():
    assert normalize_answer("Bảo hành **06 tháng**,  từ 08/09/2026") == "bảo hành 6 tháng, từ 8/9/2026"


def test_normalize_keeps_grouped_and_decimal_numbers():
    assert normalize_answer("200.000.000 VNĐ và 0,05%") == "200.000.000 vnđ và 0,05%"


def test_missing_fact_accepts_any_alternative():
    answer = "Lãi chậm trả là 0.05% mỗi ngày."

    assert find_missing_facts(answer, [["0,05%", "0.05%"]]) == []
    assert find_missing_facts(answer, ["8%"]) == ["8%"]


def test_forbidden_phrase_is_reported():
    assert find_forbidden_phrases("Bà Bình, Tổng Giám đốc", ["tổng giám đốc"]) == ["tổng giám đốc"]


def test_verdict_passes_grounded_correct_answer():
    question = {"must_contain": ["6 tháng"], "reference": "06 tháng"}

    verdict = build_verdict(question, "Bảo hành 06 tháng.", judgement(verdicts=["supported"]))

    assert verdict.is_passed
    assert verdict.faithfulness == 1.0


def test_verdict_fails_on_unsupported_claim():
    verdict = build_verdict({}, "...", judgement(verdicts=["supported", "unsupported"]))

    assert verdict.has_hallucination
    assert verdict.faithfulness == 0.5
    assert not verdict.is_passed


def test_verdict_fails_when_answering_instead_of_refusing():
    verdict = build_verdict({"expect_refusal": True}, "Phí bảo trì là 10 triệu.", judgement())

    assert not verdict.is_refusal_correct
    assert not verdict.is_passed


def test_expected_refusal_skips_required_facts():
    question = {"expect_refusal": True, "must_contain": ["x"]}

    verdict = build_verdict(question, "Tài liệu không đề cập.", judgement(refused=True, correctness="n/a"))

    assert verdict.is_passed


def test_correctness_ignored_without_reference():
    verdict = build_verdict({}, "...", judgement(correctness="incorrect"))

    assert verdict.correctness == "n/a"


def test_parse_judgement_strips_code_fence():
    reply = '```json\n{"refused": false, "claims": [{"claim": "a", "verdict": "supported"}], "correctness": "partial", "explanation": "e"}\n```'

    parsed = parse_judgement(reply)

    assert parsed.correctness == "partial"
    assert parsed.claims == [Claim(text="a", verdict="supported")]


@pytest.mark.parametrize("reply", ["not json", '{"correctness": "maybe"}'])
def test_parse_judgement_rejects_bad_reply(reply):
    with pytest.raises(JudgementParseError):
        parse_judgement(reply)
