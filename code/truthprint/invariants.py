"""Invariant layer: canonical digest of the locked semantic contract.

The invariant set ``I`` is the truth-conditional content that a watermark must
never alter (entities, predicates, roles, polarity, quantities, time,
attribution, ...). We serialize it canonically (sorted keys, no whitespace,
UTF-8) and hash with SHA-256 to obtain ``h_I``. Because the payload MAC is
computed over ``h_I`` (see :mod:`truthprint.payload`), any transformation that
changes a locked field changes ``h_I`` and breaks attribution -- this is the
tamper-detection property.
"""
from __future__ import annotations

import hashlib
import json

__all__ = ["canonical_json", "canonical_digest", "invariant_eq"]


def canonical_json(invariants: dict) -> str:
    """Deterministic, whitespace-independent JSON serialization."""
    return json.dumps(invariants, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def canonical_digest(invariants: dict) -> bytes:
    """h_I = SHA-256(canonical_json(I))."""
    return hashlib.sha256(canonical_json(invariants).encode("utf-8")).digest()


def invariant_eq(a: dict, b: dict) -> bool:
    """InvariantEq(a, b): True iff the two invariant sets are identical
    after canonicalization. Sound checkers may project onto locked fields
    before calling this; here we compare the full contract."""
    return canonical_digest(a) == canonical_digest(b)
