"""Tests for the optional embedding backend and its baselines.

All tests that need real weights skip cleanly when ``model2vec`` or the model is
unavailable, so the stdlib-only core and offline CI are unaffected.
"""
import pytest

from truthprint import embedding as E


def test_keyed_hyperplanes_deterministic_and_keyed():
    p1 = E.keyed_hyperplanes(b"key-a", 8, 4)
    p1b = E.keyed_hyperplanes(b"key-a", 8, 4)
    p2 = E.keyed_hyperplanes(b"key-b", 8, 4)
    assert p1 == p1b            # deterministic given key
    assert p1 != p2             # depends on the key (Kerckhoffs)
    assert len(p1) == 4 and len(p1[0]) == 8


def test_simhash_and_hamming_pure():
    planes = E.keyed_hyperplanes(b"k", 4, 6)
    a = E.simhash_bits([1.0, 0.0, 0.0, 0.0], planes)
    b = E.simhash_bits([1.0, 0.0, 0.0, 0.0], planes)
    assert a == b
    assert E.hamming(a, b) == 0
    c = E.simhash_bits([-1.0, 0.0, 0.0, 0.0], planes)
    assert 0 <= E.hamming(a, c) <= 6


def test_cosine():
    assert abs(E.cosine([1, 0], [1, 0]) - 1.0) < 1e-9
    assert abs(E.cosine([1, 0], [0, 1])) < 1e-9


# --------- tests below need the real encoder; skip if unavailable ---------- #
_HAVE = E.available()
needs_model = pytest.mark.skipif(not _HAVE, reason="embedding model unavailable")


@needs_model
def test_real_embedding_crosslingual_signal():
    v = E.embed(["The developer fixed the server error.",
                 "개발자가 서버 오류를 수정했다.",
                 "The cat sat on the mat."])
    # a translation is far closer than an unrelated sentence
    assert E.cosine(v[0], v[1]) > E.cosine(v[0], v[2]) + 0.2


@needs_model
def test_semstamp_target_bits_deterministic():
    from truthprint.semstamp import target_bits
    t1 = target_bits(b"k", b"n", "s1", 8)
    t2 = target_bits(b"k", b"n", "s1", 8)
    t3 = target_bits(b"k", b"n", "s2", 8)
    assert t1 == t2 and len(t1) == 8
    assert t1 != t3


@needs_model
def test_neural_embed_extractor_interface():
    from truthprint.neural_embed_parser import NeuralEmbedExtractor, CATEGORICAL
    from truthprint.multilingual import FIELDS
    ex = NeuralEmbedExtractor()
    out = ex.extract("The developer did not fix the server error.", "en")
    assert set(out.keys()) == set(FIELDS)
    # categorical fields are answered (not None); open/numeric abstained
    for f in CATEGORICAL:
        assert out[f] is not None
    assert out["agent"] is None and out["quantity"] is None
