"""Tests for meaning-based provenance authentication."""
from truthprint.provenance import (register_tag, authenticate,
                                   document_attribution, CONTRACTS)

KEY = b"truthprint-challenge-key-01234567"[:32]
NONCE = b"nonce-xyz-01"


def _inv(**kw):
    base = {"agent": "the developer", "patient": "server error",
            "predicate": "FIX", "polarity": "positive", "quantity": 1,
            "time_dir": "previous", "modality": "asserted",
            "attribution": "none", "causation": "none"}
    base.update(kw)
    return base


def test_exact_recovery_authenticates():
    gold = _inv()
    tag = register_tag(KEY, gold, NONCE, "D-s1", "core6")
    # verifier recovered identical contract fields
    assert authenticate(KEY, dict(gold), NONCE, "D-s1", tag, "core6")


def test_meaning_altering_edit_is_rejected():
    gold = _inv(polarity="positive")
    tag = register_tag(KEY, gold, NONCE, "D-s1", "core6")
    tampered = _inv(polarity="negative")   # flipped a contract field
    assert not authenticate(KEY, tampered, NONCE, "D-s1", tag, "core6")


def test_noncontract_field_change_does_not_break_core6():
    # 'patient' is NOT in core6; changing it must not affect authentication
    gold = _inv(patient="server error")
    tag = register_tag(KEY, gold, NONCE, "D-s1", "core6")
    other = _inv(patient="memory leak")
    assert authenticate(KEY, other, NONCE, "D-s1", tag, "core6")
    # but under full9 (which includes patient) it must be rejected
    tag9 = register_tag(KEY, gold, NONCE, "D-s1", "full9")
    assert not authenticate(KEY, other, NONCE, "D-s1", tag9, "full9")


def test_wrong_key_or_nonce_fails():
    gold = _inv()
    tag = register_tag(KEY, gold, NONCE, "D-s1", "core6")
    assert not authenticate(b"x" * 32, dict(gold), NONCE, "D-s1", tag, "core6")
    assert not authenticate(KEY, dict(gold), b"other-nonce", "D-s1", tag, "core6")


def test_document_attribution_threshold():
    assert document_attribution([True, True, False, True], 0.5)
    assert not document_attribution([True, False, False, False], 0.5)
    assert not document_attribution([], 0.5)
