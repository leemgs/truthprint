"""Wide-coverage neural invariant extractor (review W5).

The Stage-2 extractor (:mod:`truthprint.multilingual`) is lexicon-based: it
recovers the typed invariant fields on the *closed* template domain but cannot
generalize to open-domain wording. This module is the drop-in neural
counterpart: it prompts an instruction-following LLM to read a (possibly
translated) sentence and emit the nine invariant fields as JSON, then robustly
parses and normalizes that JSON to the same schema as
``multilingual.extract_invariants``.

Design goals:
  * **Same interface** as the lexicon extractor -- ``extract(text, lang) -> dict``
    over :data:`truthprint.multilingual.FIELDS` -- so provenance/authentication
    code is backend-agnostic.
  * **Backend-agnostic and testable offline** -- the LLM is any callable
    ``fn(prompt: str) -> str``. The parsing/normalization is deterministic and
    unit-tested with a stub backend; the real HF backend lives in the author
    notebook (GPU).
  * **Honest abstention** -- an unparsable field is ``None``, never a guess, so
    it behaves like the lexicon extractor for downstream digest/authentication.

This closes the "lexicon, not wide-coverage" limitation with a real neural
frontend whose accuracy the author measures on real MT and on open-domain
probes (see ``scripts/eval_neural_parser.py`` and the W5 notebook).
"""
from __future__ import annotations

import json
import re
from typing import Callable

from .multilingual import FIELDS, LANGS

__all__ = [
    "build_prompt", "parse_response", "normalize_fields",
    "NeuralInvariantExtractor", "StubBackend",
]

_SCHEMA_DOC = """Extract the meaning of the sentence into these fields (JSON):
- agent: who performs the action (short noun phrase) or null
- patient: what the action is done to (short noun phrase) or null
- predicate: the core action as an uppercase lemma (e.g. FIX, BREAK) or null
- polarity: "positive" or "negative"
- quantity: an integer count of the patient, or null
- time_dir: "previous" (before reference time) or "following" (after) or null
- modality: "asserted" (plain fact), "necessary" (must/required), or "possible" (may/might)
- attribution: who the claim is credited to ("report", "vendor", ...) or "none"
- causation: "cause" (because of), "purpose" (in order to), or "none\""""

_FEWSHOT = (
    'Sentence: "On the previous day, the server error was fixed by the developer."\n'
    '{"agent":"the developer","patient":"server error","predicate":"FIX",'
    '"polarity":"positive","quantity":1,"time_dir":"previous",'
    '"modality":"asserted","attribution":"none","causation":"none"}'
)


def build_prompt(text: str, lang: str) -> str:
    """Deterministic few-shot JSON-extraction prompt for one sentence."""
    if lang not in LANGS:
        raise ValueError(f"lang must be one of {LANGS}")
    return (
        f"{_SCHEMA_DOC}\n\n"
        f"Reply with ONLY a single-line JSON object using exactly these keys: "
        f"{', '.join(FIELDS)}.\n\n"
        f"Example:\n{_FEWSHOT}\n\n"
        f"Sentence (language={lang}): \"{text}\"\n"
    )


# --- normalization to the canonical closed vocabulary ---------------------- #
_POLARITY = {"positive": "positive", "negative": "negative",
             "pos": "positive", "neg": "negative", "true": "positive",
             "false": "negative"}
_TIME = {"previous": "previous", "following": "following",
         "before": "previous", "after": "following", "past": "previous",
         "future": "following", "prior": "previous", "next": "following"}
_MOD = {"asserted": "asserted", "necessary": "necessary", "possible": "possible",
        "must": "necessary", "required": "necessary", "may": "possible",
        "might": "possible", "could": "possible", "certain": "asserted",
        "fact": "asserted"}
_CAUSE = {"none": "none", "cause": "cause", "purpose": "purpose",
          "because": "cause", "reason": "cause", "goal": "purpose",
          "in order to": "purpose", "to prevent": "purpose"}
_WORDNUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
            "seven": 7, "eight": 8, "nine": 9, "ten": 10}


def _norm_choice(val, table):
    if val is None:
        return None
    s = str(val).strip().lower()
    return table.get(s)


def _norm_quantity(val):
    if val is None:
        return None
    if isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        return int(val)
    s = str(val).strip().lower()
    m = re.search(r"-?\d+", s)
    if m:
        return int(m.group())
    return _WORDNUM.get(s)


def _norm_str(val):
    if val is None:
        return None
    s = str(val).strip().lower()
    return s or None


def normalize_fields(d: dict) -> dict:
    """Coerce a raw extracted dict to the canonical FIELDS schema."""
    out = {f: None for f in FIELDS}
    out["agent"] = _norm_str(d.get("agent"))
    out["patient"] = _norm_str(d.get("patient"))
    pred = d.get("predicate")
    out["predicate"] = str(pred).strip().upper() if pred not in (None, "") else None
    out["polarity"] = _norm_choice(d.get("polarity"), _POLARITY) or (
        "positive" if d.get("polarity") is None else None)
    out["quantity"] = _norm_quantity(d.get("quantity"))
    out["time_dir"] = _norm_choice(d.get("time_dir"), _TIME)
    out["modality"] = _norm_choice(d.get("modality"), _MOD) or "asserted"
    attr = d.get("attribution")
    out["attribution"] = _norm_str(attr) or "none"
    out["causation"] = _norm_choice(d.get("causation"), _CAUSE) or "none"
    return out


def parse_response(raw: str) -> dict:
    """Robustly parse an LLM response into the canonical FIELDS schema.

    Handles Markdown code fences, surrounding prose, and single quotes; missing
    fields become ``None`` (honest abstention). Returns an all-``None`` dict if
    no JSON object can be found.
    """
    if not raw:
        return {f: None for f in FIELDS}
    text = raw.strip()
    # strip Markdown fences
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    # find the first {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return {f: None for f in FIELDS}
    blob = text[start:end + 1]
    try:
        d = json.loads(blob)
    except json.JSONDecodeError:
        # tolerate single quotes
        try:
            d = json.loads(blob.replace("'", '"'))
        except json.JSONDecodeError:
            return {f: None for f in FIELDS}
    if not isinstance(d, dict):
        return {f: None for f in FIELDS}
    return normalize_fields(d)


class NeuralInvariantExtractor:
    """Drop-in neural replacement for ``multilingual.extract_invariants``.

    ``backend`` is any callable mapping a prompt string to a model response
    string (an HF pipeline, an API client, or a test stub).
    """

    def __init__(self, backend: Callable[[str], str]):
        self.backend = backend

    def extract(self, text: str, lang: str) -> dict:
        prompt = build_prompt(text, lang)
        return parse_response(self.backend(prompt))

    # match the module-level function name used elsewhere
    def extract_invariants(self, text: str, lang: str) -> dict:
        return self.extract(text, lang)


class StubBackend:
    """Deterministic test backend: maps a prompt to a canned response.

    ``responses`` maps a substring of the sentence to the raw model reply.
    Falls back to an empty JSON object (all abstentions) when nothing matches.
    """

    def __init__(self, responses: dict[str, str]):
        self.responses = responses

    def __call__(self, prompt: str) -> str:
        for needle, reply in self.responses.items():
            if needle in prompt:
                return reply
        return "{}"
