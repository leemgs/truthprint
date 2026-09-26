"""Stage-2 multilingual invariant extractor (semantic frontend).

The Stage-1 frontend (:mod:`truthprint.linguistic`, :mod:`truthprint.challenge`)
only parses the exact English template it generated, so it cannot read real
machine-translation output (Section ``sec:realmt``: 0/192 parse coverage). This
module is a first, honest step toward the wide-coverage semantic frontend the
paper defers to future work: a **closed-domain, lexicon-based extractor** that
reads a sentence in English, Korean, Hindi, Chinese, Arabic, or German and
recovers the *typed invariant fields* (the meaning layer), independent of
surface realization.

It is deliberately rule/lexicon-based (standard-library only, no model, no
network) so it runs anywhere and is fully auditable. Its purpose is to test the
paper's central hypothesis on **real** MT output: meaning-layer fields
(polarity, quantity, temporal direction, attribution, causation, modality)
survive translation and are recoverable, whereas surface carriers do not. It is
not a wide-coverage parser; entities a translator renders inconsistently are
recovered less reliably, and those honest misses are part of the measured
result. Lexicons are grounded in standard dictionary renderings of the
closed-domain vocabulary, not tuned to any particular MT system's output.
"""
from __future__ import annotations

import re

__all__ = ["extract_invariants", "FIELDS", "LANGS"]

FIELDS = ["agent", "patient", "predicate", "polarity", "quantity",
          "time_dir", "modality", "attribution", "causation"]
LANGS = ["en", "ko", "hi", "zh", "ar", "de"]

# --- lexicons: field value -> {lang: [surface markers]} --------------------- #
_AGENT = {
    "the developer": {"en": ["developer"], "ko": ["개발자"], "hi": ["डेवलपर"],
                      "zh": ["开发者", "开发人员"], "ar": ["المطور", "المطوّر", "مطور"],
                      "de": ["entwickler"]},
    "the engineer":  {"en": ["engineer"], "ko": ["엔지니어"], "hi": ["इंजीनियर"],
                      "zh": ["工程师"], "ar": ["المهندس", "مهندس"],
                      "de": ["ingenieur"]},
    "the operator":  {"en": ["operator"], "ko": ["운영자"], "hi": ["ऑपरेटर", "संचालक"],
                      "zh": ["操作员", "运维", "运营商"],
                      "ar": ["المشغل", "المشغّل", "مشغل"],
                      "de": ["betreiber", "operator"]},
    "the analyst":   {"en": ["analyst"], "ko": ["분석가"], "hi": ["विश्लेषक"],
                      "zh": ["分析师", "分析员"], "ar": ["المحلل", "محلل"],
                      "de": ["analyst"]},
}
_PATIENT = {
    "server error": {"en": ["server error", "server bug"], "ko": ["서버 오류", "서버 에러"],
                     "hi": ["सर्वर त्रुटि", "सर्वर एरर"], "zh": ["服务器错误", "服务器故障"],
                     "ar": ["خطأ الخادم", "خطأ في الخادم", "خطأ خادم", "أخطاء خادم",
                            "أخطاء الخادم", "أخطاء في الخادم", "خادم"],
                     "de": ["serverfehler", "server-fehler"]},
    "memory leak":  {"en": ["memory leak"], "ko": ["메모리 누출", "메모리 누수", "메모리 유출"],
                     "hi": ["मेमोरी लीक"],
                     "zh": ["内存泄漏", "内存泄露", "记忆泄漏", "记忆泄露", "记忆泄"],
                     "ar": ["تسرب الذاكرة", "تسرّب الذاكرة"],
                     "de": ["speicherleck", "speicherleck", "memory leak"]},
    "config drift": {"en": ["config", "configuration"], "ko": ["구성", "구성 드리프트", "컨피그"],
                     "hi": ["कॉन्फ़िग", "कॉन्फ़िगरेशन", "विन्यास"],
                     "zh": ["配置漂移", "配置"],
                     "ar": ["انحراف التكوين", "التكوين", "التهيئة", "الإعداد",
                            "إعداد", "إعدادي", "التكوينات"],
                     "de": ["konfigurationsabweichung", "konfiguration"]},
    "cache miss":   {"en": ["cache"], "ko": ["캐시"], "hi": ["कैश"],
                     "zh": ["缓存未命中", "缓存"],
                     "ar": ["فقدان ذاكرة التخزين", "الكاش", "التخزين المؤقت",
                            "ذاكرة التخزين", "التخزين الاحتياطي"],
                     "de": ["cache-fehl", "cache-miss", "cache"]},
}
_NEG = {"en": [" not ", "n't", "never", "should not", "not fix",
               "failed to", "fail to", "unable to", "did not", "was not able"],
        "ko": ["않", "없", "안 ", "못"],
        "hi": ["नहीं", "मत "],
        "zh": ["没有", "未", "不", "沒"],
        # space-delimited: bare "لا"/"لم" would false-match inside common words
        # (e.g. الانقطاع "outage", لمنع "to prevent"); the search text is padded.
        "ar": [" لا ", " لم ", " ليس ", " لن ", " لمْ "],
        "de": ["nicht", "kein"]}
_FIX = {"en": ["fix", "correct", "modif", "resolv", "repair", "set up", "setup",
               "address"],
        "ko": ["수정", "고정", "설정", "정정", "해결", "복구"],
        "hi": ["ठीक", "तय", "सुधार", "हल", "समाधान"],
        "zh": ["修复", "修正", "解决", "修好", "修理"],
        "ar": ["صلح", "إصلاح", "تصليح", "صحح", "صحّح", "تصحيح", "حل", "عالج"],
        "de": ["behob", "behoben", "beheben", "behebt", "korrigier", "reparier",
               "löste", "gelöst", "fixier"]}
_TIME = {
    "following": {"en": ["next day", "following day", "day after"],
                  "ko": ["다음 날", "다음날", "이튿날"],
                  "hi": ["अगले दिन", "अगला दिन"],
                  "zh": ["第二天", "次日", "隔天", "翌日", "下一天"],
                  "ar": ["اليوم التالي", "في اليوم التالي", "اليوم الموالي"],
                  "de": ["nächsten tag", "folgenden tag", "folgetag", "tag darauf"]},
    "previous":  {"en": ["previous day", "day before", "prior day", "preceding day"],
                  "ko": ["전날", "이전 날", "지난날", "전 날"],
                  "hi": ["पिछले दिन", "पिछला दिन", "एक दिन पहले"],
                  "zh": ["前一天", "前天", "昨天", "上一天"],
                  "ar": ["اليوم السابق", "في اليوم السابق", "اليوم الماضي"],
                  "de": ["vortag", "vorherigen tag", "vorigen tag", "tag zuvor"]},
}
_MOD_POSSIBLE = {"en": ["may ", "might", "could", "can be", "possibly", "perhaps"],
                 "ko": ["수 있", "수도 있", "지도 모"],
                 "hi": ["सकत", "शायद"],
                 "zh": ["可能", "也许", "或许", "大概"],
                 "ar": ["قد لا", "قد ي", "ربما", "يمكن أن", "من الممكن",
                        "من المحتمل"],
                 "de": ["könnte", "könnten", "konnte", "konnten", "kann ",
                        "möglicherweise", "vielleicht", "dürfte"]}
_MOD_NECESSARY = {"en": ["must", "should", "has to", "have to", "had to",
                         "need to", "ought to", "required"],
                  "ko": ["해야", "않아야", "야 합니다", "야 한다", "필요", "해야 합니다"],
                  "hi": ["चाहिए", "करना होगा", "करना पड़", "आवश्यक", "ज़रूरी",
                         "किया होगा", "होंगे", "होगा", "होगी"],
                  "zh": ["必须", "应该", "需要", "得 "],
                  "ar": ["يجب", "ينبغي", "عليه أن", "لا بد", "لا بدّ", "ضروري"],
                  "de": ["muss", "müssen", "sollte", "sollten", "notwendig",
                         "erforderlich", "darf nicht", "dürfen nicht", "darf kein"]}
_ATTR = {
    "report": {"en": ["according to the report", "the report", "report says",
                      "per the report"],
               "ko": ["보고서에 따르면", "보고서에", "보고서"],
               "hi": ["रिपोर्ट के अनुसार", "रिपोर्ट के मुताबिक", "रिपोर्ट"],
               "zh": ["根据报告", "据报告", "报告称", "报告", "根据报道", "据报道", "报道"],
               "ar": ["وفقًا للتقرير", "حسب التقرير", "بحسب التقرير", "وفقا للتقرير",
                      "التقرير", "للتقرير", "تقرير"],
               "de": ["laut bericht", "dem bericht zufolge", "bericht"]},
    "vendor": {"en": ["according to the vendor", "the vendor", "vendor says",
                      "according to the seller", "the seller", "supplier"],
               "ko": ["판매자", "공급업체", "공급자", "벤더", "판매업체"],
               "hi": ["विक्रेता के अनुसार", "विक्रेता", "आपूर्तिकर्ता", "वेंडर"],
               "zh": ["根据供应商", "据供应商", "供应商", "卖方", "厂商"],
               "ar": ["وفقًا للبائع", "حسب المورد", "البائع", "المورد", "المورّد",
                      "للبائع", "بائع", "للمورد", "مورد"],
               "de": ["laut anbieter", "laut verkäufer", "dem anbieter zufolge",
                      "anbieter", "verkäufer", "lieferant"]},
}
_CAUSE = {
    "purpose": {"en": ["to prevent", "to avoid", "in order to", "so as to",
                       "to stop"],
                "ko": ["방지하기 위해", "막기 위해", "위해", "위하여", "방지", "막기"],
                "hi": ["रोकने के लिए", "बचने के लिए", "के लिए"],
                "zh": ["为了防止", "为防止", "以防止", "为了避免", "为了"],
                "ar": ["لمنع", "من أجل منع", "لتجنب", "من أجل"],
                "de": ["um zu verhindern", "um zu vermeiden", "zu verhindern",
                       "um ein", "um eine"]},
    "cause":   {"en": ["because", "due to", "owing to", "as a result of",
                       "caused by"],
                "ko": ["때문", "로 인해", "으로 인해", "인해"],
                "hi": ["क्योंकि", "के कारण", "कारण", "वजह से"],
                "zh": ["因为", "由于", "因", "导致"],
                "ar": ["بسبب", "نظرًا", "لأن", "بسبَب"],
                "de": ["wegen", "aufgrund", "weil", "da "]},
}
_NUMWORD = {
    "en": {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
           "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
           "twelve": 12, "a single": 1, "a ": 1},
    "ko": {"하나": 1, "둘": 2, "셋": 3, "넷": 4, "다섯": 5},
    "hi": {"एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पाँच": 5, "पांच": 5},
    "zh": {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
           "八": 8, "九": 9, "十": 10},
    "ar": {"واحد": 1, "اثنان": 2, "اثنين": 2, "ثلاثة": 3, "أربعة": 4, "خمسة": 5,
           "ستة": 6, "سبعة": 7, "ثمانية": 8, "تسعة": 9, "عشرة": 10},
    "de": {"eins": 1, "ein ": 1, "eine ": 1, "zwei": 2, "drei": 3, "vier": 4,
           "fünf": 5, "sechs": 6, "sieben": 7, "acht": 8, "neun": 9, "zehn": 10},
}

# Arabic-Indic digits -> ASCII (some MT systems emit them)
_ARABIC_DIGITS = {ord(a): d for a, d in zip("٠١٢٣٤٥٦٧٨٩", "0123456789")}


def _spelled_number(text: str, lang: str) -> int:
    for word, val in _NUMWORD.get(lang, {}).items():
        if word in text:
            return val
    return 1


def _find(text: str, markers: list[str]) -> bool:
    return any(m in text for m in markers)


def _first_value(text: str, table: dict, lang: str):
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
    # normalize case for Latin-script languages; keep others verbatim
    norm = text.lower() if lang in ("en", "de") else text

    out = {f: None for f in FIELDS}
    out["agent"] = _first_value(norm, _AGENT, lang)
    out["patient"] = _first_value(norm, _PATIENT, lang)
    if _find(norm, _FIX.get(lang, [])):
        out["predicate"] = "FIX"
    # pad so space-delimited negation markers can match at string boundaries
    padded = f" {norm} "
    out["polarity"] = "negative" if _find(padded, _NEG.get(lang, [])) else "positive"

    # quantity: strip temporal phrases first, else an ordinal inside a time
    # expression is misread as a count (e.g. Chinese 第二天 "next day" -> 二 -> 2).
    qtext = norm
    for _tv in _TIME.values():
        for _tm in _tv.get(lang, []):
            qtext = qtext.replace(_tm, " ")
    digits = qtext.translate(_ARABIC_DIGITS)
    m = re.search(r"\d+", digits)
    out["quantity"] = int(m.group()) if m else _spelled_number(qtext, lang)

    out["time_dir"] = _first_value(norm, _TIME, lang)
    if _find(norm, _MOD_POSSIBLE.get(lang, [])):
        out["modality"] = "possible"
    elif _find(norm, _MOD_NECESSARY.get(lang, [])):
        out["modality"] = "necessary"
    else:
        out["modality"] = "asserted"
    out["attribution"] = _first_value(norm, _ATTR, lang) or "none"
    out["causation"] = _first_value(norm, _CAUSE, lang) or "none"
    return out
