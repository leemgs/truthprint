# Same-text comparison: token watermarks vs Truthprint on one LLM's output

Generator `Qwen/Qwen2.5-0.5B-Instruct` (CPU) rewords the source facts of 50 committed documents (800 sentences) in three variants (unwatermarked, KGW, SynthID-Text); translator `facebook/nllb-200-distilled-600M`. Detection per 16-sentence document. Token watermarks: TPR above the maximum unwatermarked score (empirical FPR 0 over the null documents) and ROC-AUC; Truthprint: document attribution against the registered facts (>= 50% of sentences), id-free false attributions.

Truthprint validated realizations (Stage-2 reads back the core6 record within the try budget): 0.868 [0.842,0.889]

| Condition | KGW TPR (> max null) | KGW AUC | SynthID TPR (> max null) | SynthID AUC | Truthprint doc attribution | Truthprint sentence auth | Truthprint docs w/ false attribution |
|---|---|---|---|---|---|---|---|
| clean | 0.920 [0.812,0.968] | 0.998 | 0.200 [0.112,0.330] | 0.870 | 1.000 [0.929,1.000] | 0.868 [0.842,0.889] | 0.000 [0.000,0.071] |
| ko | 0.040 [0.011,0.135] | 0.607 | 0.000 [0.000,0.071] | 0.697 | 0.580 [0.442,0.706] | 0.481 [0.447,0.516] | 0.000 [0.000,0.071] |
| ar | 0.040 [0.011,0.135] | 0.545 | 0.140 [0.070,0.262] | 0.533 | 0.580 [0.442,0.706] | 0.470 [0.436,0.505] | 0.000 [0.000,0.071] |
| de | 0.080 [0.032,0.188] | 0.631 | 0.000 [0.000,0.071] | 0.500 | 0.960 [0.865,0.989] | 0.716 [0.684,0.746] | 0.000 [0.000,0.071] |
