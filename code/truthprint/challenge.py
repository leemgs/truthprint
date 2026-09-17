"""Field-level semantic challenge set for the typed-invariant contract.

This module operationalizes the paper's central claim -- that embedding
*similarity* cannot distinguish meaning-preserving realization changes from
lexically small but meaning-*altering* edits -- into a real, measured,
fully-offline experiment on actual sentence strings.

It extends the Stage-1 closed-domain frontend of :mod:`truthprint.linguistic`
from one predicate and polarity to **six protected (locked) fields**, each with
a minimal-pair generator:

    polarity     positive  <-> negative        ("fixed" / "did not fix")
    quantity     q         <-> q'              ("3 server errors" / "8 ...")
    time_dir     previous  <-> following       (before / after the reference day)
    modality     necessary <-> possible        ("must have" / "may have")
    attribution  report    <-> vendor          (who the claim is credited to)
    causation    cause     <-> purpose         ("because of" / "to prevent")

Two realization-only carriers remain watermark carriers exactly as in the base
linguistic layer:

    carrier 0: VOICE          in {active, passive}
    carrier 1: TIME_POSITION  in {front, end}

For each sampled fact we build two probes:

  * a **benign** probe: a meaning-preserving realization change (flip the two
    carriers, keep every locked field) -- attribution SHOULD survive; and
  * an **altering** probe: a single-field edit that changes one locked field --
    attribution SHOULD fail (this is tamper).

Three detectors judge each probe, so the ablation isolates *what each component
buys*:

  * ``typed``        -- Truthprint: re-parse -> typed invariants -> h_I -> MAC.
  * ``no_mac``       -- decode the payload but skip the h_I-bound MAC check
                        (attributes on carrier recovery alone).
  * ``embedding``    -- no h_I binding; attribute iff the payload decodes AND the
                        bag-of-words cosine to the reference surface is >= theta.

The grammar is finite and regular so :func:`parse` deterministically inverts
:func:`realize`; ``tests/test_challenge.py`` asserts round-trip over the whole
enumerated domain, so results are trustworthy within the closed domain. This is
a Stage-1 closed-domain demonstration, not a wide-coverage multilingual parser.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, replace

from .core import Truthprint

__all__ = [
    "ExtFact", "ext_invariants", "realize", "parse", "cosine_bow",
    "FIELDS", "sample_fact", "altering_edit", "run_challenge",
]

# ---- closed-domain vocabulary --------------------------------------------- #
AGENTS = ["the developer", "the engineer", "the operator", "the analyst"]
PATIENTS = ["server error", "memory leak", "config drift", "cache miss"]
_TIME_WORD = {"previous": "the previous day", "following": "the following day"}
_ATTR_PHRASE = {"none": "", "report": "according to the report, ",
                "vendor": "according to the vendor, "}
_CAUSE_TAIL = {"none": "", "cause": " because of the outage",
               "purpose": " to prevent the outage"}

# finite (polarity, modality, voice) -> verb-head table, so parse is exact.
# active heads take the patient as object; passive heads are followed by "by".
_ACTIVE_HEAD = {
    ("positive", "asserted"): "fixed",
    ("negative", "asserted"): "did not fix",
    ("positive", "necessary"): "must have fixed",
    ("negative", "necessary"): "must not have fixed",
    ("positive", "possible"): "may have fixed",
    ("negative", "possible"): "may not have fixed",
}
_PASSIVE_HEAD = {
    ("positive", "asserted"): "was fixed by",
    ("negative", "asserted"): "was not fixed by",
    ("positive", "necessary"): "must have been fixed by",
    ("negative", "necessary"): "must not have been fixed by",
    ("positive", "possible"): "may have been fixed by",
    ("negative", "possible"): "may not have been fixed by",
}
_ACTIVE_REV = {v: k for k, v in _ACTIVE_HEAD.items()}
_PASSIVE_REV = {v: k for k, v in _PASSIVE_HEAD.items()}

# the six protected fields exercised by the challenge set.
FIELDS = ["polarity", "quantity", "time_dir", "modality", "attribution",
          "causation"]


@dataclass(frozen=True)
class ExtFact:
    agent: str = "the developer"
    patient: str = "server error"
    quantity: int = 1
    polarity: str = "positive"       # positive | negative
    time_dir: str = "previous"       # previous | following
    modality: str = "asserted"       # asserted | necessary | possible
    attribution: str = "none"        # none | report | vendor
    causation: str = "none"          # none | cause | purpose


def ext_invariants(f: ExtFact) -> dict:
    """The locked semantic contract for one fact (carriers excluded)."""
    return {
        "agent": f.agent, "patient": f.patient, "predicate": "FIX",
        "quantity": f.quantity, "polarity": f.polarity,
        "time_dir": f.time_dir, "modality": f.modality,
        "attribution": f.attribution, "causation": f.causation,
    }


def doc_invariants(facts) -> dict:
    return {"facts": [ext_invariants(f) for f in facts]}


def _patient_phrase(f: ExtFact) -> str:
    if f.quantity == 1:
        return f"the {f.patient}"
    return f"{f.quantity} {f.patient}s"


# --------------------------------------------------------------- realization
def realize(f: ExtFact, voice_bit: int, timepos_bit: int) -> str:
    """Render a fact + two carrier bits to a sentence (closed grammar)."""
    attr = _ATTR_PHRASE[f.attribution]
    cause = _CAUSE_TAIL[f.causation]
    pp = _patient_phrase(f)
    if voice_bit == 0:  # active: agent HEAD patient
        head = _ACTIVE_HEAD[(f.polarity, f.modality)]
        core = f"{f.agent} {head} {pp}{cause}"
    else:               # passive: patient HEAD by agent
        head = _PASSIVE_HEAD[(f.polarity, f.modality)]
        core = f"{pp} {head} {f.agent}{cause}"
    tw = _TIME_WORD[f.time_dir]
    if timepos_bit == 0:  # time at front
        body = f"{attr}on {tw}, {core}"
    else:                 # time at end
        body = f"{attr}{core} on {tw}"
    return body[0].upper() + body[1:] + "."


# ---------------------------------------------------------------------- parse
def _strip_attr(low: str):
    for name, phrase in _ATTR_PHRASE.items():
        if phrase and low.startswith(phrase):
            return name, low[len(phrase):]
    return "none", low


def _strip_cause(s: str):
    for name, tail in _CAUSE_TAIL.items():
        if tail and s.endswith(tail):
            return name, s[: -len(tail)]
    return "none", s


def _parse_patient(pp: str):
    pp = pp.strip()
    m = pp.split(" ", 1)
    if pp.startswith("the "):
        return 1, pp[4:].strip()
    # "<q> <patient>s"
    qty = int(m[0])
    noun = m[1].strip()
    if noun.endswith("s"):
        noun = noun[:-1]
    return qty, noun


def parse(sentence: str):
    """Invert :func:`realize`. Returns ``(ExtFact, {carrier_id: (bit, ok)})``.

    Deterministic on the closed grammar; ``tests/test_challenge.py`` asserts
    round-trip over the enumerated domain.
    """
    s = sentence.strip()
    s = s[:-1] if s.endswith(".") else s
    low = s[0].lower() + s[1:] if s else s
    attribution, low = _strip_attr(low)

    # time position + time word
    if low.startswith("on "):
        timepos = 0
        rest = low[3:]
        for name, tw in _TIME_WORD.items():
            if rest.startswith(tw + ", "):
                time_dir = name
                core = rest[len(tw) + 2:]
                break
        else:
            raise ValueError(f"unparseable time-front: {sentence!r}")
    else:
        timepos = 1
        for name, tw in _TIME_WORD.items():
            if low.endswith(" on " + tw):
                time_dir = name
                core = low[: -(len(tw) + 4)]
                break
        else:
            raise ValueError(f"unparseable time-end: {sentence!r}")

    causation, core = _strip_cause(core)

    # match longest verb-heads first so "fixed" does not match inside
    # "must have fixed"; try passive (" ... by <agent>") then active.
    for head in sorted(_PASSIVE_REV, key=len, reverse=True):
        pol, mod = _PASSIVE_REV[head]
        marker = f" {head} "
        if marker in core:
            pp, agent = core.split(marker, 1)
            qty, patient = _parse_patient(pp)
            f = ExtFact(agent=agent.strip(), patient=patient, quantity=qty,
                        polarity=pol, time_dir=time_dir, modality=mod,
                        attribution=attribution, causation=causation)
            return f, {0: (1, True), 1: (timepos, True)}

    for head in sorted(_ACTIVE_REV, key=len, reverse=True):
        pol, mod = _ACTIVE_REV[head]
        marker = f" {head} "
        if marker in core:
            agent, pp = core.split(marker, 1)
            qty, patient = _parse_patient(pp)
            f = ExtFact(agent=agent.strip(), patient=patient, quantity=qty,
                        polarity=pol, time_dir=time_dir, modality=mod,
                        attribution=attribution, causation=causation)
            return f, {0: (0, True), 1: (timepos, True)}

    raise ValueError(f"unparseable core: {sentence!r}")


# ------------------------------------------------------- embedding-only proxy
def _bow(sentence: str):
    counts: dict[str, int] = {}
    for tok in sentence.lower().replace(".", " ").replace(",", " ").split():
        counts[tok] = counts.get(tok, 0) + 1
    return counts


def cosine_bow(a: str, b: str) -> float:
    """Bag-of-words cosine similarity -- a transparent stand-in for the
    'high embedding similarity' that a metric-based admissibility judge sees.
    Minimal single-field edits (negation, a number, before/after) keep this
    high, which is exactly why a similarity gate cannot protect meaning."""
    ca, cb = _bow(a), _bow(b)
    keys = set(ca) | set(cb)
    dot = sum(ca.get(k, 0) * cb.get(k, 0) for k in keys)
    na = math.sqrt(sum(v * v for v in ca.values()))
    nb = math.sqrt(sum(v * v for v in cb.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# ----------------------------------------------------------- fact generation
def sample_fact(rng: random.Random) -> ExtFact:
    return ExtFact(
        agent=rng.choice(AGENTS),
        patient=rng.choice(PATIENTS),
        quantity=rng.choice([1, 2, 3, 5]),
        polarity=rng.choice(["positive", "negative"]),
        time_dir=rng.choice(["previous", "following"]),
        modality=rng.choice(["asserted", "necessary", "possible"]),
        attribution=rng.choice(["none", "report", "vendor"]),
        causation=rng.choice(["none", "cause", "purpose"]),
    )


def altering_edit(f: ExtFact, field: str, rng: random.Random) -> ExtFact:
    """Return a copy of ``f`` with exactly one locked field changed to a near
    but semantically different value (a minimal meaning-altering edit)."""
    if field == "polarity":
        return replace(f, polarity="negative" if f.polarity == "positive"
                       else "positive")
    if field == "quantity":
        alt = rng.choice([q for q in [1, 2, 3, 5, 8] if q != f.quantity])
        return replace(f, quantity=alt)
    if field == "time_dir":
        return replace(f, time_dir="following" if f.time_dir == "previous"
                       else "previous")
    if field == "modality":
        return replace(f, modality="possible" if f.modality != "possible"
                       else "necessary")
    if field == "attribution":
        alt = rng.choice([a for a in ["none", "report", "vendor"]
                          if a != f.attribution])
        return replace(f, attribution=alt)
    if field == "causation":
        alt = rng.choice([c for c in ["none", "cause", "purpose"]
                          if c != f.causation])
        return replace(f, causation=alt)
    raise ValueError(f"unknown field {field!r}")


# --------------------------------------------------------------- experiment
def _percentile(sorted_vals, q: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = int(q / 100.0 * (len(sorted_vals) - 1))
    return sorted_vals[idx]


def run_challenge(n_docs: int = 200, sents_per_doc: int = 24,
                  msg_len: int = 8, tag_bits: int = 16,
                  benign_erase_prob: float = 0.25,
                  benign_false_reject_target: float = 0.05,
                  seed: int = 20270101, num_resamples: int = 2000) -> dict:
    """Run the field-level challenge set and return structured metrics.

    Design (all on real sentence strings, no fabricated numbers):

    * ``n_docs`` independent watermarked documents of ``sents_per_doc`` facts.
    * **Benign** transform: a meaning-preserving rewrite that canonicalizes a
      ``benign_erase_prob`` fraction of carriers (erasures), keeping every
      locked field. Typed attribution should be RETAINED (ECC + unchanged h_I).
    * **Tamper** probes: for each protected field, one random sentence per
      document gets a single-field meaning-altering edit. Typed attribution
      should FAIL (h_I changes -> MAC fails).
    * Three detectors, differing only in the admissibility rule:
        - ``typed``      : Truthprint (h_I-bound MAC).
        - ``no_mac``     : decode-only (ECC returns a candidate -> attribute).
        - ``embedding``  : no h_I binding; a bag-of-words cosine gate calibrated
                           so benign paraphrases are rejected at most
                           ``benign_false_reject_target``.

    The embedding gate is *calibrated to keep legitimate paraphrases*, then
    measured on tamper -- a fair, threshold-free-by-construction comparison.
    """
    from .stats import bootstrap_ci, wilson_ci

    rng = random.Random(seed)
    key = b"truthprint-challenge-key-01234567"[:32]
    code_n = 2 * sents_per_doc
    core = Truthprint(key, msg_len=msg_len, tag_bits=tag_bits,
                      code_n=code_n, code_seed=0xC0FFEE)

    # accumulators
    benign_retained = 0
    # cosine of a legitimate meaning-preserving paraphrase (voice+time reflow)
    benign_para_cos: list[float] = []
    tamper_cos = {f: [] for f in FIELDS}          # tamper surface cosine
    paired_benign_cos = {f: [] for f in FIELDS}   # benign cos of same sentence
    typed_detect = {f: 0 for f in FIELDS}         # tamper correctly rejected
    nomac_detect = {f: 0 for f in FIELDS}         # tamper rejected by decode-only

    for _ in range(n_docs):
        facts = [sample_fact(rng) for _ in range(sents_per_doc)]
        msg = [rng.randrange(2) for _ in range(msg_len)]
        nonce = bytes(rng.randrange(256) for _ in range(12))  # seeded => reproducible
        options = core.encode(doc_invariants(facts), msg, nonce)
        ref = [realize(f, options[2 * i], options[2 * i + 1])
               for i, f in enumerate(facts)]

        # ---- benign transform: canonicalize a fraction of carriers ----------
        mask = [False] * code_n
        for j in range(code_n):
            if rng.random() < benign_erase_prob:
                mask[j] = True
        # (locked fields untouched, so doc invariants are unchanged)
        benign_res = core.detect(doc_invariants(facts), options, nonce,
                                 erasure_mask=mask)
        benign_retained += 1 if benign_res.attributed else 0

        # legitimate paraphrase cosine per sentence (voice+time reflow)
        for i, f in enumerate(facts):
            v, t = options[2 * i], options[2 * i + 1]
            para = realize(f, 1 - v, 1 - t)
            benign_para_cos.append(cosine_bow(ref[i], para))

        # ---- tamper probes: one field, one random sentence per doc ----------
        for field in FIELDS:
            i = rng.randrange(sents_per_doc)
            f2 = altering_edit(facts[i], field, rng)
            tampered_surface = realize(f2, options[2 * i], options[2 * i + 1])
            tamper_cos[field].append(cosine_bow(ref[i], tampered_surface))
            # the same sentence's legitimate-paraphrase cosine, for pairing
            v, t = options[2 * i], options[2 * i + 1]
            paired_benign_cos[field].append(
                cosine_bow(ref[i], realize(facts[i], 1 - v, 1 - t)))
            # typed / no-mac detection: re-parse the tampered surface
            parsed = list(facts)
            parsed[i], _ = parse(tampered_surface)
            res = core.detect(doc_invariants(parsed), options, nonce)
            typed_detect[field] += 0 if res.attributed else 1
            nomac_detect[field] += 0 if res.decoded else 1

    # ---- calibrate the embedding gate to keep benign paraphrases -----------
    theta = _percentile(sorted(benign_para_cos),
                        100.0 * benign_false_reject_target)
    embed_false_reject = sum(1 for c in benign_para_cos if c < theta)

    per_field = {}
    inversion_hits = inversion_n = 0
    for field in FIELDS:
        n = len(tamper_cos[field])
        embed_detect = sum(1 for c in tamper_cos[field] if c < theta)
        # threshold-inversion: tamper looks at least as similar as the paired
        # legitimate paraphrase -> no cosine threshold can separate them.
        inv_hits = sum(1 for a, b in zip(tamper_cos[field],
                                         paired_benign_cos[field]) if a >= b)
        inversion_hits += inv_hits
        inversion_n += n
        per_field[field] = {
            "n": n,
            "typed_tamper_detect": wilson_ci(typed_detect[field], n),
            "nomac_tamper_detect": wilson_ci(nomac_detect[field], n),
            "embed_tamper_detect": wilson_ci(embed_detect, n),
            "mean_cosine_tamper": bootstrap_ci(tamper_cos[field], num_resamples),
            "threshold_inversion_rate": wilson_ci(inv_hits, n),
        }

    def _agg(metric_counts):
        num = sum(metric_counts[f] for f in FIELDS)
        den = sum(per_field[f]["n"] for f in FIELDS)
        return wilson_ci(num, den)

    embed_counts = {f: sum(1 for c in tamper_cos[f] if c < theta)
                    for f in FIELDS}
    return {
        "config": {"n_docs": n_docs, "sents_per_doc": sents_per_doc,
                   "msg_len": msg_len, "tag_bits": tag_bits,
                   "code_n": code_n, "benign_erase_prob": benign_erase_prob,
                   "benign_false_reject_target": benign_false_reject_target,
                   "seed": seed, "num_resamples": num_resamples},
        "embedding_theta": theta,
        "benign": {
            "typed_retention": wilson_ci(benign_retained, n_docs),
            "embed_false_reject": wilson_ci(embed_false_reject,
                                            len(benign_para_cos)),
            "mean_cosine_paraphrase": bootstrap_ci(benign_para_cos,
                                                   num_resamples),
        },
        "per_field": per_field,
        "aggregate": {
            "typed_tamper_detect": _agg(typed_detect),
            "nomac_tamper_detect": _agg(nomac_detect),
            "embed_tamper_detect": _agg(embed_counts),
            "threshold_inversion_rate": wilson_ci(inversion_hits, inversion_n),
        },
    }
