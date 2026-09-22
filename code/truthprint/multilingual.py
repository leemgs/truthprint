"""Stage-2 multilingual invariant extractor (semantic frontend).

The Stage-1 frontend (:mod:`truthprint.linguistic`, :mod:`truthprint.challenge`)
only parses the exact English template it generated, so it cannot read real
machine-translation output (Section ``sec:realmt``: 0/192 parse coverage). This
module is a first, honest step toward the wide-coverage semantic frontend the
paper defers to future work: a **closed-domain, lexicon-based extractor** that
reads a sentence in English, Korean, or Hindi and recovers the *typed invariant
fields* (the meaning layer), independent of surface realization.

It is deliberately rule/lexicon-based (standard-library only, no model, no
network) so it runs anywhere and is fully auditable. Its purpose is to test the
paper's central hypothesis on **real** MT output: meaning-layer fields
(polarity, quantity, temporal direction, attribution, causation, modality)
survive translation and are recoverable, whereas surface carriers do not. It is
not a wide-coverage parser; entities that a translator renders inconsistently
(e.g. "config drift") are expected to be recovered less reliably, and those
honest misses are part of the measured result.

Lexicons are grounded in standard dictionary renderings of the closed-domain
vocabulary, not tuned to any particular MT system's output.
"""
from __future__ import annotations

import re

__all__ = ["extract_invariants", "FIELDS", "LANGS"]

FIELDS = ["agent", "patient", "predicate", "polarity", "quantity",
          "time_dir", "modality", "attribution", "causation"]
LANGS = ["en", "ko", "hi"]

# --- lexicons: field value -> {lang: [surface markers]} --------------------- #
_AGENT = {
    "the developer": {"en": ["developer"], "ko": ["개발자"], "hi": ["डेवलपर"]},
    "the engineer":  {"en": ["engineer"], "ko": ["엔지니어"], "hi": ["इंजीनियर"]},
    "the operator":  {"en": ["operator"], "ko": ["운영자"], "hi": ["ऑपरेटर", "संचालक"]},
    "the analyst":   {"en": ["analyst"], "ko": ["분석가"], "hi": ["विश्लेषक"]},
}
_PATIENT = {
    "server error": {"en": ["server error", "server bug"], "ko": ["서버 오류", "서버 에러"],
                     "hi": ["सर्वर त्रुटि", "सर्वर एरर"]},
    "memory leak":  {"en": ["memory leak"], "ko": ["메모리 누출", "메모리 누수", "메모리 유출"],
                     "hi": ["मेमोरी लीक"]},
    "config drift": {"en": ["config", "configuration"], "ko": ["구성", "구성 드리프트", "컨피그"],
                     "hi": ["कॉन्फ़िग", "कॉन्फ़िगरेशन", "विन्यास"]},
    "cache miss":   {"en": ["cache"], "ko": ["캐시"], "hi": ["कैश"]},
}
_NEG = {"en": [" not ", "n't", "never", "should not", "not fix"],
        "ko": ["않", "없", "안 "],
        "hi": ["नहीं", "मत "]}
_FIX = {"en": ["fix", "correct", "modif", "resolv", "repair", "set up", "setup",
               "address"],
        "ko": ["수정", "고정", "설정", "정정", "해결", "복구"],
        "hi": ["ठीक", "तय", "सुधार", "हल", "समाधान"]}
_TIME = {
    "following": {"en": ["next day", "following day", "day after"],
                  "ko": ["다음 날", "다음날", "이튿날"],
                  "hi": ["अगले दिन", "अगला दिन"]},
    "previous":  {"en": ["previous day", "day before", "prior day", "preceding day"],
                  "ko": ["전날", "이전 날", "지난날", "전 날"],
                  "hi": ["पिछले दिन", "पिछला दिन", "एक दिन पहले"]},
}
_MOD_POSSIBLE = {"en": ["may ", "might", "could", "can be", "possibly", "perhaps"],
                 "ko": ["수 있", "수도 있", "지도 모"],
                 "hi": ["सकत", "शायद"]}
_MOD_NECESSARY = {"en": ["must", "should", "has to", "have to", "need to",
                         "ought to", "required"],
                  "ko": ["해야", "않아야", "야 합니다", "야 한다", "필요", "해야 합니다"],
                  "hi": ["चाहिए", "करना होगा", "करना पड़", "आवश्यक", "ज़रूरी"]}
_ATTR = {
    "report": {"en": ["according to the report", "the report", "report says",
                      "per the report"],
               "ko": ["보고서에 따르면", "보고서에", "보고서"],
               "hi": ["रिपोर्ट के अनुसार", "रिपोर्ट के मुताबिक", "रिपोर्ट"]},
    "vendor": {"en": ["according to the vendor", "the vendor", "vendor says",
                      "according to the seller", "the seller", "supplier"],
               "ko": ["판매자", "공급업체", "공급자", "벤더", "판매업체"],
               "hi": ["विक्रेता के अनुसार", "विक्रेता", "आपूर्तिकर्ता", "वेंडर"]},
}
_CAUSE = {
    "purpose": {"en": ["to prevent", "to avoid", "in order to", "so as to",
                       "to stop"],
                "ko": ["방지하기 위해", "막기 위해", "위해", "위하여"],
                "hi": ["रोकने के लिए", "बचने के लिए", "के लिए"]},
    "cause":   {"en": ["because", "due to", "owing to", "as a result of",
                       "caused by"],
                "ko": ["때문", "로 인해", "으로 인해", "인해"],
                "hi": ["क्योंकि", "के कारण", "कारण", "वजह से"]},
}


_NUMWORD = {
    "en": {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
           "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
           "twelve": 12, "a single": 1, "a ": 1},
    "ko": {"하나": 1, "둘": 2, "셋": 3, "넷": 4, "다섯": 5},
    "hi": {"एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पाँच": 5, "पांच": 5},
}


def _spelled_number(text: str, lang: str) -> int:
    for word, val in _NUMWORD.get(lang, {}).items():
        if word in text:
            return val
    return 1


def _find(text: str, markers: list[str]) -> bool:
    return any(m in text for m in markers)


def _first_value(text: str, table: dict, lang: str):
    """Return the field value whose markers appear (first match), else None."""
    for value, langmap in table.items():
        if _find(text, langmap.get(lang, [])):
            return value
    return None


def extract_invariants(text: str, lang: str) -> dict:
    """Best-effort recovery of the typed invariant fields from ``text``.

    Returns a dict over :data:`FIELDS`; a field is ``None`` when no marker is
    found (an honest abstention, not a guess). ``lang`` in :data:`LANGS`.
    """
    if lang not in LANGS:
        raise ValueError(f"lang must be one of {LANGS}")
    low = text.lower() if lang == "en" else text  # CJK/Devanagari: keep case
    low_en = text.lower()

    out = {f: None for f in FIELDS}

    # entities
    out["agent"] = _first_value(low if lang != "en" else low_en, _AGENT, lang)
    out["patient"] = _first_value(low if lang != "en" else low_en, _PATIENT, lang)

    # predicate (closed domain: only FIX)
    probe = low_en if lang == "en" else text
    if _find(probe, _FIX.get(lang, [])):
        out["predicate"] = "FIX"

    # polarity
    negprobe = low_en if lang == "en" else text
    out["polarity"] = "negative" if _find(negprobe, _NEG.get(lang, [])) else "positive"

    # quantity: first integer digit, else a spelled-out number word, else 1.
    # MT often keeps digits in KO/HI but spells numbers in English round-trip.
    m = re.search(r"\d+", text)
    if m:
        out["quantity"] = int(m.group())
    else:
        out["quantity"] = _spelled_number(probe, lang)

    # temporal direction
    out["time_dir"] = _first_value(probe, _TIME, lang)

    # modality (possible takes precedence when both epistemic markers appear)
    if _find(probe, _MOD_POSSIBLE.get(lang, [])):
        out["modality"] = "possible"
    elif _find(probe, _MOD_NECESSARY.get(lang, [])):
        out["modality"] = "necessary"
    else:
        out["modality"] = "asserted"

    # attribution
    out["attribution"] = _first_value(probe, _ATTR, lang) or "none"

    # causation
    out["causation"] = _first_value(probe, _CAUSE, lang) or "none"

    return out
