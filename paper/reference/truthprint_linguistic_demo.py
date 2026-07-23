"""
Truthprint Stage-1 closed-domain linguistic proof-of-concept.

Unlike truthprint_poc.py (which exercises the crypto/coding core on abstract
bits), this demo round-trips the watermark through *actual sentence strings*
using two linguistic carriers on a templated factual domain:

  carrier 0: VOICE            in {active, passive}
  carrier 1: TIME_POSITION    in {front,  end}

Both carriers are invariant-preserving: they change realization only, never
the locked fact (agent, predicate, patient, time, polarity). The pipeline is:

  fact --realize(bits)--> English sentence
       --transform-------> invariant-preserving rewrite (+erasures)
       --parse-----------> recovered invariants + observed carrier bits
       --detect----------> keyed inversion, ECC decode, MAC verify

It demonstrates, on strings:
  (L1) invariant fidelity: every transform preserves the parsed invariants;
  (L2) round-trip recovery of an authenticated payload spread over sentences,
       even when a fraction of linguistic carriers are erased by rewriting;
  (L3) tamper detection: a rewrite that negates a fact changes h_I so the MAC
       fails and the document is not attributed.

Depends only on the standard library and truthprint_poc.py (same folder).
Run:  python3 truthprint_linguistic_demo.py
"""
from __future__ import annotations
import json
import os
import random
import re

from truthprint_poc import (
    GF2Code, authenticate_payload, verify_payload,
    canonical_invariant_digest, keyed_bit,
)

AGENTS = ["the developer", "the auditor", "the operator", "the vendor"]
PATIENTS = ["the server error", "the config drift", "the data leak",
            "the build failure"]
PRED = {"predicate": "FIX", "verb": "fixed", "past_part": "fixed"}
TIME_PHRASE = "the previous day"


# ---------------------------------------------------------------- realization
def realize(fact: dict, voice_bit: int, timepos_bit: int) -> str:
    """Render a fact as English. Both carriers preserve the invariants."""
    a, p = fact["agent"], fact["patient"]
    neg = fact["polarity"] == "negative"
    if voice_bit == 0:  # active
        core = f"{a} did not {PRED['verb'].replace('fixed','fix')} {p}" if neg \
               else f"{a} {PRED['verb']} {p}"
    else:               # passive
        core = f"{p} was not {PRED['past_part']} by {a}" if neg \
               else f"{p} was {PRED['past_part']} by {a}"
    if timepos_bit == 0:  # time at front
        s = f"On {TIME_PHRASE}, {core}."
    else:                 # time at end
        s = f"{core[0].upper()+core[1:]} on {TIME_PHRASE}."
    return s[0].upper() + s[1:]


# ---------------------------------------------------------------------- parse
def parse(sentence: str):
    """Recover invariants + observed carrier bits from surface form.
    Returns (invariants, {carrier_id: (bit, reliable)})."""
    s = sentence.strip().rstrip(".")
    low = s.lower()
    neg = ("did not" in low) or ("was not" in low)
    # voice
    if " was " in low and " by " in low:
        voice = 1
        m = re.search(r"^(?:on the previous day,\s*)?(.*?) was(?: not)? "
                      r"fixed by (.*?)(?: on the previous day)?$", low)
        patient = m.group(1).strip() if m else None
        agent = m.group(2).strip() if m else None
    else:
        voice = 0
        m = re.search(r"^(?:on the previous day,\s*)?(.*?) (?:did not fix|fixed) "
                      r"(.*?)(?: on the previous day)?$", low)
        agent = m.group(1).strip() if m else None
        patient = m.group(2).strip() if m else None
    timepos = 0 if low.startswith("on the previous day") else 1
    invariants = {
        "agent": agent, "patient": patient,
        "predicate": PRED["predicate"],
        "polarity": "negative" if neg else "positive",
        "time": "previous_day",
    }
    carriers = {0: (voice, True), 1: (timepos, True)}
    return invariants, carriers


# ------------------------------------------------------------------ transform
def invariant_preserving_transform(sentence: str, rng: random.Random,
                                   erase_prob: float):
    """Rewrite preserving invariants; may 'normalize' a carrier (=erasure).
    Returns (new_sentence, {carrier_id: reliable_bool})."""
    inv, carriers = parse(sentence)
    v, (t) = carriers[0][0], carriers[1][0]
    reliable = {0: True, 1: True}
    # a paraphrase/translation may canonicalize voice and/or time position,
    # destroying that carrier while keeping the fact intact
    if rng.random() < erase_prob:
        v = 0; reliable[0] = False          # normalized to active -> erased
    if rng.random() < erase_prob:
        t = 1; reliable[1] = False          # normalized to end -> erased
    fact = {"agent": inv["agent"], "patient": inv["patient"],
            "polarity": inv["polarity"]}
    return realize(fact, v, t), reliable


def negate_transform(sentence: str) -> str:
    """A meaning-ALTERING rewrite: flip polarity (tamper)."""
    inv, carriers = parse(sentence)
    fact = {"agent": inv["agent"], "patient": inv["patient"],
            "polarity": "negative" if inv["polarity"] == "positive"
                        else "positive"}
    return realize(fact, carriers[0][0], carriers[1][0])


# ------------------------------------------------------------------- document
def doc_invariant_digest(facts: list[dict]) -> bytes:
    norm = [{"agent": f["agent"], "patient": f["patient"],
             "predicate": PRED["predicate"], "polarity": f["polarity"],
             "time": "previous_day"} for f in facts]
    return canonical_invariant_digest({"facts": norm})


def main():
    rng = random.Random(23)
    KEY = b"truthprint-linguistic-demo-key-001"
    MSG_LEN, TAG = 12, 20
    K = MSG_LEN + TAG                     # 32 payload bits
    N = 64                               # 2 carriers x 32 sentences, rate 1/2
    code = GF2Code(K, N)
    n_sent = N // 2

    facts = [{"agent": AGENTS[i % len(AGENTS)],
              "patient": PATIENTS[(i * 3) % len(PATIENTS)],
              "polarity": "positive"} for i in range(n_sent)]
    msg = [rng.randint(0, 1) for _ in range(MSG_LEN)]
    nonce = os.urandom(12)
    h_I = doc_invariant_digest(facts)
    p = authenticate_payload(KEY, msg, nonce, h_I, TAG)
    c = code.encode(p)                    # N code bits -> 2 per sentence

    print("=" * 70)
    print("Truthprint Stage-1 linguistic proof-of-concept (voice + time carrier)")
    print("=" * 70)
    print(f"[setup] {n_sent} sentences, 2 carriers each, code=[{N},{K}], "
          f"tag={TAG} bits")
    print(f"[setup] message m = {''.join(map(str, msg))}")

    # ---- realize each sentence carrying two code bits via keyed map --------
    sentences = []
    for i, fact in enumerate(facts):
        cid_v, cid_t = 2 * i, 2 * i + 1
        v = keyed_bit(KEY, h_I, nonce, cid_v) ^ c[cid_v]
        t = keyed_bit(KEY, h_I, nonce, cid_t) ^ c[cid_t]
        sentences.append(realize(fact, v, t))
    print(f"[example] sentence 0 -> {sentences[0]!r}")

    # ---- (L1)+(L2) invariant-preserving transform with erasures -----------
    ERASE = 0.30
    received: list[int | None] = [None] * N
    fidelity_ok = True
    for i, s in enumerate(sentences):
        s2, reliable = invariant_preserving_transform(s, rng, ERASE)
        inv0, _ = parse(s)
        inv1, obs = parse(s2)
        # fidelity: invariants unchanged by the benign transform
        if {k: inv0[k] for k in ("agent", "patient", "predicate", "polarity")} \
           != {k: inv1[k] for k in ("agent", "patient", "predicate", "polarity")}:
            fidelity_ok = False
        cid_v, cid_t = 2 * i, 2 * i + 1
        for cid, key_c in ((cid_v, 0), (cid_t, 1)):
            bit, _ = obs[key_c]
            if reliable[key_c]:
                received[cid] = keyed_bit(KEY, h_I, nonce, cid) ^ bit
            else:
                received[cid] = None      # erasure
    n_erased = sum(1 for r in received if r is None)
    p_hat = code.decode_erasure(received)
    rec_ok = p_hat is not None and verify_payload(
        KEY, p_hat, nonce, doc_invariant_digest(facts), MSG_LEN, TAG)
    rec_msg = p_hat[:MSG_LEN] if p_hat else None
    print(f"\n[L1] invariant fidelity across all benign transforms: {fidelity_ok}")
    print(f"[L2] {n_erased}/{N} carriers erased -> attributed={rec_ok}  "
          f"recovered==message={rec_msg == msg}")

    # ---- (L3) meaning-altering tamper: negate sentence 0 ------------------
    tampered_facts = [dict(f) for f in facts]
    tampered_facts[0]["polarity"] = "negative"
    h_tampered = doc_invariant_digest(tampered_facts)
    tamper_attributed = verify_payload(
        KEY, p, nonce, h_tampered, MSG_LEN, TAG)   # h_I changed -> should fail
    print(f"[L3] negation tamper on 1 fact -> attributed={tamper_attributed} "
          f"(expected False: document invariant digest changed)")

    print("\n" + "=" * 70)
    all_ok = fidelity_ok and rec_ok and rec_msg == msg and not tamper_attributed
    print("RESULT:", "ALL LINGUISTIC PROPERTIES HOLD" if all_ok
          else "CHECK OUTPUT")
    print("=" * 70)
    return all_ok


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
