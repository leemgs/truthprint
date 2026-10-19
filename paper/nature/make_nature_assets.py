#!/usr/bin/env python3
"""Generate every table and figure dataset of the Nature manuscript from the
committed result files in ``paper/results/`` (no number is typed by hand).

Writes ``generated/*.tex`` (table bodies) and ``generated/*.dat`` (pgfplots data).
Run from anywhere: ``python3 paper/nature/make_nature_assets.py``.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent / "results"
OUT = HERE / "generated"

CONDS = ["rt", "ko", "hi", "zh", "ar", "de"]
LABEL = {"rt": "Round trip (EN)", "ko": "Korean", "hi": "Hindi", "zh": "Chinese",
         "ar": "Arabic", "de": "German"}
SHORT = {"rt": "RT", "ko": "KO", "hi": "HI", "zh": "ZH", "ar": "AR", "de": "DE"}
FIELDS = ["agent", "patient", "predicate", "polarity", "quantity", "time_dir",
          "modality", "attribution", "causation"]
FIELD_LABEL = {"time_dir": "time", "agent": "agent", "patient": "patient",
               "predicate": "predicate", "polarity": "polarity", "quantity": "quantity",
               "modality": "modality", "attribution": "attribution", "causation": "causation"}


def load(name: str) -> dict:
    return json.loads((RES / name).read_text(encoding="utf-8"))


def f3(x: float) -> str:
    return f"{x:.3f}"


def ci(t) -> str:
    """(point, lo, hi) -> '0.900 (0.786--0.957)'."""
    p, lo, hi = t
    return f"{p:.3f} ({lo:.3f}--{hi:.3f})"


def write(name: str, text: str) -> None:
    (OUT / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def fig2() -> None:
    prov = load("provenance_realmt.json")["contracts"]
    kgw = load("baselines_real.json")["methods"]["KGW"]["tpr_at_1pct_fpr"]
    rows = ["cond core6 full9 kgw"]
    for c in CONDS:
        rows.append(f"{SHORT[c]} {prov['core6']['conditions'][c]['document_attribution'][0]:.3f} "
                    f"{prov['full9']['conditions'][c]['document_attribution'][0]:.3f} {kgw[c]:.3f}")
    write("fig2a.dat", "\n".join(rows))
    led = load("ledger_search.json")["contracts"]
    rows = ["cond sent_core6 sent_full9 doc_core6 doc_full9"]
    for c in CONDS:
        a, b = led["core6"]["conditions"][c], led["full9"]["conditions"][c]
        rows.append(f"{SHORT[c]} {a['sentence_matches_wrong_entry'][0]:.3f} "
                    f"{b['sentence_matches_wrong_entry'][0]:.3f} "
                    f"{a['docs_with_any_false_attribution'][0]:.3f} "
                    f"{b['docs_with_any_false_attribution'][0]:.3f}")
    write("fig2b.dat", "\n".join(rows))


def table_matched(src: str, out: str) -> None:
    d = load(src)
    conds = [c for c in CONDS if c in d["conditions"]]
    names = [("meaning-digest", "Typed meaning digest (this work)"),
             ("SemStamp", "Embedding region (SemStamp-style)"),
             ("SimHash-hash", "Embedding SimHash"),
             ("MinHash-hash", "Character MinHash"),
             ("exact-hash", "Exact hash (SHA-256)")]
    tam = d["tamper_rejection"]
    lines = [r"\begin{tabular}{@{}l" + "c" * len(conds) + "c@{}}", r"\toprule",
             "Method & " + " & ".join(SHORT[c] for c in conds) + r" & Tamper rejected \\",
             r"\midrule"]
    for key, lab in names:
        cells = [f3(d["conditions"][c][key]["tpr_at_fpr"]) for c in conds]
        t = tam.get(key)
        cells.append(f3(t[0]) if t else "--")
        lines.append(lab + " & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write(out, "\n".join(lines))


def table_adaptive() -> None:
    gpt = load("neural_defense_gpt4omini.json")
    ll = load("neural_defense.json")
    rows = [("Closed lexicon", gpt["frontends"]["closed"], gpt["config"]["n_items"]),
            ("Extended lexicon", gpt["frontends"]["extended"], gpt["config"]["n_items"]),
            ("Neural extractor (GPT-4o-mini)", gpt["frontends"]["neural"], gpt["config"]["n_items"]),
            ("Neural extractor (Llama-3.3-70B)", ll["frontends"]["neural"], ll["config"]["n_items"])]
    C = r">{\centering\arraybackslash}p"
    lines = [r"\begin{tabular}{@{}p{38mm}c" + C + "{15mm}" + C + "{29mm}" + C + "{29mm}" + C + r"{15mm}@{}}", r"\toprule",
             r"Extractor & $n$ & Benign accepted & Seen attack removes & Held-out attack removes & Tamper rejected \\",
             r"\midrule"]
    for lab, f, n in rows:
        lines.append(f"{lab} & {n} & {f3(f['benign_tpr'][0])} & {ci(f['adaptive_seen_valid_removal'])} & "
                     f"{ci(f['held_out_novel_valid_removal'])} & {f3(f['tamper_rejection'][0])} " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("table2.tex", "\n".join(lines))


def ed_stage2() -> None:
    d = load("stage2_multilingual.json")["conditions"]
    lines = [r"\begin{tabular}{@{}l" + "c" * len(CONDS) + "@{}}", r"\toprule",
             "Field & " + " & ".join(SHORT[c] for c in CONDS) + r" \\", r"\midrule"]
    for f in FIELDS:
        lines.append(FIELD_LABEL[f] + " & " + " & ".join(
            f"{d[c]['per_field'][f][0]:.2f}" for c in CONDS) + r" \\")
    lines.append(r"\midrule")
    lines.append(r"All nine exact & " + " & ".join(
        f"{d[c]['all_fields_exact'][0]:.2f}" for c in CONDS) + r" \\")
    lines.append(r"Sentences ($n$) & " + " & ".join(str(d[c]["n"]) for c in CONDS) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("ed_stage2.tex", "\n".join(lines))


def ed_provenance() -> None:
    d = load("provenance_realmt.json")["contracts"]
    lines = [r"\begin{tabular}{@{}llcccc@{}}", r"\toprule",
             r"Contract & Condition & Sentence accepted & Document attributed & Tamper rejected & False positive \\",
             r"\midrule"]
    for cn in ["core6", "robust7", "full9"]:
        for i, c in enumerate(CONDS):
            x = d[cn]["conditions"][c]
            lines.append((cn if i == 0 else "") + f" & {LABEL[c]} & {f3(x['sentence_tpr'][0])} & "
                         f"{ci(x['document_attribution'])} & {f3(x['tamper_rejection'][0])} & "
                         f"{f3(x['false_positive'][0])} " + r"\\")
        if cn != "full9":
            lines.append(r"\midrule")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("ed_provenance.tex", "\n".join(lines))


def ed_ledger() -> None:
    d = load("ledger_search.json")
    C = r">{\centering\arraybackslash}p"
    lines = [r"\begin{tabular}{@{}ll" + C + "{30mm}" + C + "{30mm}" + C + r"{30mm}@{}}", r"\toprule",
             r"Contract & Condition & Sentence matches a wrong entry & Own document attributed & False document attributions \\",
             r"\midrule"]
    for cn in ["core6", "robust7", "full9"]:
        for i, c in enumerate(CONDS):
            x = d["contracts"][cn]["conditions"][c]
            fa = x["doc_false_attribution_per_pair"]
            lines.append((cn if i == 0 else "") + f" & {LABEL[c]} & {f3(x['sentence_matches_wrong_entry'][0])} & "
                         f"{f3(x['doc_true_attribution_id_free'][0])} & "
                         f"{round(fa[0] * x['n_pairs'])}/{x['n_pairs']:,} " + r"\\")
        if cn != "full9":
            lines.append(r"\midrule")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("ed_ledger.tex", "\n".join(lines))


def sci(x: float) -> str:
    """5.15e-03 -> '$5.15\\times10^{-3}$'."""
    mant, exp = f"{x:.2e}".split("e")
    return f"${mant}\\times10^{{{int(exp)}}}$"


def ed_collision() -> None:
    d = load("semantic_fp.json")
    lines = [r"\begin{tabular}{@{}lcccc@{}}", r"\toprule",
             r"Contract & Fields & Possible values & Collision entropy (bits) & Collision floor \\",
             r"\midrule"]
    for cn in ["core6", "robust7", "full9"]:
        x = d["contracts"][cn]
        lines.append(f"{cn} & {len(x['fields'])} & {x['space_size']:,} & "
                     f"{x['collision_entropy_bits']:.2f} & {sci(x['collision_prob'])} " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("ed_collision.tex", "\n".join(lines))


def ed_retrieval() -> None:
    bow = load("retrieval.json")
    emb = load("retrieval_embedding.json")
    names = [("typed", "Typed meaning digest"), ("retrieval", "Retrieval"),
             ("retrieval_nli_proxy", "Retrieval + entailment proxy"),
             ("retrieval_nli_oracle", "Retrieval + oracle entailment")]
    lines = [r"\begin{tabular}{@{}lcccc@{}}", r"\toprule",
             r" & \multicolumn{2}{c}{Bag-of-words} & \multicolumn{2}{c}{Multilingual encoder} \\",
             r"\cmidrule(lr){2-3}\cmidrule(l){4-5}",
             r"Method & Benign accepted & Tamper rejected & Benign accepted & Tamper rejected \\",
             r"\midrule"]
    for k, lab in names:
        a, b = bow["methods"][k], emb["methods"][k]
        lines.append(f"{lab} & {f3(a['benign_tpr'][0])} & {f3(a['tamper_rejection'][0])} & "
                     f"{f3(b['benign_tpr'][0])} & {f3(b['tamper_rejection'][0])} " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("ed_retrieval.tex", "\n".join(lines))


def ed_paraphrase() -> None:
    d = load("paraphrase.json")["closed"]["contracts"]["core6"]["per_operator"]
    ops = [("voice", "Voice alternation"), ("time_reflow", "Time-phrase reordering"),
           ("verb_syn", "Verb synonym"), ("time_syn", "Time synonym"),
           ("hedge", "Discourse hedge"), ("combo_benign", "Combined benign")]
    lines = [r"\begin{tabular}{@{}lccc@{}}", r"\toprule",
             r"Rule-based operator & Sentence accepted & Document attributed & Valid removal \\",
             r"\midrule"]
    for k, lab in ops:
        x = d[k]
        lines.append(f"{lab} & {f3(x['auth_tpr'][0])} & {f3(x['document_attribution'][0])} & "
                     f"{f3(x['valid_removal'][0])} " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("ed_paraphrase.tex", "\n".join(lines))


def ed_neural() -> None:
    d = load("neural_parser.json")
    lines = [r"\begin{tabular}{@{}lcc@{}}", r"\toprule",
             r"Field & Neural extractor & Lexicon \\", r"\midrule"]
    for f in FIELDS:
        lines.append(f"{FIELD_LABEL[f]} & {f3(d['fields']['neural'][f][0])} & "
                     f"{f3(d['fields']['lexicon'][f][0])} " + r"\\")
    lines.append(r"\midrule")
    lines.append(f"All nine exact & {f3(d['all_exact']['neural'][0])} & {f3(d['all_exact']['lexicon'][0])} " + r"\\")
    for dom, lab in [("template", "Mean field recovery, template wording"),
                     ("open", "Mean field recovery, open wording")]:
        lines.append(f"{lab} & {f3(d['by_domain'][dom]['neural'][0])} & {f3(d['by_domain'][dom]['lexicon'][0])} " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("ed_neural.tex", "\n".join(lines))


def ed_challenge() -> None:
    d = load("challenge_results.json")["per_field"]
    order = ["polarity", "quantity", "time_dir", "modality", "attribution", "causation"]
    lines = [r"\begin{tabular}{@{}lccc@{}}", r"\toprule",
             r"Altered field & Typed contract with tag & Decoding without tag & Embedding similarity gate \\",
             r"\midrule"]
    for f in order:
        x = d[f]
        lines.append(f"{FIELD_LABEL[f]} & {f3(x['typed_tamper_detect'][0])} & "
                     f"{f3(x['nomac_tamper_detect'][0])} & {f3(x['embed_tamper_detect'][0])} " + r"\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("ed_challenge.tex", "\n".join(lines))


def main() -> int:
    OUT.mkdir(exist_ok=True)
    fig2()
    table_matched("semantic_baselines_nllb800.json", "table1.tex")
    table_matched("semantic_baselines.json", "ed_matched16.tex")
    table_adaptive()
    ed_stage2()
    ed_provenance()
    ed_ledger()
    ed_collision()
    ed_retrieval()
    ed_paraphrase()
    ed_neural()
    ed_challenge()
    print(f"[written] {sorted(p.name for p in OUT.iterdir())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
