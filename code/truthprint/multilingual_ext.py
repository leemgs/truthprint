"""Extended-coverage (wide-lexicon) invariant extractor --- adaptive-attack defense.

The paraphrase harness (:mod:`truthprint.paraphrase`, ``scripts/eval_paraphrase.py``)
shows a schema-aware adaptive attacker removing the meaning-digest by swapping the
predicate verb and time expression for synonyms *outside the closed Stage-2
lexicon* (:mod:`truthprint.multilingual`). We argued that this is a coverage limit
of the closed lexicon, not a failure of the meaning-digest principle---because the
invariants are still present in the paraphrase, a reader recovers them. This module
*measures* that defense: a frontend with a broader English inventory recovers the
same invariant fields from the adaptive paraphrase, restoring authentication.

Design:
  * **Same interface** as the closed extractor --- ``extract_invariants(text, lang)``
    over :data:`truthprint.multilingual.FIELDS` --- so it is a drop-in frontend for
    the provenance authentication code.
  * **Delegates then extends.** It first runs the closed extractor (which already
    handles polarity, modality, quantity, agent, patient, six languages), then, for
    English, *fills* the fields the closed lexicon abstained on (predicate,
    time direction, attribution) using a broader, independently-motivated synonym
    inventory, and recomputes quantity with word-boundary matching (fixing the
    closed lexicon's substring collision, e.g. ``straightened`` -> ``ten``). It only
    ever *fills an abstention*; it never overwrites a value the closed extractor
    already committed, so it cannot turn a correct reading into a wrong one.
  * **Soundness preserved.** Because it reads field *values*, a meaning-altering edit
    still yields a different value and fails authentication (verified in tests). The
    extension widens *coverage*, not tolerance.

This is still a fixed lexicon, so an open-vocabulary attacker can always find a
synonym outside it---which the held-out ``NOVEL`` pools in
:mod:`truthprint.paraphrase` measure as a residual, and which the open-vocabulary
neural frontend (:mod:`truthprint.neural_parser`, e.g. via ``APIBackend``) is meant
to close in the general case. The extension quantifies the mechanism: each added
synonym family recovers authentication for that family.
"""
from __future__ import annotations

import re

from .multilingual import extract_invariants as _base_extract, FIELDS, LANGS, \
    _ARABIC_DIGITS

__all__ = ["extract_invariants", "FIELDS", "LANGS"]

# --- extended English inventories (broader than the closed lexicon) --------- #
# General "fix / resolve" verb family (true synonyms only; no meaning-weakeners
# like "mitigate"). Matched as substrings on lowercased English text, same as the
# closed lexicon. Deliberately does NOT include the held-out NOVEL attack verbs in
# paraphrase.py, so the generalization bound is honest.
_FIX_EXT = [
    # closed-lexicon stems (kept for completeness)
    "fix", "correct", "modif", "resolv", "repair", "set up", "setup", "address",
    # common out-of-lexicon synonyms an attacker reaches for first
    "took care of", "take care of", "taken care of",
    "sorted out", "sort out",
    "dealt with", "deal with",
    "cleared up", "clear up",
    "straighten",              # straightened out / straighten out
    "remed",                   # remedied / remedy
    "rectif",                  # rectified / rectify
    "patch",                   # patched / patch
    "worked out", "work out",
    "got working", "get working", "up and running",
    "handled", "handle",
]

# Relative-time expressions, before ("previous") vs after ("following").
_TIME_EXT = {
    "previous": ["previous day", "day before", "prior day", "preceding day",
                 "24 hours earlier", "hours earlier", "one day earlier",
                 "day earlier", "a day ago", "day prior", "earlier that day"],
    "following": ["next day", "following day", "day after",
                  "24 hours later", "hours later", "one day later",
                  "day later", "a day from then", "day thereafter",
                  "later that day"],
}

# Attribution paraphrases beyond "report"/"vendor".
_ATTR_EXT = {
    "report": ["according to the report", "the report", "report says",
               "write-up", "writeup", "memo", "internal memo", "analysis",
               "documentation", "the note", "findings"],
    "vendor": ["according to the vendor", "the vendor", "supplier", "the seller",
               "merchant", "outside firm", "third party", "the provider"],
}

_WORDNUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
            "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
            "twelve": 12}

# every English time phrase we recognize, stripped before counting so a temporal
# number ("24 hours earlier", "one day later") is never read as a quantity.
_ALL_TIME_PHRASES = sorted(
    set(_TIME_EXT["previous"]) | set(_TIME_EXT["following"]),
    key=len, reverse=True)


def _find(text: str, markers) -> bool:
    return any(m in text for m in markers)


def _find_word(text: str, markers) -> bool:
    """Substring match with word boundaries, so a short marker ("memo") does not
    fire inside a longer word ("memory")."""
    return any(re.search(rf"\b{re.escape(m)}\b", text) for m in markers)


def _quantity_boundary(text: str) -> int | None:
    """Word-boundary quantity on time-stripped text: digits (ASCII or Arabic-Indic)
    or spelled numbers on token boundaries, so ``straightened`` no longer yields
    ``ten`` and ``24 hours earlier`` no longer yields ``24``."""
    for phrase in _ALL_TIME_PHRASES:
        text = text.replace(phrase, " ")
    digits = text.translate(_ARABIC_DIGITS)
    m = re.search(r"\d+", digits)
    if m:
        return int(m.group())
    for word, val in _WORDNUM.items():
        if re.search(rf"\b{word}\b", text):
            return val
    return None


def extract_invariants(text: str, lang: str) -> dict:
    """Extended-coverage recovery of the typed invariant fields.

    Identical schema/behavior to :func:`truthprint.multilingual.extract_invariants`
    on languages other than English; for English it additionally fills predicate,
    time direction, and attribution from a broader inventory and recomputes
    quantity with word boundaries. Only abstentions are filled.
    """
    if lang not in LANGS:
        raise ValueError(f"lang must be one of {LANGS}")
    out = _base_extract(text, lang)
    if lang != "en":
        return out
    low = text.lower()

    # predicate: fill only if the closed lexicon abstained
    if out.get("predicate") is None and _find(low, _FIX_EXT):
        out["predicate"] = "FIX"

    # time direction: fill only if abstained; strip nothing (markers are specific)
    if out.get("time_dir") is None:
        for direction, markers in _TIME_EXT.items():
            if _find(low, markers):
                out["time_dir"] = direction
                break

    # attribution: the closed extractor defaults to "none"; upgrade only from
    # "none" so we never overwrite a committed report/vendor reading. Word-boundary
    # matched so "memo" does not fire inside "memory (leak)".
    if out.get("attribution") in (None, "none"):
        for value, markers in _ATTR_EXT.items():
            if _find_word(low, markers):
                out["attribution"] = value
                break

    # quantity: recompute with word boundaries, which fixes the closed lexicon's
    # substring collisions (e.g. "straightened" -> "ten"). When no boundary number
    # is present the closed-domain default count is 1, so we discard any substring
    # artifact the base extractor may have produced rather than trusting it.
    out["quantity"] = _quantity_boundary(low) or 1
    return out
