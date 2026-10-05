# Responsible NLP Research Checklist (ARR / ACL 2027)

Draft answers for the submission portal. Transcribe into START/OpenReview at
submission time; wording may need to match the venue's current form. Section and
table references are to the anonymous ACL build (`acl_main.tex` / `acl_main.pdf`).

## A. For every submission

- **A1. Did you discuss the limitations of your work?** **Yes** — unnumbered
  *Limitations* section (after the Conclusion). It states the closed-domain,
  small-scale scope; imperfect multilingual parsing; low carrier capacity in
  constrained text; the fixed-lexicon adaptive-attack vulnerability and its
  open-vocabulary defense; and that comparative robustness and deployment
  readiness at wide coverage are not established.
- **A2. Did you discuss any potential risks of your work?** **Yes** —
  unnumbered *Ethical Considerations* section: misuse of a provenance detector
  (false accusation, censorship, automated discipline), dual-use of public
  carrier families and over-detailed payloads, and mitigations (treat a positive
  as evidence about a participating keyed generator only, calibrated error rates,
  appeal path, no personal identifiers in payloads).
- **A3. Do the abstract and introduction summarize the paper's claims?**
  **Yes** — the abstract and §1, with an explicit claim–evidence boundary
  (Appendix Table, "Claim–Evidence Boundary") separating demonstrated,
  conditional, and hypothesized claims.
- **A4. Did you use AI assistants (e.g., ChatGPT, Copilot) in your research
  and/or writing?** **Author to confirm.** Recommended disclosure if used:
  "AI coding/writing assistants were used for software scaffolding and editing;
  all claims, experiments, and numbers were verified by the authors against the
  committed artifact."

## B. Scientific artifacts

- **B1. Did you cite the creators of artifacts you used?** **Yes** — NLLB-200
  (translation), KGW (token-watermark baseline, cite), SemStamp (semantic
  baseline, cite), MinHash/SimHash (robust-hashing baselines, cite), and the
  instruction LLMs used for the neural frontend (named in §Experiments /
  Table). All baseline and tool references are in the bibliography.
- **B2. Did you discuss the license / terms of use?** **Partly — author to
  confirm.** NLLB-200-distilled-600M is open-weights (CC-BY-NC for NLLB);
  the released code/artifact is the authors'. State the artifact license in the
  camera-ready (e.g., the repository's LICENSE).
- **B3. Did you discuss whether your use was consistent with intended use?**
  **Yes (implicitly) — author to confirm.** All third-party artifacts are used
  for research evaluation, consistent with their research/benchmark intent;
  NLLB is used non-commercially for research.
- **B4. Did you discuss steps for PII / offensive content?** **Yes** — the
  evaluation uses **synthetic template facts only**: no personal data, no human
  subjects, no user content (stated in §Ethical Considerations). Payloads are
  specified to exclude personal identifiers, prompts, and exact timestamps.
- **B5. Did you provide documentation of the artifacts?** **Yes** — the
  repository ships the code, seeded scripts, cached extractions, and the full
  raw real-MT run under `paper/results/realmt_b2/`; the appendix gives the
  reproducibility/notation map and the extended evaluation protocol.
- **B6. Did you report statistics about the data?** **Yes** — 50 source
  documents × 16 sentences = 800 items; 4,800 real NLLB translations across six
  conditions (ko/hi/zh/ar/de + round-trip); paraphrase/adaptive corpora sizes
  and seeds are stated per experiment.

## C. Computational experiments

- **C1. Did you report the number of parameters and compute budget?**
  **Partly.** The translation model is NLLB-200-distilled-600M (~600M params);
  the neural-frontend extractors are named instruction LLMs (GPT-4o-mini,
  Llama-3.3-70B). The method's own cryptographic/coding core is parameter-free;
  end-to-end latency is explicitly stated as unmeasured (Appendix, Complexity).
  Compute is modest (no training; translation + cached extraction). *Author:
  add wall-clock/GPU-hours if the venue requires.*
- **C2. Did you report the experimental setup and hyperparameters?** **Yes** —
  KGW γ=0.25, δ=2.0; contracts core6/robust7/full9; τ=32-bit tags; matched 1%
  FPR calibration; seeds fixed; full protocol in Appendix (Extended Evaluation
  Protocol).
- **C3. Did you report descriptive statistics (e.g., CIs, multiple runs)?**
  **Yes** — Wilson 95% confidence intervals throughout; seeded determinism; the
  contract-collision false-positive floor is derived and matched to measured
  values.
- **C4. Did you use existing packages, and report versions/settings?**
  **Partly — author to confirm versions.** NLLB-200-distilled-600M, a real
  multilingual sentence embedding (model2vec), and OpenAI-compatible API
  backends for the neural frontend. Pin versions in the artifact README for the
  camera-ready.

## D. Human annotators / crowdsourcing

- **Not applicable.** No human annotators, crowdsourcing, or human subjects were
  used; all data are synthetic template facts and their machine translations.
  (Any future scaled evaluation adding human factual-equivalence annotation must
  use licensed/consented text and compensated, documented annotation — stated in
  §Ethical Considerations.)

## E. Notes for the author before submitting

1. Confirm A4 (AI-assistant disclosure) in the venue's exact wording.
2. Add the artifact license (B2) and pin tool/model versions (C4) in the
   repository README for the camera-ready.
3. If the venue's form asks for GPU-hours (C1), fill in the actual translation +
   extraction compute.
4. The *Limitations* section is present and unnumbered; the 8-page body excludes
   it, the references, and the appendices, per ACL policy.
