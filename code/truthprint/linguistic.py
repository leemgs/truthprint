"""Closed-domain linguistic layer: realize/parse the watermark on real strings.

This is the Stage-1, closed-domain instantiation from the paper. Each factual
sentence exposes two invariant-preserving carriers:

    carrier 0: VOICE          in {active, passive}
    carrier 1: TIME_POSITION  in {front, end}

Both change realization only, never the locked fact (agent, predicate, patient,
time, polarity). The layer wraps :class:`truthprint.core.Truthprint`, mapping
its abstract carrier options to and from English sentences. It is intentionally
small and rule-based so the full pipeline can be tested end to end without a
wide-coverage semantic parser; extend :func:`realize`/:func:`parse` to add
carriers or domains.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass

from .core import Truthprint, DetectionResult
from .invariants import canonical_digest

__all__ = ["Fact", "realize", "parse", "doc_invariants",
           "invariant_preserving_transform", "negate_transform",
           "LinguisticCodec"]

_VERB = "fixed"
_TIME = "the previous day"


@dataclass(frozen=True)
class Fact:
    agent: str
    patient: str
    polarity: str = "positive"  # "positive" | "negative"


def _fact_invariants(f: Fact) -> dict:
    return {"agent": f.agent, "patient": f.patient, "predicate": "FIX",
            "polarity": f.polarity, "time": "previous_day"}


def doc_invariants(facts: list[Fact]) -> dict:
    """Canonical document-level invariant set over all facts."""
    return {"facts": [_fact_invariants(f) for f in facts]}


# --------------------------------------------------------------- realization
def realize(fact: Fact, voice_bit: int, timepos_bit: int) -> str:
    a, p = fact.agent, fact.patient
    neg = fact.polarity == "negative"
    if voice_bit == 0:  # active
        core = f"{a} did not fix {p}" if neg else f"{a} {_VERB} {p}"
    else:               # passive
        core = f"{p} was not {_VERB} by {a}" if neg else f"{p} was {_VERB} by {a}"
    if timepos_bit == 0:  # time at front
        s = f"On {_TIME}, {core}."
    else:                 # time at end
        s = f"{core[0].upper() + core[1:]} on {_TIME}."
    return s[0].upper() + s[1:]


# ---------------------------------------------------------------------- parse
def parse(sentence: str):
    """Return (invariants_dict, {local_carrier_id: (bit, reliable)})."""
    s = sentence.strip().rstrip(".")
    low = s.lower()
    neg = ("did not" in low) or ("was not" in low)
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
    invariants = {"agent": agent, "patient": patient, "predicate": "FIX",
                  "polarity": "negative" if neg else "positive",
                  "time": "previous_day"}
    return invariants, {0: (voice, True), 1: (timepos, True)}


# ------------------------------------------------------------------ transforms
def invariant_preserving_transform(sentence: str, rng: random.Random,
                                   erase_prob: float):
    """Rewrite preserving invariants; may canonicalize a carrier (= erasure).

    Returns (new_sentence, {local_carrier_id: reliable_bool}).
    """
    inv, carriers = parse(sentence)
    v, t = carriers[0][0], carriers[1][0]
    reliable = {0: True, 1: True}
    if rng.random() < erase_prob:
        v = 0
        reliable[0] = False   # normalized to active -> voice carrier erased
    if rng.random() < erase_prob:
        t = 1
        reliable[1] = False   # normalized to end -> time carrier erased
    fact = Fact(agent=inv["agent"], patient=inv["patient"],
                polarity=inv["polarity"])
    return realize(fact, v, t), reliable


def negate_transform(sentence: str) -> str:
    """A meaning-ALTERING rewrite: flip polarity (tamper)."""
    inv, carriers = parse(sentence)
    fact = Fact(agent=inv["agent"], patient=inv["patient"],
                polarity="negative" if inv["polarity"] == "positive"
                else "positive")
    return realize(fact, carriers[0][0], carriers[1][0])


# ------------------------------------------------------------------- codec
class LinguisticCodec:
    """Encode/detect an authenticated payload across factual sentences."""

    def __init__(self, key: bytes, n_sentences: int, msg_len: int = 12,
                 tag_bits: int = 20, code_seed: int = 0xC0FFEE):
        self.n_sentences = n_sentences
        self.core = Truthprint(key, msg_len=msg_len, tag_bits=tag_bits,
                               code_n=2 * n_sentences, code_seed=code_seed)

    def encode(self, facts: list[Fact], msg_bits: list[int],
               nonce: bytes) -> list[str]:
        if len(facts) != self.n_sentences:
            raise ValueError("number of facts must equal n_sentences")
        options = self.core.encode(doc_invariants(facts), msg_bits, nonce)
        return [realize(f, options[2 * i], options[2 * i + 1])
                for i, f in enumerate(facts)]

    def detect(self, sentences: list[str], nonce: bytes,
               reliability: list[dict] | None = None) -> DetectionResult:
        """Detect from (possibly transformed) sentences.

        ``reliability[i]`` optionally marks per-sentence carriers as unreliable
        (erasures); if omitted every carrier is treated as reliable.
        """
        parsed_facts: list[Fact] = []
        options = [0] * (2 * len(sentences))
        mask = [False] * (2 * len(sentences))
        for i, s in enumerate(sentences):
            inv, carriers = parse(s)
            parsed_facts.append(Fact(agent=inv["agent"], patient=inv["patient"],
                                     polarity=inv["polarity"]))
            options[2 * i] = carriers[0][0]
            options[2 * i + 1] = carriers[1][0]
            if reliability is not None:
                mask[2 * i] = not reliability[i].get(0, True)
                mask[2 * i + 1] = not reliability[i].get(1, True)
        return self.core.detect(doc_invariants(parsed_facts), options, nonce,
                                erasure_mask=mask)
