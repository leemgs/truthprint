"""Tests for the Stage-2 multilingual invariant extractor.

Uses real NLLB-style sentences (English, Korean, Hindi) to check that the
meaning-layer fields are recovered across languages, and that a
meaning-altering edit changes a recovered field (cross-lingual tamper signal).
"""
from truthprint.multilingual import extract_invariants, FIELDS


def test_english_roundtrip_style():
    inv = extract_invariants(
        "The day before, the developer may not have fixed the server error "
        "due to a bug.", "en")
    assert inv["agent"] == "the developer"
    assert inv["patient"] == "server error"
    assert inv["predicate"] == "FIX"
    assert inv["polarity"] == "negative"
    assert inv["time_dir"] == "previous"
    assert inv["modality"] == "possible"
    assert inv["causation"] == "cause"


def test_korean_direct_translation():
    # "According to the report, the next day the engineer had to fix 3 server
    #  errors to prevent an outage."
    inv = extract_invariants(
        "보고서에 따르면, 다음 날 엔지니어는 장애를 방지하기 위해 3개의 서버 오류를 "
        "수정해야 합니다.", "ko")
    assert inv["agent"] == "the engineer"
    assert inv["patient"] == "server error"
    assert inv["predicate"] == "FIX"
    assert inv["polarity"] == "positive"
    assert inv["quantity"] == 3
    assert inv["time_dir"] == "following"
    assert inv["modality"] == "necessary"
    assert inv["attribution"] == "report"
    assert inv["causation"] == "purpose"


def test_korean_negative_possible():
    inv = extract_invariants(
        "전날 개발자는 장애로 인해 서버 오류를 수정하지 않았을 수도 있습니다.", "ko")
    assert inv["polarity"] == "negative"
    assert inv["modality"] == "possible"
    assert inv["time_dir"] == "previous"
    assert inv["causation"] == "cause"


def test_hindi_fields():
    inv = extract_invariants(
        "रिपोर्ट के अनुसार, अगले दिन, इंजीनियर ने 2 सर्वर त्रुटि को ठीक किया।", "hi")
    assert inv["attribution"] == "report"
    assert inv["time_dir"] == "following"
    assert inv["quantity"] == 2
    assert inv["patient"] == "server error"
    assert inv["predicate"] == "FIX"


def test_tamper_changes_a_field():
    base = extract_invariants("The developer fixed the server error the day before.", "en")
    neg = extract_invariants("The developer did not fix the server error the day before.", "en")
    assert base["polarity"] == "positive" and neg["polarity"] == "negative"


def test_chinese_fields():
    # "According to the report, the next day the engineer had to fix 3 server
    #  errors to prevent an outage."
    inv = extract_invariants(
        "根据报告，第二天工程师必须修复3个服务器错误以防止故障。", "zh")
    assert inv["attribution"] == "report"
    assert inv["time_dir"] == "following"
    assert inv["modality"] == "necessary"
    assert inv["quantity"] == 3
    assert inv["patient"] == "server error"
    assert inv["predicate"] == "FIX"
    assert inv["causation"] == "purpose"


def test_arabic_fields():
    # "The previous day, the developer did not fix the server error."
    inv = extract_invariants(
        "في اليوم السابق، لم يصلح المطور خطأ الخادم.", "ar")
    assert inv["time_dir"] == "previous"
    assert inv["polarity"] == "negative"
    assert inv["agent"] == "the developer"
    assert inv["patient"] == "server error"


def test_german_fields():
    # "According to the vendor, the operator could fix two memory leaks the
    #  next day."
    inv = extract_invariants(
        "Laut Anbieter könnte der Betreiber am nächsten Tag zwei Speicherlecks "
        "beheben.", "de")
    assert inv["attribution"] == "vendor"
    assert inv["modality"] == "possible"
    assert inv["time_dir"] == "following"
    assert inv["quantity"] == 2
    assert inv["predicate"] == "FIX"


def test_arabic_indic_digits():
    inv = extract_invariants("المطور أصلح ٥ أخطاء.", "ar")
    assert inv["quantity"] == 5


def test_arabic_morphology_variants():
    # Standard-MSA variants a translator commonly emits: definite article
    # assimilation after the preposition la- (للتقرير, للبائع), plural /
    # indefinite patient nouns (أخطاء خادم), and the imperfect verb form
    # (يصلح) rather than the perfect (أصلح). These are dictionary morphology,
    # not any one MT system's quirks.
    inv = extract_invariants(
        "وفقاً للتقرير، في اليوم التالي، لم يصلح المهندس أخطاء خادم.", "ar")
    assert inv["attribution"] == "report"
    assert inv["time_dir"] == "following"
    assert inv["polarity"] == "negative"
    assert inv["patient"] == "server error"
    assert inv["predicate"] == "FIX"


def test_arabic_vendor_and_possible_modality():
    inv = extract_invariants(
        "وفقاً للبائع، قد لا يكون المشغل قد أصلح خطأ الخادم.", "ar")
    assert inv["attribution"] == "vendor"
    assert inv["modality"] == "possible"
    assert inv["polarity"] == "negative"


def test_arabic_perfective_qad_is_not_possible():
    # "قد" before a past-tense verb is the perfective particle ("has"),
    # not the modal "might"; with a necessity marker present the modality
    # must resolve to necessary, not possible.
    inv = extract_invariants(
        "يجب أن يكون المهندس قد أصلح خطأ الخادم.", "ar")
    assert inv["modality"] == "necessary"


def test_korean_ability_negation_and_purpose():
    # "못" is the standard ability-negation particle; a result clause expressing
    # prevention still carries the purpose relation.
    inv = extract_invariants(
        "다음 날 엔지니어는 5개의 캐시 오류를 수정하여 장애를 방지했습니다.", "ko")
    assert inv["causation"] == "purpose"
    inv2 = extract_invariants("개발자는 서버 오류를 수정하지 못했습니다.", "ko")
    assert inv2["polarity"] == "negative"


def test_english_action_negation_and_past_necessity():
    inv = extract_invariants(
        "The next day the developer failed to fix the server error.", "en")
    assert inv["polarity"] == "negative"
    inv2 = extract_invariants(
        "The day before, the operator had to fix five config drifts.", "en")
    assert inv2["modality"] == "necessary"
    assert inv2["quantity"] == 5


def test_german_simple_past_modal_and_anglicism_verb():
    inv = extract_invariants(
        "Laut Bericht konnte der Entwickler am Vortag drei Serverfehler fixieren.",
        "de")
    assert inv["modality"] == "possible"
    assert inv["predicate"] == "FIX"


def test_chinese_ordinal_not_counted_and_report_variant():
    # 第二天 ("next day") must not be read as quantity 2; 报道 is a report variant.
    inv = extract_invariants(
        "据报道，第二天，工程师修复了服务器错误。", "zh")
    assert inv["quantity"] == 1
    assert inv["attribution"] == "report"
    assert inv["time_dir"] == "following"


def test_hindi_presumptive_necessity():
    inv = extract_invariants(
        "रिपोर्ट के अनुसार, अगले दिन, इंजीनियर ने 5 सर्वर त्रुटि ठीक की होगी।", "hi")
    assert inv["modality"] == "necessary"


def test_abstention_is_not_a_guess():
    # unknown entity -> agent/patient None rather than a wrong guess
    inv = extract_invariants("Someone changed something yesterday.", "en")
    assert inv["agent"] is None
    assert inv["patient"] is None
