import math

import pytest

from app.eval.metrics import score_question


def test_target_counted_once_at_first_rank():
    # target 0 at ranks 3 and 4, target 1 at rank 7
    matches = [set(), set(), {0}, {0}, set(), set(), {1}]

    scores = score_question(matches, target_count=2)

    assert scores["hit@1"] == 0.0
    assert scores["hit@5"] == 1.0
    assert scores["recall@5"] == 0.5
    assert scores["recall@20"] == 1.0
    assert scores["mrr"] == pytest.approx(1 / 3)

    dcg = 1 / math.log2(4) + 1 / math.log2(8)
    ideal = 1 + 1 / math.log2(3)
    assert scores["ndcg@10"] == pytest.approx(dcg / ideal)


def test_no_hit_scores_zero():
    scores = score_question([set(), set()], target_count=1)

    assert all(value == 0.0 for value in scores.values())


def test_requires_targets():
    with pytest.raises(ValueError):
        score_question([], target_count=0)

