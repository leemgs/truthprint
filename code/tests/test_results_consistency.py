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
