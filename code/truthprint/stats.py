"""Small, dependency-free statistics helpers for the evaluation harness.

The paper's Stage-1 numbers are point estimates; ACL reviewers rightly ask for
confidence intervals. These helpers compute nonparametric bootstrap intervals
and Wilson score intervals for proportions using only the standard library, so
every reported rate can carry an interval reproducibly from a fixed seed.
"""
from __future__ import annotations

import math
import random

__all__ = ["bootstrap_ci", "wilson_ci", "mean"]


def mean(values) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def bootstrap_ci(values, num_resamples: int = 2000, ci: float = 0.95,
                 seed: int = 0xB007):
    """Nonparametric bootstrap CI for the mean of ``values``.

    Returns ``(point_estimate, lo, hi)``. Deterministic given ``seed``.
    """
    values = list(values)
    n = len(values)
    if n == 0:
        return 0.0, 0.0, 0.0
    point = mean(values)
    rng = random.Random(seed)
    means = []
    for _ in range(num_resamples):
        resample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(resample) / n)
    means.sort()
    lo_idx = int((1.0 - ci) / 2.0 * num_resamples)
    hi_idx = min(num_resamples - 1, int((1.0 + ci) / 2.0 * num_resamples))
    return point, means[lo_idx], means[hi_idx]


def wilson_ci(successes: int, n: int, z: float = 1.959963985):
    """Wilson score interval for a binomial proportion (95% by default).

    More reliable than the normal approximation for rates near 0 or 1, which is
    exactly where watermark tamper-detection / false-attribution rates sit.
    Returns ``(point, lo, hi)``.
    """
    if n == 0:
        return 0.0, 0.0, 0.0
    p = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))) / denom
    return p, max(0.0, center - half), min(1.0, center + half)
