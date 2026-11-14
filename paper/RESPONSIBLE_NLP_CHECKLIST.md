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
  (translation); KGW (token watermark on GPT-2 and Qwen2.5-0.5B-Instruct
  generations); SynthID-Text (`transformers` implementation); SemStamp (our
  SemStamp-style re-implementation); MinHash/SimHash (robust hashing); the
  retrieval defense of Krishna et al. (2023); the encoders
  `paraphrase-multilingual-MiniLM-L12-v2` (Reimers & Gurevych 2020) and
  `potion-multilingual-128M`; and the instruction LLMs of the neural frontend
  (GPT-4o-mini, Llama-3.3-70B). All are in the bibliography or the appendix
  "Models, Data, and Licenses".
- **B2. Did you discuss the license / terms of use?** **Yes** — appendix
  "Models, Data, and Licenses" lists every model's license (NLLB-200
  CC-BY-NC-4.0; GPT-2 MIT; Qwen2.5-0.5B-Instruct, `transformers`, MiniLM
  encoder Apache-2.0; potion encoder MIT; GPT-4o-mini API terms; Llama 3.3
  Community License). The released code is MIT (`code/LICENSE`).
- **B3. Did you discuss whether your use was consistent with intended use?**
  **Yes** — same appendix: every use is research evaluation within these terms,
  and because of the NLLB license the measured pipeline is not a deployable
  commercial system.
- **B4. Did you discuss steps for PII / offensive content?** **Yes** — the
  evaluation uses **synthetic template facts only**: no personal data, no human
  subjects, no user content (stated in §Ethical Considerations). Payloads are
  specified to exclude personal identifiers, prompts, and exact timestamps.
- **B5. Did you provide documentation of the artifacts?** **Yes** — the
  repository ships the code, seeded scripts, cached extractions, the full raw
  real-MT run under `paper/results/realmt_b2/` (and the pre-fix run under
  `realmt_b2_legacy/`); the appendix gives the reproducibility/notation map
  and the "Evaluation Coverage" section.
- **B6. Did you report statistics about the data?** **Yes** — 50 source
  documents × 16 sentences = 800 items; 4,800 real NLLB translations across six
  conditions (ko/hi/zh/ar/de + round-trip); an edited-text tamper corpus (800
  edited sources, 4,800 translations) and its LLM rewording (800 sentences,
  2,400 translations); the same-text run (50 documents, 800 sentences, three
  variants); paraphrase/adaptive corpora sizes and seeds are stated per
  experiment.

## C. Computational experiments

- **C1. Did you report the number of parameters and compute budget?**
  **Partly.** The translation model is NLLB-200-distilled-600M (~600M params);
  the neural-frontend extractors are named instruction LLMs (GPT-4o-mini,
  Llama-3.3-70B). The method's own cryptographic/coding core is parameter-free;
  end-to-end latency is explicitly stated as unmeasured (Appendix, Complexity).
  No model is trained. Measured on four CPU threads: rebuilding the 4,800 NLLB
  outputs ~30 min; the edited-text tamper corpus ~22 min; the same-text run
  ~1.5 h for 30 documents (55 min generation, 36 min translation) plus ~48 min
  to extend it to 50; the LLM-reworded tamper run ~20 min for 30 documents plus
  ~9 min to extend it to 50; scoring scripts minutes (appendix "Models, Data, and
  Licenses"). The original NLLB/KGW Kaggle GPU runs and the API neural-parser
  runs did not record wall-clock time; state that if the form asks.
- **C2. Did you report the experimental setup and hyperparameters?** **Yes** —
  KGW γ=0.25, δ=2.0; contracts core6/robust7/full9; τ=32-bit tags; matched 1%
  FPR calibration; seeds fixed; full protocol in Appendix (Extended Evaluation
  Protocol).
- **C3. Did you report descriptive statistics (e.g., CIs, multiple runs)?**
  **Yes** — Wilson 95% confidence intervals throughout; seeded determinism; the
  contract-collision false-positive floor is derived and matched to measured
  values.
- **C4. Did you use existing packages, and report versions/settings?**
  **Yes** — NLLB-200-distilled-600M, Qwen2.5-0.5B-Instruct, model2vec and
  sentence-transformers encoders, OpenAI-compatible API backends; the CPU
  rebuilds used `torch` 2.14.1 and `transformers` 5.20.2 (stated in the
  appendix).

## D. Human annotators / crowdsourcing

- **Not applicable.** No human annotators, crowdsourcing, or human subjects were
  used; all data are synthetic template facts and their machine translations.
  (Any future scaled evaluation adding human factual-equivalence annotation must
  use licensed/consented text and compensated, documented annotation — stated in
  §Ethical Considerations.)

## E. Notes for the author before submitting

1. Confirm A4 (AI-assistant disclosure) in the venue's exact wording.
2. B2/B3/C4 are now answered in the appendix; check the wording against the
   venue form.
3. C1: the CPU times are measured; the original Kaggle GPU and API runs were not
   timed, so answer "not recorded" for those if asked.
4. The *Limitations* section is present and unnumbered; the 8-page body excludes
   it, the references, and the appendices, per ACL policy.
