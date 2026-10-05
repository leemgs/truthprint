# ACL/ARR submission source

`acl_main.tex` is the **anonymous ACL/ARR long-paper submission** (anonymous,
line- and page-numbered `[review]` mode). The manuscript body has a single
source of truth in `main.tex`; the ACL source is generated from it.

## Build

```bash
make acl        # python3 make_acl_source.py + 2x pdflatex -> acl_main.pdf
```

After editing `main.tex`, regenerate and verify synchronization:

```bash
python3 make_acl_source.py          # regenerate acl_main.tex
python3 make_acl_source.py --check  # fail if acl_main.tex is stale
```

## Submission compliance (desk-reject checklist)

- **Format:** official `acl.sty`, `\documentclass[11pt]{article}`, `[review]`
  mode (anonymous + line numbers + page numbers for reviewers).
- **Page limit:** the main body (Introduction through Conclusion) fits in
  **8 pages**; References, the unnumbered *Limitations* and *Ethical
  Considerations* sections, and all appendices follow and do not count toward
  the limit. Verify after any edit with the body-length probe
  (last body section must end on page 8 or earlier).
- **Mandatory sections:** *Limitations* (unnumbered) and *Ethical
  Considerations* (unnumbered) are present, after the Conclusion.
- **Anonymity:** author is "Anonymous ACL submission"; no identifying strings
  (`make acl` includes a grep guard); the compiled PDF carries no author
  metadata. The only GitHub URL is a cited third-party reference (SynthID).
- **Responsible NLP checklist:** draft answers in
  [`RESPONSIBLE_NLP_CHECKLIST.md`](RESPONSIBLE_NLP_CHECKLIST.md); transcribe
  into the portal at submission time.

## What moved to the appendix to meet the 8-page limit

Content was relocated (not deleted; recoverable in git): the reference
implementation and closed-domain round-trip/ablation, the experimental
methodology and research questions, falsifiable hypotheses, deployment
considerations, formal-analysis supporting detail, the encoding/detection
pseudocode and the IR JSON example, the worked example, and the
claim–evidence / positioning / extended result tables. The 8-page body keeps
the core method (typed invariant contract), the formal statements, and the
headline real-MT evidence (Stage-2 recovery, provenance authentication,
matched-FPR baselines, paraphrase/adaptive defense).

## Reproducibility

All real-MT numbers reproduce in-repo with no GPU from the committed raw run
under `paper/results/realmt_b2/` via `scripts/eval_multilingual.py` and
`scripts/eval_provenance.py`; other evaluations ship seeded, cached scripts
(see `code/README.md`).

## Camera-ready

Restore author metadata and acknowledgments only in the camera-ready
(`[final]` mode); do not add them to the anonymous submission.
