"""Paraphrase and adaptive-attack transforms on real sentence strings.

The paper's motivation is robustness to *meaning-preserving transformation*, and
the manuscript names paraphrasing explicitly (Threat Model, Eq. ``validremoval``,
RQ4/RQ7, hypotheses H1--H6). The measured evidence so far, however, is all *real
machine translation* (NLLB); **translation is not paraphrase**. This module adds
the missing axis: it rewrites the closed-domain watermarked sentence with
paraphrase operators that keep the locked invariants fixed, and with a
*schema-aware adaptive attacker* (RQ7) that deliberately swaps the content words
the extractor keys on for out-of-lexicon synonyms while preserving meaning.

It is deliberately self-contained, seeded, and standard-library only --- the same
discipline as :mod:`truthprint.challenge` and :mod:`truthprint.semantic_fp` --- so
the numbers are reproducible in CI and fully auditable, rather than depending on a
hosted paraphraser. An optional LLM paraphraser (any callable
``fn(text) -> paraphrase``, e.g. :class:`truthprint.neural_parser.APIBackend`)
can be plugged in for scale, exactly as the neural frontend is.

Design (all on real English strings, no fabricated numbers):

  * A **benign** paraphrase keeps every locked field and uses *in-lexicon* content
    words (voice flip, time-position reflow, verb/time synonyms the Stage-2
    extractor knows, a discourse hedge). Meaning-based provenance authentication
    (:mod:`truthprint.provenance`) SHOULD survive --- this is RQ4.
  * An **adaptive** paraphrase (RQ7) keeps every locked field but replaces the
    predicate verb and the time expression with *out-of-lexicon* synonyms an
    attacker who knows the schema would choose ("took care of" for "fixed",
    "24 hours earlier" for "the previous day"). Meaning is preserved (an oracle
    judges the gold contract unchanged), so any authentication failure here is a
    ``ValidRemoval`` in the sense of Eq. ``validremoval``.
  * An **altering** edit changes one locked field (via
    :func:`truthprint.challenge.altering_edit`); authentication SHOULD fail, and
    because meaning changed it does *not* count as a ``ValidRemoval``.

The honest result the harness measures is that benign paraphrase is authenticated
at high rates while the adaptive attacker's residual success is bounded by the
*closed lexicon's coverage* --- not by the meaning-digest principle --- which is
exactly what the wide-coverage neural frontend (:mod:`truthprint.neural_parser`)
is meant to close. Surface carriers (the Stage-1 parser) die under any
content-word paraphrase, the paraphrase counterpart of the ``0/192`` translation
negative.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, replace
from typing import Callable

from .challenge import ExtFact, ext_invariants, altering_edit, cosine_bow

__all__ = [
    "VerbForms", "BENIGN_VERBS", "ADAPTIVE_VERBS",
    "BENIGN_TIME", "ADAPTIVE_TIME", "OPERATORS", "ADAPTIVE_OPS", "BENIGN_OPS",
    "realize_surface", "paraphrase_variants", "invariant_eq_gold",
]


# --------------------------------------------------------------------------- #
# Lexical inventories. Each verb is (past, participle, base). "Benign" forms are
# recognized by the Stage-2 extractor's _FIX lexicon (fix/correct/modif/resolv/
# repair/set up/address); "adaptive" forms are meaning-preserving synonyms of
# "fix" that are deliberately *outside* that lexicon, so a schema-aware attacker
# can strip the marker without changing meaning.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class VerbForms:
    past: str
    participle: str
    base: str


BENIGN_VERBS = [
    VerbForms("fixed", "fixed", "fix"),
    VerbForms("repaired", "repaired", "repair"),
    VerbForms("resolved", "resolved", "resolve"),
    VerbForms("corrected", "corrected", "correct"),
    VerbForms("addressed", "addressed", "address"),
]
ADAPTIVE_VERBS = [
    VerbForms("took care of", "taken care of", "take care of"),
    VerbForms("sorted out", "sorted out", "sort out"),
    VerbForms("dealt with", "dealt with", "deal with"),
    VerbForms("cleared up", "cleared up", "clear up"),
    VerbForms("straightened out", "straightened out", "straighten out"),
]

# Time expressions per direction. Benign forms hit the extractor's _TIME lexicon;
# adaptive forms carry the same before/after meaning without any lexicon marker.
BENIGN_TIME = {
    "previous": ["the previous day", "the day before", "the prior day",
                 "the preceding day"],
    "following": ["the following day", "the next day", "the day after"],
}
# NB: these must contain NO _TIME lexicon marker (e.g. avoid "day before" /
# "day after" substrings), so the schema-aware attacker genuinely strips the
# time marker while keeping the before/after meaning. Checked in tests.
ADAPTIVE_TIME = {
    "previous": ["24 hours earlier", "one day earlier", "a day ago"],
    "following": ["24 hours later", "one day later", "a day from then"],
}

# Attribution prefixes. Benign forms contain a lexicon marker (report/vendor);
# adaptive forms refer to the same source without one.
_BENIGN_ATTR = {
    "none": [""],
    "report": ["according to the report, ", "the report states that "],
    "vendor": ["according to the vendor, ", "the vendor states that "],
}
_ADAPTIVE_ATTR = {
    "none": [""],
    "report": ["as the write-up put it, ", "per the internal memo, "],
    "vendor": ["as the merchant's memo said, ", "per the outside firm, "],
}
_CAUSE_TAIL = {"none": "", "cause": " because of the outage",
               "purpose": " to prevent the outage"}

# discourse hedges that carry no invariant marker (checked in tests).
_HEDGES = ["Notably, ", "In fact, ", "As documented, "]


# --------------------------------------------------------------------------- #
# Realization. Generalizes challenge.realize to an arbitrary predicate verb and
# free-form time / attribution surface, keeping the same finite auxiliary grammar
# for polarity x modality x voice so negation/modality markers stay in-lexicon
# (an attacker rewrites content words, not the function-word scaffolding).
# --------------------------------------------------------------------------- #
def _patient_phrase(f: ExtFact) -> str:
    return f"the {f.patient}" if f.quantity == 1 else f"{f.quantity} {f.patient}s"


def _active_vp(v: VerbForms, pol: str, mod: str, pp: str) -> str:
    if mod == "asserted":
        return f"{v.past} {pp}" if pol == "positive" else f"did not {v.base} {pp}"
    aux = "must have" if mod == "necessary" else "may have"
    neg = "" if pol == "positive" else "not "
    aux = aux.replace("have", f"{neg}have") if neg else aux
    return f"{aux} {v.participle} {pp}"


def _passive_vp(v: VerbForms, pol: str, mod: str, pp: str, agent: str) -> str:
    if mod == "asserted":
        core = f"was {v.participle}" if pol == "positive" else f"was not {v.participle}"
    else:
        aux = "must have been" if mod == "necessary" else "may have been"
        if pol == "negative":
            aux = aux.replace("have", "not have")
        core = f"{aux} {v.participle}"
    return f"{pp} {core} by {agent}"


def realize_surface(f: ExtFact, verb: VerbForms, voice_bit: int,
                    timepos_bit: int, time_phrase: str, attr_prefix: str,
                    hedge: str = "") -> str:
    """Render a fact to an English sentence with explicit lexical choices.

    ``voice_bit`` 0=active/1=passive, ``timepos_bit`` 0=front/1=end. The locked
    fields of ``f`` (polarity, modality, quantity, attribution, causation, agent,
    patient, time direction) are all preserved; only the *surface* changes.
    """
    pp = _patient_phrase(f)
    cause = _CAUSE_TAIL[f.causation]
    if voice_bit == 0:
        core = f"{f.agent} {_active_vp(verb, f.polarity, f.modality, pp)}{cause}"
    else:
        core = f"{_passive_vp(verb, f.polarity, f.modality, pp, f.agent)}{cause}"
    if timepos_bit == 0:
        body = f"{attr_prefix}on {time_phrase}, {core}"
    else:
        body = f"{attr_prefix}{core} on {time_phrase}"
    body = body[0].upper() + body[1:] + "."
    if hedge:
        body = hedge + body[0].lower() + body[1:]
    return body


# --------------------------------------------------------------------------- #
# Operators. Each returns the paraphrased text for one fact given the reference
# carrier bits. Benign ops preserve meaning with in-lexicon content; adaptive ops
# preserve meaning with out-of-lexicon content; the altering op changes meaning.
# --------------------------------------------------------------------------- #
BENIGN_OPS = ["voice", "time_reflow", "verb_syn", "time_syn", "hedge",
              "combo_benign"]
ADAPTIVE_OPS = ["adv_verb", "adv_time", "adv_combo"]
OPERATORS = BENIGN_OPS + ADAPTIVE_OPS + ["alter"]


def _pick(rng: random.Random, seq):
    return seq[rng.randrange(len(seq))]


def paraphrase_variants(f: ExtFact, voice_bit: int, timepos_bit: int,
                        rng: random.Random) -> list[dict]:
    """All operator outputs for one fact. Returns a list of dicts with keys
    ``op``, ``mode`` (benign/adaptive/altering), ``text``, and ``gold`` (the
    ExtFact whose contract the transformed sentence should reproduce)."""
    benign_verb = _pick(rng, BENIGN_VERBS)
    adv_verb = _pick(rng, ADAPTIVE_VERBS)
    b_time = _pick(rng, BENIGN_TIME[f.time_dir])
    a_time = _pick(rng, ADAPTIVE_TIME[f.time_dir])
    b_attr = _pick(rng, _BENIGN_ATTR[f.attribution])
    a_attr = _pick(rng, _ADAPTIVE_ATTR[f.attribution])
    ref_time = _pick(rng, BENIGN_TIME[f.time_dir])

    def s(fact, verb, vb, tb, tphrase, attr, hedge=""):
        return realize_surface(fact, verb, vb, tb, tphrase, attr, hedge)

    out = []
    # ---- benign (meaning-preserving, in-lexicon) -------------------------- #
    out.append({"op": "voice", "mode": "benign", "gold": f,
                "text": s(f, benign_verb, 1 - voice_bit, timepos_bit, ref_time, b_attr)})
    out.append({"op": "time_reflow", "mode": "benign", "gold": f,
                "text": s(f, benign_verb, voice_bit, 1 - timepos_bit, ref_time, b_attr)})
    out.append({"op": "verb_syn", "mode": "benign", "gold": f,
                "text": s(f, benign_verb, voice_bit, timepos_bit, ref_time, b_attr)})
    out.append({"op": "time_syn", "mode": "benign", "gold": f,
                "text": s(f, benign_verb, voice_bit, timepos_bit, b_time, b_attr)})
    hedge = _pick(rng, _HEDGES) if f.attribution == "none" else ""
    out.append({"op": "hedge", "mode": "benign", "gold": f,
                "text": s(f, benign_verb, voice_bit, timepos_bit, ref_time, b_attr, hedge)})
    out.append({"op": "combo_benign", "mode": "benign", "gold": f,
                "text": s(f, benign_verb, 1 - voice_bit, 1 - timepos_bit, b_time, b_attr)})
    # ---- adaptive (meaning-preserving, out-of-lexicon; RQ7) --------------- #
    out.append({"op": "adv_verb", "mode": "adaptive", "gold": f,
                "text": s(f, adv_verb, voice_bit, timepos_bit, ref_time, b_attr)})
    out.append({"op": "adv_time", "mode": "adaptive", "gold": f,
                "text": s(f, benign_verb, voice_bit, timepos_bit, a_time, b_attr)})
    out.append({"op": "adv_combo", "mode": "adaptive", "gold": f,
                "text": s(f, adv_verb, 1 - voice_bit, timepos_bit, a_time, a_attr)})
    # ---- altering (meaning-changing control; NOT a valid removal) --------- #
    field = _pick(rng, ["polarity", "time_dir", "attribution", "quantity"])
    f2 = altering_edit(f, field, rng)
    out.append({"op": "alter", "mode": "altering", "gold": f2, "altered_field": field,
                "text": s(f2, benign_verb, voice_bit, timepos_bit,
                          _pick(rng, BENIGN_TIME[f2.time_dir]),
                          _pick(rng, _BENIGN_ATTR[f2.attribution]))})
    return out


def invariant_eq_gold(a: ExtFact, b: ExtFact, fields: list[str]) -> bool:
    """Oracle InvariantEq over a contract's fields: did the transform preserve the
    locked meaning? Uses the ground-truth ExtFacts, not the noisy extractor, so
    'meaning preserved' in ValidRemoval is a fact about the transform, not about
    detection."""
    ia, ib = ext_invariants(a), ext_invariants(b)
    return all(ia.get(k) == ib.get(k) for k in fields)


def apply_llm_paraphraser(text: str, paraphraser: Callable[[str], str]) -> str:
    """Optional hook: route a sentence through an external LLM paraphraser.

    ``paraphraser`` is any ``fn(text) -> paraphrase`` (e.g. an OpenAI-compatible
    client). Kept trivial so the offline operators remain the reproducible
    default and the API path is opt-in, mirroring the neural frontend.
    """
    return paraphraser(text)
