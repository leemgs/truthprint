# Same-text control, Truthprint on its first sample only

480 sentences; the 122 accepted at draw 2-4 are scored on their stored first sample, translated with the same NLLB settings. Same budget as the token watermarks (one sample). Wilson 95% CI.

| Condition | Document attribution | Sentence authentication | Docs w/ false attribution |
|---|---|---|---|
| clean | 0.967 [0.833,0.994] | 0.617 [0.572,0.659] | 0.000 [0.000,0.114] |
| ko | 0.167 [0.073,0.336] | 0.365 [0.323,0.409] | 0.000 [0.000,0.114] |
| ar | 0.200 [0.095,0.373] | 0.365 [0.323,0.409] | 0.000 [0.000,0.114] |
| de | 0.700 [0.521,0.833] | 0.523 [0.478,0.567] | 0.000 [0.000,0.114] |
