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
    "NeuralInvariantExtractor", "StubBackend", "APIBackend", "SeparatedPipeline",
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


# Map a predicate surface form (any inflection) to its canonical uppercase lemma,
# so an extractor that returns "fixed"/"raises" compares fairly against gold "FIX"/
# "RAISE". Matched by stem prefix; unknown predicates fall back to uppercase.
_PREDICATE_STEMS = {
    "fix": "FIX", "broke": "BREAK", "break": "BREAK", "broken": "BREAK",
    "rais": "RAISE", "reduc": "REDUCE", "clos": "CLOSE", "detect": "DETECT",
    "overturn": "OVERTURN", "patch": "PATCH",
}


def _norm_predicate(pred):
    if pred in (None, ""):
        return None
    s = str(pred).strip().lower()
    for stem, lemma in _PREDICATE_STEMS.items():
        if s.startswith(stem):
            return lemma
    return str(pred).strip().upper()


def normalize_fields(d: dict) -> dict:
    """Coerce a raw extracted dict to the canonical FIELDS schema."""
    out = {f: None for f in FIELDS}
    out["agent"] = _norm_str(d.get("agent"))
    out["patient"] = _norm_str(d.get("patient"))
    out["predicate"] = _norm_predicate(d.get("predicate"))
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


class APIBackend:
    """OpenAI-compatible chat-completions backend (no GPU, no local weights).

    Works with any OpenAI-compatible endpoint, including free providers:
    OpenRouter (``https://openrouter.ai/api/v1``), Groq
    (``https://api.groq.com/openai/v1``), Google Gemini's OpenAI-compat endpoint,
    Together, or a local Ollama (``http://localhost:11434/v1``). The neural
    invariant parser is a structured-extraction task, so an API model is a valid
    substitute for a local model---where the model runs does not affect the
    result, only extraction accuracy does.

    ``api_key`` falls back to the ``TRUTHPRINT_API_KEY`` environment variable.
    Uses only the standard library (``urllib``), so it adds no dependency.
    """

    def __init__(self, model: str, base_url: str, api_key: str | None = None,
                 system: str = "You extract structured meaning as compact JSON.",
                 timeout: int = 60, max_tokens: int = 200, retries: int = 2):
        import os
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("TRUTHPRINT_API_KEY")
        self.system = system
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.retries = retries

    def _post(self, url: str, data: dict, headers: dict) -> dict:
        """HTTP POST returning parsed JSON. Overridden in tests."""
        import urllib.request
        req = urllib.request.Request(
            url, data=json.dumps(data).encode("utf-8"), headers=headers,
            method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode("utf-8"))

    def __call__(self, prompt: str) -> str:
        url = self.base_url + "/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "max_tokens": self.max_tokens,
        }
        last = None
        for _ in range(max(1, self.retries)):
            try:
                resp = self._post(url, data, headers)
                return resp["choices"][0]["message"]["content"]
            except Exception as e:  # noqa: BLE001 - network/parse errors are retryable
                last = e
        raise RuntimeError(f"APIBackend call failed after {self.retries} tries: {last}")


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


class SeparatedPipeline:
    """Enforce *separate* translation and extraction models (review W5 / Task 1).

    The first neural pilot let one model both translate a sentence and extract
    invariants from its own output, a self-consistency confound. This wrapper
    makes model separation a checked contract: the translation backend and the
    extraction backend must be distinct model identifiers, or construction fails.
    The GPU handoff notebook instantiates this with two different models (e.g. one
    system for ``translate`` and a different instruction model for ``extract``),
    so the reported neural numbers are unconfounded.

    ``translate_backend`` maps ``(text, target_lang) -> translated_text``;
    ``extractor`` is a :class:`NeuralInvariantExtractor` over the *other* model.
    """

    def __init__(self, translate_backend: Callable[[str, str], str],
                 translate_model_id: str,
                 extractor: "NeuralInvariantExtractor",
                 extract_model_id: str):
        if translate_model_id == extract_model_id:
            raise ValueError(
                "translation and extraction must use different models "
                f"(both were {translate_model_id!r}); this is the self-"
                "consistency confound W5 asks to remove.")
        self.translate_backend = translate_backend
        self.translate_model_id = translate_model_id
        self.extractor = extractor
        self.extract_model_id = extract_model_id

    def run(self, text: str, target_lang: str) -> dict:
        """Translate with one model, extract invariants with a different one."""
        translated = self.translate_backend(text, target_lang)
        fields = self.extractor.extract(translated, target_lang)
        return {"translated": translated, "fields": fields,
                "translate_model": self.translate_model_id,
                "extract_model": self.extract_model_id}
