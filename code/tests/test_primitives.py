import random

import pytest

from truthprint import (GF2Code, canonical_digest, invariant_eq,
                        authenticate_payload, verify_payload,
                        keyed_bit, realize_option, recover_symbol)


def test_invariant_digest_is_order_independent():
    a = {"x": 1, "y": [1, 2], "z": {"p": "a", "q": "b"}}
    b = {"z": {"q": "b", "p": "a"}, "y": [1, 2], "x": 1}
    assert canonical_digest(a) == canonical_digest(b)
    assert invariant_eq(a, b)


def test_invariant_digest_changes_on_tamper():
    a = {"polarity": "positive"}
    b = {"polarity": "negative"}
    assert canonical_digest(a) != canonical_digest(b)
    assert not invariant_eq(a, b)


def test_payload_roundtrip_and_tamper():
    key, nonce, h = b"k" * 32, b"n" * 12, canonical_digest({"a": 1})
    msg = [1, 0, 1, 1, 0, 0, 1, 0]
    p = authenticate_payload(key, msg, nonce, h, tag_bits=32)
    assert verify_payload(key, p, nonce, h, len(msg), 32)
    # flip a message bit -> tag no longer matches
    p2 = p[:]
    p2[0] ^= 1
    assert not verify_payload(key, p2, nonce, h, len(msg), 32)
    # different invariant digest -> fails
    assert not verify_payload(key, p, nonce, canonical_digest({"a": 2}),
                              len(msg), 32)


def test_code_encode_is_systematic():
    code = GF2Code(k=8, n=16)
    p = [1, 0, 1, 1, 0, 1, 0, 0]
    c = code.encode(p)
    assert c[:8] == p and len(c) == 16


def test_code_recovers_with_no_erasures():
    code = GF2Code(k=8, n=16)
    p = [random.randint(0, 1) for _ in range(8)]
    c = code.encode(p)
    assert code.decode_erasure(list(c)) == p


def test_code_recovers_under_partial_erasure():
    rng = random.Random(1)
    code = GF2Code(k=24, n=48)
    p = [rng.randint(0, 1) for _ in range(24)]
    c = code.encode(p)
    recv = list(c)
    for j in rng.sample(range(48), 20):   # erase 20/48 < rate limit
        recv[j] = None
    assert code.decode_erasure(recv) == p


def test_code_fails_beyond_rate_limit():
    rng = random.Random(2)
    code = GF2Code(k=24, n=48)
    c = code.encode([rng.randint(0, 1) for _ in range(24)])
    recv = list(c)
    for j in rng.sample(range(48), 40):   # erase far beyond capacity
        recv[j] = None
    assert code.decode_erasure(recv) is None


def test_keyed_carrier_roundtrip():
    key, h, nonce = b"k" * 32, b"h" * 32, b"n" * 12
    for cid in range(10):
        for bit in (0, 1):
            opt = realize_option(key, h, nonce, cid, bit)
            assert recover_symbol(key, h, nonce, cid, opt) == bit


def test_keyed_map_is_invariant_bound():
    key, nonce = b"k" * 32, b"n" * 12
    h1, h2 = canonical_digest({"p": "positive"}), canonical_digest({"p": "negative"})
    v1 = [realize_option(key, h1, nonce, j, 1) for j in range(64)]
    v2 = [realize_option(key, h2, nonce, j, 1) for j in range(64)]
    diff = sum(a != b for a, b in zip(v1, v2))
    assert 16 <= diff <= 48   # ~N/2, no global rule
