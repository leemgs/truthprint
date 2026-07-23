"""Truthprint: invariant-constrained semantic provenance watermarking.

Reference implementation of the language-independent core (invariant digest,
authenticated payload, GF(2) erasure-coded carriers) plus a closed-domain
linguistic layer that round-trips the watermark through real sentences.

Quick start::

    from truthprint import Truthprint
    tp = Truthprint(key=b"0" * 32)
    inv = {"events": [{"predicate": "FIX", "polarity": "positive"}]}
    msg = [1, 0, 1, 0] * 4                      # 16-bit message
    nonce = tp.new_nonce()
    options = tp.encode(inv, msg, nonce)        # realized carrier options
    result = tp.detect(inv, options, nonce)     # -> DetectionResult
    assert result.attributed and result.message == msg
"""
from __future__ import annotations

from .core import Truthprint, DetectionResult
from .coding import GF2Code
from .invariants import canonical_digest, canonical_json, invariant_eq
from .payload import authenticate_payload, verify_payload
from .carriers import keyed_bit, realize_option, recover_symbol
from .linguistic import (Fact, LinguisticCodec, realize, parse,
                         doc_invariants, invariant_preserving_transform,
                         negate_transform)

__version__ = "0.1.0"

__all__ = [
    "Truthprint", "DetectionResult", "GF2Code",
    "canonical_digest", "canonical_json", "invariant_eq",
    "authenticate_payload", "verify_payload",
    "keyed_bit", "realize_option", "recover_symbol",
    "Fact", "LinguisticCodec", "realize", "parse", "doc_invariants",
    "invariant_preserving_transform", "negate_transform",
]
