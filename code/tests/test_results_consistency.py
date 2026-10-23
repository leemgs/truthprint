"""Committed result summaries must agree with the runs they are derived from."""
import json
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[2] / "paper" / "results"


def test_baselines_truthprint_rows_match_committed_provenance_run():
    prov = json.loads((RESULTS / "provenance_realmt.json").read_text(encoding="utf-8"))
    core6 = prov["contracts"]["core6"]["conditions"]
    row = json.loads((RESULTS / "baselines_real.json").read_text(encoding="utf-8"))[
        "methods"]["Truthprint (meaning-digest, core6)"]
    for cond, measured in core6.items():
        assert row["document_attribution"][cond] == round(measured["document_attribution"][0], 3)
        assert row["sentence_tpr"][cond] == round(measured["sentence_tpr"][0], 3)


def test_same_text_table_matches_committed_run():
    res = json.loads((RESULTS / "same_text_nllb.json").read_text(encoding="utf-8"))
    tex = (RESULTS.parent / "main.tex").read_text(encoding="utf-8")
    i = tex.index("\\label{tab:sametext}")
    table = tex[tex.rindex("\\begin{table*}", 0, i):]
    table = table[: table.index("\\end{table*}")]
    for cond, label in (("clean", "clean"), ("ko", "KO"), ("ar", "AR"), ("de", "DE")):
        r = res["conditions"][cond]
        k, s, t = r["KGW"], r["SynthID-Text"], r["Truthprint (core6)"]
        ci = lambda c: f"{c[0]:.3f} [{c[1]:.3f},{c[2]:.3f}]"  # noqa: E731
        row = (f"{label} & {ci(k['tpr_above_max_null'])} & {k['roc_auc']:.3f} & "
               f"{ci(s['tpr_above_max_null'])} & {s['roc_auc']:.3f} & "
               f"{ci(t['document_attribution'])} & {t['sentence_authentication'][0]:.3f} \\\\")
        assert row in table, row
        assert t["docs_with_false_attribution"][0] == 0.0
    v = res["truthprint_valid_realization"]
    assert f"${v[0]:.3f}$ $[{v[1]:.3f},{v[2]:.3f}]$" in table
