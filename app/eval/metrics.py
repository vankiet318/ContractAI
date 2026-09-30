"""
Retrieval metrics over one ranked result list.

A question has one or more targets (a labeled section or an evidence
phrase). `matches[r]` is the set of targets the chunk at rank r+1
satisfies. A target counts as found at the first rank that satisfies it,
so several chunks from the same section do not inflate recall or nDCG.
"""

import math

METRICS = [
    "hit@1",
    "hit@5",
    "recall@5",
    "recall@20",
    "mrr",
    "ndcg@10",
]


def first_found_ranks(
    matches: list[set[int]],
    target_count: int,
) -> list[int | None]:

    found: list[int | None] = [None] * target_count

    for rank, matched in enumerate(matches, start=1):
        for target in matched:
            if found[target] is None:
                found[target] = rank

    return found


def score_question(
    matches: list[set[int]],
    target_count: int,
) -> dict[str, float]:

    if target_count <= 0:
        raise ValueError("target_count must be > 0")

    found = first_found_ranks(matches, target_count)
    ranks = [rank for rank in found if rank is not None]

    def hit(k: int) -> float:
        return 1.0 if any(rank <= k for rank in ranks) else 0.0

    def recall(k: int) -> float:
        return sum(rank <= k for rank in ranks) / target_count

    def ndcg(k: int) -> float:
        # Gain 1 at the rank where each target is first found.
        dcg = sum(
            1.0 / math.log2(rank + 1)
            for rank in ranks
            if rank <= k
        )
        ideal = sum(
            1.0 / math.log2(rank + 1)
            for rank in range(1, min(k, target_count) + 1)
        )
        return dcg / ideal

    return {
        "hit@1": hit(1),
        "hit@5": hit(5),
        "recall@5": recall(5),
        "recall@20": recall(20),
        "mrr": 1.0 / min(ranks) if ranks else 0.0,
        "ndcg@10": ndcg(10),
    }
