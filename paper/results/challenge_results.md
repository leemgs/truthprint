# Field-level semantic challenge set (Stage-1, closed domain)

Real, fully-offline experiment on actual sentence strings (standard library only, no neural model, no network). Regenerate with `python3 scripts/eval_challenge.py`.

- Documents: 300 x 24 facts; code `[48, 24]` GF(2) (rate 0.50).
- Payload: 8-bit message + 16-bit tag. Benign transform erases 25% of carriers (meaning preserved).
- Embedding gate calibrated to <= 5% benign false-reject: theta* = 0.8891 (bag-of-words cosine).
- CIs: Wilson (rates), bootstrap (2000 resamples, mean cosine). Seed 20270101.

## Benign (meaning-preserving) behavior

| Quantity | Value (95% CI) |
|---|---|
| Truthprint attribution retained | 0.990 [0.971, 0.997] |
| Embedding gate false-reject | 0.018 [0.015, 0.022] |
| Mean paraphrase cosine | 0.953 [0.953, 0.954] |

## Tamper detection by protected field

| Field | Truthprint (typed) | No-MAC (decode-only) | Embedding gate | Mean tamper cosine | Threshold-inversion |
|---|---|---|---|---|---|
| polarity | 1.000 [0.987, 1.000] | 0.000 [0.000, 0.013] | 0.020 [0.009, 0.043] | 0.973 [0.970, 0.976] | 0.947 [0.915, 0.967] |
| quantity | 1.000 [0.987, 1.000] | 0.000 [0.000, 0.013] | 0.023 [0.011, 0.047] | 0.950 [0.947, 0.952] | 0.363 [0.311, 0.419] |
| time_dir | 1.000 [0.987, 1.000] | 0.000 [0.000, 0.013] | 0.000 [0.000, 0.013] | 0.962 [0.961, 0.963] | 0.573 [0.517, 0.628] |
| modality | 1.000 [0.987, 1.000] | 0.000 [0.000, 0.013] | 0.027 [0.014, 0.052] | 0.951 [0.948, 0.954] | 0.617 [0.561, 0.670] |
| attribution | 1.000 [0.987, 1.000] | 0.000 [0.000, 0.013] | 0.000 [0.000, 0.013] | 0.951 [0.948, 0.953] | 0.273 [0.226, 0.326] |
| causation | 1.000 [0.987, 1.000] | 0.000 [0.000, 0.013] | 0.000 [0.000, 0.013] | 0.939 [0.937, 0.940] | 0.143 [0.108, 0.188] |
| **all fields** | **1.000 [0.998, 1.000]** | **0.000 [0.000, 0.002]** | **0.012 [0.008, 0.018]** | --- | **0.486 [0.463, 0.509]** |

## Reading the result

- The typed invariant + MAC contract detects every single-field meaning-altering edit while retaining attribution across legitimate paraphrases.
- Removing the h_I-bound MAC (decode-only) drops tamper-detection to zero: the carriers still recover, so the MAC binding is the load-bearing component for tamper resistance.
- An embedding-similarity gate calibrated to keep legitimate paraphrases catches almost no tamper, because a single-field edit is lexically smaller than a legitimate voice/time reflow. The threshold-inversion rate quantifies why: for a large fraction of cases the tamper is at least as similar as the paraphrase, so no threshold can separate them.

This is a Stage-1 closed-domain demonstration, not a wide-coverage multilingual parser; it isolates the contract property, not neural frontend accuracy.
