# Same-text comparison: token watermarks vs Truthprint on one LLM's output

Generator `Qwen/Qwen2.5-0.5B-Instruct` (CPU) rewords the source facts of 30 committed documents (480 sentences) in three variants (unwatermarked, KGW, SynthID-Text); translator `facebook/nllb-200-distilled-600M`. Detection per 16-sentence document. Token watermarks: TPR above the maximum unwatermarked score (empirical FPR 0 over the null documents) and ROC-AUC; Truthprint: document attribution against the registered facts (>= 50% of sentences), id-free false attributions.

Truthprint validated realizations (Stage-2 reads back the core6 record within the try budget): 0.871 [0.838,0.898]

| Condition | KGW TPR (> max null) | KGW AUC | SynthID TPR (> max null) | SynthID AUC | Truthprint doc attribution | Truthprint sentence auth | Truthprint docs w/ false attribution |
|---|---|---|---|---|---|---|---|
| clean | 0.933 [0.787,0.982] | 0.998 | 0.267 [0.142,0.444] | 0.881 | 1.000 [0.886,1.000] | 0.871 [0.838,0.898] | 0.000 [0.000,0.114] |
| ko | 0.100 [0.035,0.256] | 0.609 | 0.000 [0.000,0.114] | 0.672 | 0.633 [0.455,0.781] | 0.508 [0.464,0.553] | 0.000 [0.000,0.114] |
| ar | 0.000 [0.000,0.114] | 0.527 | 0.133 [0.053,0.297] | 0.529 | 0.667 [0.488,0.808] | 0.500 [0.455,0.545] | 0.000 [0.000,0.114] |
| de | 0.033 [0.006,0.167] | 0.631 | 0.000 [0.000,0.114] | 0.499 | 0.967 [0.833,0.994] | 0.731 [0.690,0.769] | 0.000 [0.000,0.114] |
