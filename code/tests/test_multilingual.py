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


def test_abstention_is_not_a_guess():
    # unknown entity -> agent/patient None rather than a wrong guess
    inv = extract_invariants("Someone changed something yesterday.", "en")
    assert inv["agent"] is None
    assert inv["patient"] is None
