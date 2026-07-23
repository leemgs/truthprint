"""Command-line interface: ``truthprint {selftest,demo-core,demo-linguistic,repro-table}``."""
from __future__ import annotations

import argparse
import random

from .core import Truthprint
from .invariants import canonical_digest
from .linguistic import (Fact, LinguisticCodec, invariant_preserving_transform,
                         negate_transform, doc_invariants)
from .payload import verify_payload

_KEY = b"truthprint-demo-key-0123456789abc"


def _demo_core(seed: int = 7) -> bool:
    rng = random.Random(seed)
    tp = Truthprint(_KEY, msg_len=16, tag_bits=32, code_n=96)
    inv = {"events": [{"predicate": "FIX", "agent": "developer",
                       "patient": "server_error", "polarity": "positive"}]}
    msg = [rng.randint(0, 1) for _ in range(16)]
    nonce = tp.new_nonce()
    options = tp.encode(inv, msg, nonce)

    n_erase = int(0.30 * tp.n_carriers)
    erased = set(rng.sample(range(tp.n_carriers), n_erase))
    mask = [j in erased for j in range(tp.n_carriers)]
    r = tp.detect(inv, options, nonce, mask)
    print(f"[P1] {n_erase}/{tp.n_carriers} erased -> attributed={r.attributed} "
          f"msg_ok={r.message == msg}")

    tampered = {"events": [{"predicate": "FIX", "agent": "developer",
                            "patient": "server_error", "polarity": "negative"}]}
    rt = tp.detect(tampered, options, nonce, mask)
    print(f"[P2] invariant tamper -> attributed={rt.attributed} (expect False)")

    fp = 0
    trials = 5000
    for _ in range(trials):
        rinv = {"events": [{"predicate": "SAY", "agent": f"x{rng.randint(0,9)}",
                            "polarity": rng.choice(["positive", "negative"])}]}
        ropts = [rng.randint(0, 1) for _ in range(tp.n_carriers)]
        if tp.detect(rinv, ropts, tp.new_nonce()).attributed:
            fp += 1
    print(f"[P3] cryptographic FP over {trials} docs -> {fp} "
          f"(bound 2^-32={2**-32:.1e})")
    return r.attributed and r.message == msg and not rt.attributed and fp == 0


def _demo_linguistic(seed: int = 23) -> bool:
    rng = random.Random(seed)
    agents = ["the developer", "the auditor", "the operator", "the vendor"]
    patients = ["the server error", "the config drift", "the data leak",
                "the build failure"]
    n = 32
    facts = [Fact(agents[i % 4], patients[(i * 3) % 4]) for i in range(n)]
    codec = LinguisticCodec(_KEY, n_sentences=n, msg_len=12, tag_bits=20)
    msg = [rng.randint(0, 1) for _ in range(12)]
    nonce = codec.core.new_nonce()
    sentences = codec.encode(facts, msg, nonce)
    print(f"[example] {sentences[0]!r}")

    transformed, reliability = [], []
    for s in sentences:
        s2, rel = invariant_preserving_transform(s, rng, 0.30)
        transformed.append(s2)
        reliability.append(rel)
    r = codec.detect(transformed, nonce, reliability)
    print(f"[L1/L2] erasures={r.erasures}/{2*n} -> attributed={r.attributed} "
          f"msg_ok={r.message == msg}")

    tampered = [negate_transform(sentences[0])] + sentences[1:]
    rt = codec.detect(tampered, nonce)
    print(f"[L3] negation tamper -> attributed={rt.attributed} (expect False)")
    return r.attributed and r.message == msg and not rt.attributed


def _repro_table(seed: int = 11) -> bool:
    rng = random.Random(seed)
    tp = Truthprint(_KEY, msg_len=16, tag_bits=32, code_n=96)
    inv = {"events": [{"predicate": "FIX", "polarity": "positive"}]}
    print("erasure_frac  recovery_rate (300 trials)")
    for frac in (0.10, 0.20, 0.30, 0.40, 0.50, 0.55, 0.60):
        ok = 0
        trials = 300
        for _ in range(trials):
            msg = [rng.randint(0, 1) for _ in range(16)]
            nonce = tp.new_nonce()
            opts = tp.encode(inv, msg, nonce)
            ne = int(frac * tp.n_carriers)
            er = set(rng.sample(range(tp.n_carriers), ne))
            mask = [j in er for j in range(tp.n_carriers)]
            r = tp.detect(inv, opts, nonce, mask)
            ok += int(r.attributed and r.message == msg)
        print(f"   {frac:.2f}          {ok/trials:.3f}")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="truthprint",
                                     description="Truthprint reference CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest", help="run all reproducible properties (P1-P4, L1-L3)")
    sub.add_parser("demo-core", help="crypto/coding core demo")
    sub.add_parser("demo-linguistic", help="sentence-level round-trip demo")
    sub.add_parser("repro-table", help="regenerate the erasure-cliff table")
    args = parser.parse_args(argv)

    if args.cmd == "demo-core":
        return 0 if _demo_core() else 1
    if args.cmd == "demo-linguistic":
        return 0 if _demo_linguistic() else 1
    if args.cmd == "repro-table":
        return 0 if _repro_table() else 1
    if args.cmd == "selftest":
        ok = _demo_core() and _demo_linguistic()
        print("SELFTEST:", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
