# Same-text control, Truthprint on its first sample only

800 sentences; the 207 accepted at draw 2-4 are scored on their stored first sample, translated with the same NLLB settings. Same budget as the token watermarks (one sample). Wilson 95% CI.

| Condition | Document attribution | Sentence authentication | Docs w/ false attribution |
|---|---|---|---|
| clean | 0.940 [0.838,0.979] | 0.609 [0.574,0.642] | 0.000 [0.000,0.071] |
| ko | 0.160 [0.083,0.285] | 0.349 [0.317,0.382] | 0.000 [0.000,0.071] |
| ar | 0.180 [0.098,0.308] | 0.351 [0.319,0.385] | 0.000 [0.000,0.071] |
| de | 0.660 [0.522,0.776] | 0.516 [0.482,0.551] | 0.000 [0.000,0.071] |
