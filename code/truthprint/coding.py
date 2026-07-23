"""Systematic [n, k] linear block code over GF(2) with erasure decoding.

The authenticated payload is spread across carriers via this code so that a
meaning-preserving transformation that destroys some carriers (erasures) still
allows exact payload recovery -- provided the surviving carriers exceed the
capacity floor. Recovery succeeds iff the retained rows have rank k, which
yields the recovery cliff at erasure rate ~ (1 - rate) (Proposition 2).
"""
from __future__ import annotations

import random

__all__ = ["GF2Code"]


class GF2Code:
    """Systematic code G = [I_k | P], with P pseudo-random from a fixed seed."""

    def __init__(self, k: int, n: int, seed: int = 0xC0FFEE):
        if n < k:
            raise ValueError("n must be >= k")
        self.k, self.n, self.seed = k, n, seed
        rng = random.Random(seed)
        self.P = [[rng.randint(0, 1) for _ in range(n - k)] for _ in range(k)]

    @property
    def rate(self) -> float:
        return self.k / self.n

    def encode(self, payload: list[int]) -> list[int]:
        if len(payload) != self.k:
            raise ValueError(f"payload must have length k={self.k}")
        parity = []
        for j in range(self.n - self.k):
            acc = 0
            for i in range(self.k):
                acc ^= payload[i] & self.P[i][j]
            parity.append(acc)
        return list(payload) + parity  # systematic: message bits appear first

    def _column(self, j: int) -> list[int]:
        """Coefficients (length k) of message bits producing code position j."""
        if j < self.k:
            e = [0] * self.k
            e[j] = 1
            return e
        return [self.P[i][j - self.k] for i in range(self.k)]

    def decode_erasure(self, received: list[int | None]) -> list[int] | None:
        """Recover the payload from non-erased positions (``None`` = erasure).

        Solves the surviving linear system over GF(2) by Gaussian elimination.
        Returns the k-bit payload, or ``None`` if underdetermined.
        """
        if len(received) != self.n:
            raise ValueError(f"received must have length n={self.n}")
        rows, rhs = [], []
        for j, val in enumerate(received):
            if val is None:
                continue
            rows.append(self._column(j)[:])
            rhs.append(val & 1)

        k = self.k
        pivot_row_of_col = [-1] * k
        r = 0
        for c in range(k):
            piv = -1
            for rr in range(r, len(rows)):
                if rows[rr][c] == 1:
                    piv = rr
                    break
            if piv == -1:
                continue
            rows[r], rows[piv] = rows[piv], rows[r]
            rhs[r], rhs[piv] = rhs[piv], rhs[r]
            for rr in range(len(rows)):
                if rr != r and rows[rr][c] == 1:
                    rows[rr] = [a ^ b for a, b in zip(rows[rr], rows[r])]
                    rhs[rr] ^= rhs[r]
            pivot_row_of_col[c] = r
            r += 1
        if r < k:
            return None  # not enough independent surviving equations
        solution = [0] * k
        for c in range(k):
            pr = pivot_row_of_col[c]
            if pr != -1:
                solution[c] = rhs[pr]
        return solution
