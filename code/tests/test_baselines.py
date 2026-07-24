"""Regression tests for the comparison baselines (truthprint.baselines).

These assert the *qualitative* behaviour the paper's Tables V/VI depend on:
every baseline detects a clean watermark, and under a heavy translation
channel the token-level marks collapse toward the null while the semantic-layer
marks survive. The behaviour is derived from signal placement, so these bounds
are stable across seeds.
"""
import random

from truthprint.baselines import (make_document, channel,
    KGWGreenList, DEWEditRobust, SemStampLSH, SWANStructural)

KEY = b"truthprint-demo-key-0123456789abc"
TOKEN_METHODS = [KGWGreenList, DEWEditRobust]
SEMANTIC_METHODS = [SemStampLSH, SWANStructural]


def _clean_and_null(method, seed):
    rng = random.Random(seed)
    base = make_document(32, 8, rng)
    z_clean = method.score(method.embed(base, KEY), KEY)
    z_null = method.score(make_document(32, 8, rng), KEY)
    return z_clean, z_null


def test_clean_watermark_detectable():
    """Every baseline separates a clean watermark from the null by a wide z."""
    for M in TOKEN_METHODS + SEMANTIC_METHODS:
        z_clean, z_null = _clean_and_null(M(), seed=11)
        assert z_clean > 4.0, f"{M.__name__} clean z too low: {z_clean}"
        assert z_null < 3.0, f"{M.__name__} null z too high: {z_null}"


def test_token_methods_collapse_under_translation():
    """Token-identity marks lose the signal when translation replaces tokens."""
    rng = random.Random(7)
    for M in TOKEN_METHODS:
        m = M()
        base = make_document(32, 8, rng)
        got = channel(m.embed(base, KEY), tau_tok=0.92, eps_inv=0.30, rng=rng)
        z = m.score(got, KEY)
        assert z < 2.0, f"{M.__name__} should collapse, got z={z}"


def test_semantic_methods_survive_translation():
    """Meaning-layer marks stay detectable under the same translation channel."""
    rng = random.Random(7)
    for M in SEMANTIC_METHODS:
        m = M()
        base = make_document(32, 8, rng)
        got = channel(m.embed(base, KEY), tau_tok=0.92, eps_inv=0.30, rng=rng)
        z = m.score(got, KEY)
        assert z > 3.0, f"{M.__name__} should survive, got z={z}"
