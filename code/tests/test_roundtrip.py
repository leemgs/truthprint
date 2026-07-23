import random

from truthprint import Truthprint
from truthprint.linguistic import (Fact, LinguisticCodec,
                                   invariant_preserving_transform,
                                   negate_transform)

KEY = b"truthprint-test-key-0123456789abc"


# ----------------------------- core: P1-P4 --------------------------------
def test_P1_recovery_under_erasure():
    rng = random.Random(7)
    tp = Truthprint(KEY, msg_len=16, tag_bits=32, code_n=96)
    inv = {"events": [{"predicate": "FIX", "polarity": "positive"}]}
    msg = [rng.randint(0, 1) for _ in range(16)]
    nonce = tp.new_nonce()
    opts = tp.encode(inv, msg, nonce)
    mask = [j in set(rng.sample(range(96), 28)) for j in range(96)]
    r = tp.detect(inv, opts, nonce, mask)
    assert r.attributed and r.message == msg


def test_P2_invariant_binding():
    tp = Truthprint(KEY, msg_len=16, tag_bits=32, code_n=96)
    inv = {"events": [{"predicate": "FIX", "polarity": "positive"}]}
    msg = [1, 0] * 8
    nonce = tp.new_nonce()
    opts = tp.encode(inv, msg, nonce)
    tampered = {"events": [{"predicate": "FIX", "polarity": "negative"}]}
    assert not tp.detect(tampered, opts, nonce).attributed


def test_P3_cryptographic_false_positive_rate():
    rng = random.Random(3)
    tp = Truthprint(KEY, msg_len=16, tag_bits=32, code_n=96)
    fp = 0
    trials = 5000
    for _ in range(trials):
        inv = {"events": [{"predicate": "SAY", "agent": rng.randint(0, 9)}]}
        opts = [rng.randint(0, 1) for _ in range(96)]
        if tp.detect(inv, opts, tp.new_nonce()).attributed:
            fp += 1
    assert fp == 0  # bound 2^-32 ~ 2.3e-10


def test_P4_no_global_rule_via_detect():
    tp = Truthprint(KEY, msg_len=8, tag_bits=16, code_n=48)
    inv = {"events": [{"predicate": "FIX", "polarity": "positive"}]}
    msg = [1, 0, 1, 1, 0, 0, 1, 0]
    nonce = tp.new_nonce()
    opts = tp.encode(inv, msg, nonce)
    # detecting with a different nonce should not attribute
    assert not tp.detect(inv, opts, tp.new_nonce()).attributed


# -------------------------- linguistic: L1-L3 -----------------------------
def _facts(n):
    agents = ["the developer", "the auditor", "the operator", "the vendor"]
    patients = ["the server error", "the config drift", "the data leak",
                "the build failure"]
    return [Fact(agents[i % 4], patients[(i * 3) % 4]) for i in range(n)]


def test_L1_invariant_fidelity_and_L2_recovery():
    rng = random.Random(23)
    n = 32
    codec = LinguisticCodec(KEY, n_sentences=n, msg_len=12, tag_bits=20)
    facts = _facts(n)
    msg = [rng.randint(0, 1) for _ in range(12)]
    nonce = codec.core.new_nonce()
    sentences = codec.encode(facts, msg, nonce)

    from truthprint.linguistic import parse
    transformed, reliability = [], []
    for i, s in enumerate(sentences):
        s2, rel = invariant_preserving_transform(s, rng, 0.30)
        # L1: benign transform preserves the locked invariants
        inv0, _ = parse(s)
        inv1, _ = parse(s2)
        assert {k: inv0[k] for k in ("agent", "patient", "predicate", "polarity")} \
            == {k: inv1[k] for k in ("agent", "patient", "predicate", "polarity")}
        transformed.append(s2)
        reliability.append(rel)
    r = codec.detect(transformed, nonce, reliability)   # L2
    assert r.attributed and r.message == msg


def test_L3_tamper_detection():
    rng = random.Random(5)
    n = 32
    codec = LinguisticCodec(KEY, n_sentences=n, msg_len=12, tag_bits=20)
    facts = _facts(n)
    msg = [rng.randint(0, 1) for _ in range(12)]
    nonce = codec.core.new_nonce()
    sentences = codec.encode(facts, msg, nonce)
    tampered = [negate_transform(sentences[0])] + sentences[1:]
    assert not codec.detect(tampered, nonce).attributed
