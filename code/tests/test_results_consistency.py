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
    src = RESULTS.parent / "main.tex"
    if not src.exists():  # the anonymous artifact ships only the ACL source
        src = RESULTS.parent / "acl_main.tex"
    tex = src.read_text(encoding="utf-8")
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


def test_same_text_fidelity_matches_committed_run_and_paper():
    import importlib.util
    root = RESULTS.parent.parent / "code" / "scripts" / "eval_same_text_fidelity.py"
    spec = importlib.util.spec_from_file_location("fid", root)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    res = mod.evaluate(RESULTS / "realmt_b2", RESULTS / "same_text")
    committed = json.loads((RESULTS / "same_text_fidelity.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(res)) == committed
    src = RESULTS.parent / "main.tex"
    if not src.exists():  # the anonymous artifact ships only the ACL source
        src = RESULTS.parent / "acl_main.tex"
    tex = src.read_text(encoding="utf-8")
    ci = lambda c: f"${c[0]:.3f}$ $[{c[1]:.3f},{c[2]:.3f}]$"  # noqa: E731
    for key in ("unwatermarked_first_sample", "kgw", "synthid"):
        assert ci(res[key]) in tex, key
    assert f"${res['draws_per_sentence_mean']:.2f}$" in tex


def test_plural_artifact_matches_committed_runs_and_paper():
    import importlib.util
    root = RESULTS.parent.parent / "code" / "scripts" / "eval_plural_artifact.py"
    spec = importlib.util.spec_from_file_location("plural", root)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    res = json.loads(json.dumps(mod.evaluate(str(RESULTS / "realmt_b2_legacy"), str(RESULTS / "realmt_b2"))))
    assert res == json.loads((RESULTS / "plural_artifact.json").read_text(encoding="utf-8"))
    # the fix changes exactly the affected sources and removes the misspelling
    assert res["changed_equals_affected"] and not res["fixed_contains_token"]
    # the corrected run's "all sentences" column must reproduce the committed provenance run
    prov = json.loads((RESULTS / "provenance_realmt.json").read_text(encoding="utf-8"))
    core6 = prov["contracts"]["core6"]["conditions"]
    for cond, d in res["fixed"]["doc_attribution_all_vs_without_affected"].items():
        assert abs(d["all"][0] - core6[cond]["document_attribution"][0]) < 1e-9, cond
    src = RESULTS.parent / "main.tex"
    if not src.exists():  # the anonymous artifact ships only the ACL source
        src = RESULTS.parent / "acl_main.tex"
    tex = src.read_text(encoding="utf-8")
    ar_old = res["legacy"]["conditions"]["ar"]["affected"]
    ar_new = res["fixed"]["conditions"]["ar"]["affected"]
    assert f"${ar_old['patient'][0]:.3f}\\to{ar_new['patient'][0]:.3f}$" in tex
    assert f"${ar_old['core6'][0]:.3f}\\to{ar_new['core6'][0]:.3f}$" in tex
    assert f"${res['affected_sources']}$ of the $800$" in tex


def test_cpu_rebuild_reproduces_unchanged_translations():
    chk = json.loads((RESULTS / "realmt_b2" / "rebuild_check.json").read_text(encoding="utf-8"))
    assert chk["changed_sources"] == 153
    assert chk["identical_to_old_run"] == chk["unchanged_translations"] == 647 * 6


def _paper_tex() -> str:
    src = RESULTS.parent / "main.tex"
    if not src.exists():  # the anonymous artifact ships only the ACL source
        src = RESULTS.parent / "acl_main.tex"
    return src.read_text(encoding="utf-8")


def _load_script(name: str):
    import importlib.util
    root = RESULTS.parent.parent / "code" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, root)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_same_text_noresample_matches_committed_run_and_paper():
    mod = _load_script("eval_same_text_noresample")
    res = json.loads(json.dumps(mod.evaluate(RESULTS / "realmt_b2", RESULTS / "same_text")))
    assert res == json.loads((RESULTS / "same_text_noresample.json").read_text(encoding="utf-8"))
    tex = _paper_tex()
    c = res["conditions"]
    assert (f"${c['ko']['document_attribution'][0]:.3f}$/${c['ar']['document_attribution'][0]:.3f}$/"
            f"${c['de']['document_attribution'][0]:.3f}$") in tex
    assert res["exact"] and res["first_sample_unavailable"] == 0
    assert f"${res['redrawn']}$ redrawn sentences" in tex
    # the first-sample clean sentence rate equals the committed fidelity proxy
    fid = json.loads((RESULTS / "same_text_fidelity.json").read_text(encoding="utf-8"))
    assert abs(c["clean"]["sentence_authentication"][0] - fid["unwatermarked_first_sample"][0]) < 1e-9


def test_edited_tamper_matches_committed_run_and_paper():
    mod = _load_script("eval_edited_tamper")
    res = json.loads(json.dumps(mod.evaluate(str(RESULTS / "realmt_b2"), str(RESULTS / "edited_tamper"))))
    assert res == json.loads((RESULTS / "edited_tamper_eval.json").read_text(encoding="utf-8"))
    tex = _paper_tex()
    c6, f9 = res["contracts"]["core6"], res["contracts"]["full9"]
    fa = c6["false_accept_in_contract"]
    assert f"$0.002$ (CI $[{fa[1]:.3f},{fa[2]:.3f}]$, $n{{=}}3{{,}}000$)" in tex and f"{fa[0]:.3f}" == "0.002"
    assert f"${c6['reads_edit_in_contract'][0]:.3f}$" in tex
    assert f"${c6['accepted_outside_contract'][0]:.3f}$" in tex
    assert f"${f9['false_accept_in_contract'][0]:.3f}$" in tex
    pf = f9["per_field"]
    assert f"${pf['modality']['accepted'][0]:.3f}$/${pf['causation']['accepted'][0]:.3f}$" in tex
    # the abstract's 0.998 is 1 - core6 in-contract false accept
    assert f"${1 - fa[0]:.3f}$" in tex


def test_same_text_quality_numbers_in_paper():
    res = json.loads((RESULTS / "same_text_quality.json").read_text(encoding="utf-8"))
    tex = _paper_tex()
    for v in ("first", "kgw", "synthid", "none"):
        assert f"${res['variants'][v]['ppl_geomean'][0]:.1f}$" in tex, v


def test_llm_edited_tamper_matches_committed_run_and_paper():
    mod = _load_script("eval_llm_edited_tamper")
    src = mod.sources(RESULTS / "edited_tamper")
    res = json.loads(json.dumps(mod.score(RESULTS / "realmt_b2", src, RESULTS / "llm_edited_tamper")))
    assert res == json.loads((RESULTS / "llm_edited_tamper_eval.json").read_text(encoding="utf-8"))
    tex = _paper_tex()
    d = res["contracts"]["core6"]["in_contract"]
    t, c = d["translated"]["accepted"], d["clean"]["accepted"]
    assert f"${t[0]:.3f}$ $[{t[1]:.3f},{t[2]:.3f}]$" in tex
    assert f"(${c[0]:.3f}$ in English" in tex
    assert f"${1 - t[0]:.3f}$ after LLM rewording" in tex
