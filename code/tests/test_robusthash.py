"""Robust-hashing baselines (stdlib-only parts) -- no model needed."""
from truthprint.robusthash import (sha256_hex, exact_verify, shingles, jaccard,
                                   minhash_signature, minhash_similarity,
                                   minhash_verify)


def test_exact_hash_identity_and_normalization():
    assert exact_verify("The developer fixed it.", "the  developer FIXED it.")
    assert not exact_verify("The developer fixed it.",
                            "The developer did not fix it.")


def test_exact_hash_dies_under_translation():
    # a translated string is a different surface -> exact hash cannot match
    assert not exact_verify("The developer fixed the server error.",
                            "개발자가 서버 오류를 수정했다.")


def test_shingles_and_jaccard():
    a = shingles("abcabc", k=3)
    assert "abc" in a and "bca" in a and "cab" in a
    assert jaccard(set(), set()) == 1.0
    assert jaccard({"x"}, set()) == 0.0
    s = "the developer fixed the server error"
    assert jaccard(shingles(s), shingles(s)) == 1.0


def test_minhash_self_similarity_high_and_cross_low():
    a = minhash_signature("the developer fixed the server error")
    a2 = minhash_signature("the developer fixed the server error")
    assert minhash_similarity(a, a2) == 1.0
    b = minhash_signature("a completely unrelated sentence about cats and hats")
    assert minhash_similarity(a, b) < 0.5


def test_minhash_verify_near_duplicate():
    assert minhash_verify("the developer fixed the server error",
                          "the developer fixed the server error", threshold=0.5)
    assert not minhash_verify("the developer fixed the server error",
                              "an unrelated remark on gardening tools",
                              threshold=0.5)


def test_sha256_hex_stable():
    assert sha256_hex("Hello  World") == sha256_hex("hello world")
