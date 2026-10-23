# Same-text comparison: token watermarks vs Truthprint on one LLM's output

Generator `Qwen/Qwen2.5-0.5B-Instruct` (CPU) rewords the source facts of 30 committed documents (480 sentences) in three variants (unwatermarked, KGW, SynthID-Text); translator `facebook/nllb-200-distilled-600M`. Detection per 16-sentence document. Token watermarks: TPR above the maximum unwatermarked score (empirical FPR 0 over the null documents) and ROC-AUC; Truthprint: document attribution against the registered facts (>= 50% of sentences), id-free false attributions.

Truthprint validated realizations (Stage-2 reads back the core6 record within the try budget): 0.896 [0.865,0.920]

| Condition | KGW TPR (> max null) | KGW AUC | SynthID TPR (> max null) | SynthID AUC | Truthprint doc attribution | Truthprint sentence auth | Truthprint docs w/ false attribution |
|---|---|---|---|---|---|---|---|
| clean | 1.000 [0.886,1.000] | 1.000 | 0.567 [0.392,0.726] | 0.939 | 1.000 [0.886,1.000] | 0.896 [0.865,0.920] | 0.000 [0.000,0.114] |
| ko | 0.067 [0.018,0.213] | 0.614 | 0.067 [0.018,0.213] | 0.674 | 0.700 [0.521,0.833] | 0.471 [0.427,0.516] | 0.000 [0.000,0.114] |
| ar | 0.000 [0.000,0.114] | 0.521 | 0.000 [0.000,0.114] | 0.640 | 0.567 [0.392,0.726] | 0.477 [0.433,0.522] | 0.000 [0.000,0.114] |
| de | 0.033 [0.006,0.167] | 0.578 | 0.000 [0.000,0.114] | 0.477 | 1.000 [0.886,1.000] | 0.756 [0.716,0.793] | 0.000 [0.000,0.114] |
