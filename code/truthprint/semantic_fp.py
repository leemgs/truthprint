"""Semantic-collision false-positive floor for meaning-digest provenance.

The meaning-digest scheme (:mod:`truthprint.provenance`) authenticates a
sentence iff its recovered invariant *contract* reproduces a keyed tag. The
cryptographic analysis bounds a *fresh* tag collision by ``2**-tau``. But two
genuinely distinct yet low-entropy legitimate generations that share the same
contract *digest* collide **before** the tag is ever checked: their digests are
equal, so the tag matches deterministically. The achievable false-positive rate
is therefore bounded below by the *contract-collision probability*, governed by
the entropy of the chosen contract on the deployment text -- not by ``tau``.

This module measures that floor on the closed-domain corpus, so the paper can
report the quantity a deployment must estimate on its own text:

  * the enumerated contract space ``|C|`` and its max entropy ``log2 |C|``;
  * the empirical Shannon and collision (Renyi-2) entropies of the observed
    contract distribution; and
  * the unbiased pairwise collision probability -- the expected false positive
    of authenticating one sentence against a *different* sentence's tag, which
    is exactly what ``scripts/eval_provenance.py`` estimates against a random
    ``other``.

The headline finding is a consistency check: the ``0.001``--``0.010`` false
positives reported for real MT are the contract-collision floor (``~1/192`` for
the six-field ``core6`` contract), not the ``2**-32`` cryptographic bound.
Real, non-templated text has *lower* contract entropy than this uniform closed
domain, so its floor is *higher*; estimating it per corpus is a deployment
prerequisite, especially for short or formulaic text.
"""
from __future__ import annotations

import math
import random
from collections import Counter

from .challenge import ext_invariants, sample_fact
from .provenance import CONTRACTS, contract_digest

__all__ = ["DOMAIN_CARDINALITY", "space_size", "measure"]

# Field value cardinalities of the closed-domain generator
# (truthprint.challenge.sample_fact / ext_invariants). ``predicate`` is fixed to
# "FIX" in this frontend, so it contributes 0 bits (cardinality 1).
DOMAIN_CARDINALITY = {
    "agent": 4,
    "patient": 4,
    "predicate": 1,
    "quantity": 4,      # sample_fact draws from {1, 2, 3, 5}
    "polarity": 2,
    "time_dir": 2,
    "modality": 3,
    "attribution": 3,
    "causation": 3,
}


def space_size(fields: list[str]) -> int:
    """Enumerated number of distinct contracts over ``fields``."""
    s = 1
    for f in fields:
        s *= DOMAIN_CARDINALITY[f]
    return s


def measure(n_facts: int = 800, seed: int = 7, tau_bits: int = 32) -> dict:
    """Measure the semantic-collision FP floor per named contract.

    Returns a JSON-serializable dict with, for each contract in
    :data:`truthprint.provenance.CONTRACTS`, the enumerated space size, the
    observed entropies, and the unbiased pairwise contract-collision
    probability (the semantic false-positive floor).
    """
    rng = random.Random(seed)
    facts = [ext_invariants(sample_fact(rng)) for _ in range(n_facts)]

    out = {
        "n_facts": n_facts,
        "seed": seed,
        "tau_bits": tau_bits,
        "crypto_floor": 2.0 ** (-tau_bits),
        "contracts": {},
    }
    for name, fields in CONTRACTS.items():
        digests = [contract_digest(inv, fields).hex() for inv in facts]
        counts = Counter(digests)
        n = len(digests)
        probs = [c / n for c in counts.values()]
        # Unbiased pairwise collision: P(two distinct draws share a contract).
        pairwise_collision = (
            sum(c * (c - 1) for c in counts.values()) / (n * (n - 1))
            if n > 1 else float("nan")
        )
        shannon = -sum(p * math.log2(p) for p in probs)
        renyi2 = -math.log2(sum(p * p for p in probs))
        space = space_size(fields)
        out["contracts"][name] = {
            "fields": list(fields),
            "space_size": space,
            "max_entropy_bits": math.log2(space),
            "distinct_observed": len(counts),
            "shannon_entropy_bits": shannon,
            "collision_entropy_bits": renyi2,
            "collision_prob": pairwise_collision,
            "uniform_floor": 1.0 / space,
            "crypto_floor_ratio": pairwise_collision / (2.0 ** (-tau_bits)),
        }
    return out
