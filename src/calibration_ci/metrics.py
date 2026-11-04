"""Dependency-free calibration metrics (standard library only, so the Action installs in seconds)."""

from __future__ import annotations

import math
from typing import Sequence


def accuracy(y: Sequence[int], p: Sequence[float]) -> float:
    return sum(y) / len(y)


def brier(y: Sequence[int], p: Sequence[float]) -> float:
    return sum((pi - yi) ** 2 for yi, pi in zip(y, p)) / len(y)


def ece(y: Sequence[int], p: Sequence[float], n_bins: int = 10) -> float:
    """Expected calibration error, equal-width bins."""
    sums = [[0.0, 0.0, 0] for _ in range(n_bins)]
    for yi, pi in zip(y, p):
        b = min(int(pi * n_bins), n_bins - 1)
        sums[b][0] += pi
        sums[b][1] += yi
        sums[b][2] += 1
    n = len(y)
    return sum(abs(s[0] - s[1]) for s in sums if s[2]) / n


def auroc2(y: Sequence[int], p: Sequence[float]) -> float:
    """Type-2 AUROC: does confidence rank correct answers above wrong ones? (ties = 0.5)"""
    pairs = sorted(zip(p, y))
    n1 = sum(y)
    n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return math.nan
    rank_sum, i = 0.0, 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg_rank = (i + j) / 2 + 1
        rank_sum += avg_rank * sum(pairs[k][1] for k in range(i, j + 1))
        i = j + 1
    return (rank_sum - n1 * (n1 + 1) / 2) / (n1 * n0)


def overconfidence(y: Sequence[int], p: Sequence[float]) -> float:
    return sum(p) / len(p) - sum(y) / len(y)


METRICS = {
    "accuracy": (accuracy, "higher"),
    "ece": (ece, "lower"),
    "brier": (brier, "lower"),
    "auroc2": (auroc2, "higher"),
    "overconfidence": (overconfidence, "info"),
}
