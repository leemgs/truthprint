"""Tests for the real head-to-head baseline scorer (W4).

Uses a synthetic fixture with a known structure -- a token-level method that
detects on clean text but collapses after translation, and a meaning-level
method that survives -- to check that the scorer computes TPR@FPR, thresholds,
and AUC correctly. It asserts the arithmetic, not the science.
"""
import json
import random

from scripts.eval_baselines_real import (score, merge_truthprint,
                                          _threshold_at_fpr, _auc)


def _fixture(seed=0):
    rng = random.Random(seed)
    recs = []
    # null population (unwatermarked) ~ N(0,1)
    for i in range(200):
        for cond in ["clean", "ko"]:
            recs.append({"method": "KGW", "impl": "self-contained KGW",
                         "doc_id": f"N{i}", "condition": cond,
                         "watermarked": False, "score": rng.gauss(0, 1)})
            recs.append({"method": "SemStamp", "impl": "official",
                         "doc_id": f"N{i}", "condition": cond,
                         "watermarked": False, "score": rng.gauss(0, 1)})
    # KGW: strong on clean, collapses after translation
    for i in range(200):
        recs.append({"method": "KGW", "impl": "self-contained KGW",
                     "doc_id": f"W{i}", "condition": "clean",
                     "watermarked": True, "score": rng.gauss(6, 1)})
        recs.append({"method": "KGW", "impl": "self-contained KGW",
                     "doc_id": f"W{i}", "condition": "ko",
                     "watermarked": True, "score": rng.gauss(0.2, 1)})
        # SemStamp: survives translation
        recs.append({"method": "SemStamp", "impl": "official",
                     "doc_id": f"W{i}", "condition": "clean",
                     "watermarked": True, "score": rng.gauss(6, 1)})
        recs.append({"method": "SemStamp", "impl": "official",
                     "doc_id": f"W{i}", "condition": "ko",
                     "watermarked": True, "score": rng.gauss(5, 1)})
    return recs


def test_threshold_controls_fpr():
    null = [float(i) for i in range(100)]  # 0..99
    thr = _threshold_at_fpr(null, 0.01)
    fp = sum(1 for x in null if x > thr) / len(null)
    assert fp <= 0.01


def test_auc_monotone():
    assert _auc([3, 4, 5], [0, 1, 2]) == 1.0
    assert _auc([0, 1, 2], [0, 1, 2]) == 0.5


def test_token_method_collapses_semantic_survives():
    out = score(_fixture(), fpr=0.01)
    kgw = out["methods"]["KGW"]["conditions"]
    sem = out["methods"]["SemStamp"]["conditions"]
    # KGW: high TPR on clean, near-zero after translation.
    assert kgw["clean"]["tpr_at_fpr"][0] > 0.9
    assert kgw["ko"]["tpr_at_fpr"][0] < 0.2
    # SemStamp: retains detection after translation.
    assert sem["ko"]["tpr_at_fpr"][0] > 0.8
    # AUC sanity: KGW clean near 1, KGW translated near 0.5.
    assert kgw["clean"]["roc_auc"][0] > 0.98
    assert abs(kgw["ko"]["roc_auc"][0] - 0.5) < 0.1


def test_merge_truthprint(tmp_path):
    prov = {"contracts": {"core6": {"conditions": {
        "ko": {"sentence_tpr": [0.9675, 0.95, 0.98],
               "document_attribution": [1.0, 0.93, 1.0], "n_sent": 800},
    }}}}
    p = tmp_path / "prov.json"
    p.write_text(json.dumps(prov), encoding="utf-8")
    out = score(_fixture(), fpr=0.01)
    merge_truthprint(out, p, contract="core6")
    key = "Truthprint (meaning-digest, core6)"
    assert key in out["methods"]
    assert out["methods"][key]["conditions"]["ko"]["tpr_at_fpr"][0] == 0.9675
