# Real head-to-head baseline comparison on real MT (W4)

Produced by `handoff/Truthprint_W4_Baselines_Kaggle.ipynb` on Kaggle GPU and
scored with `code/scripts/eval_baselines_real.py`. A self-contained KGW token
watermark (Kirchenbauer 2023) is embedded during generation via logit biasing,
the output is machine-translated by real NLLB-200-distilled-600M into six
conditions, and each method is detected on the translated text. TPR is reported
at a 1% FPR threshold calibrated per method on its null (unwatermarked)
population. Truthprint's meaning-digest scheme is shown at its own measured
operating point (contract-collision floor, not a tunable threshold). This is the
real-data replacement for the diagnostic simulator, which must not be used to
rank methods.

| Method | clean | EN round-trip | EN->KO | EN->HI | EN->ZH | EN->AR | EN->DE |
|---|---|---|---|---|---|---|---|
| KGW | 0.960 | 0.380 | 0.040 | 0.040 | 0.020 | 0.000 | 0.080 |
| Truthprint (meaning-digest, core6): document attribution | --- | 0.980 | 0.940 | 1.000 | 0.940 | 0.900 | 1.000 |
| Truthprint (meaning-digest, core6): sentence TPR | --- | 0.723 | 0.682 | 0.886 | 0.666 | 0.618 | 0.850 |

_Source text differs between rows:_ KGW is scored per generated document on gpt2
free-form generations (Kaggle run; its raw detector scores are not committed,
only `handoff/samples/05_baseline_outputs.jsonl` documents the schema), while the
Truthprint rows are the committed core6 results in `provenance_realmt.json` on the
template-fact corpus. Both are translated by the same NLLB system. The Truthprint
rows were refreshed from that file; an earlier version of this table carried
pre-B2 figures (0.502-0.980) that the committed run does not reproduce.

_Implementations:_ **KGW**: self-contained KGW (Kirchenbauer 2023), gamma=0.25
delta=2.0, LLM=gpt2, NLLB=distilled-600M; **Truthprint (meaning-digest, core6)**:
meaning-digest provenance; operating FP = contract-collision floor (~5e-3 core6),
not a 1% threshold.

Finding: the token watermark detects on clean text (0.960) but its signal is
destroyed by real translation (0.000-0.380 across the six conditions), while the
meaning-digest scheme attributes translated documents at 0.900-1.000
(sentence-level TPR 0.618-0.886). This confirms with a real token
watermark and real MT what the paper's surface-carrier pilot showed as 0/192,
and what He et al. (2024) reported for cross-lingual token-watermark removal.

Caveats: a single token baseline (KGW; SynthID/SIR via MarkLLM are an optional
block and not included here), a small gpt2 generator, a closed-domain source,
and one MT system; Arabic is weakest for the meaning-digest scheme too (sentence
TPR 0.618, document attribution 0.900),
consistent with the extractor's Arabic entity variability reported in Stage-2.
