# Tamper test with free LLM wording (edited fact, reworded, translated)

480 sentences (30 documents), each with one field edited, reworded once by `Qwen/Qwen2.5-0.5B-Instruct` (same prompt as the same-text run, no resampling), translated by `facebook/nllb-200-distilled-600M` into ko/ar/de. Verified against the tag of the *original* source (id-addressed). `accepted` on an in-contract edit is a false accept; `reads edit` = the re-extracted record equals the edited one. Wilson 95% CI.

## Contract `core6`

| Edit | Condition | n | Accepted | Reads edit |
|---|---|---|---|---|
| in contract | clean | 300 | 0.010 [0.003,0.029] | 0.587 [0.530,0.641] |
| in contract | ko | 300 | 0.010 [0.003,0.029] | 0.357 [0.305,0.412] |
| in contract | ar | 300 | 0.030 [0.016,0.056] | 0.363 [0.311,0.419] |
| in contract | de | 300 | 0.007 [0.002,0.024] | 0.533 [0.477,0.589] |
| in contract | translated | 900 | 0.016 [0.009,0.026] | 0.418 [0.386,0.450] |
| outside contract | clean | 180 | 0.567 [0.494,0.637] | 0.567 [0.494,0.637] |
| outside contract | ko | 180 | 0.339 [0.274,0.411] | 0.339 [0.274,0.411] |
| outside contract | ar | 180 | 0.317 [0.253,0.388] | 0.317 [0.253,0.388] |
| outside contract | de | 180 | 0.517 [0.444,0.589] | 0.517 [0.444,0.589] |
| outside contract | translated | 540 | 0.391 [0.350,0.433] | 0.391 [0.350,0.433] |

Per edited field, translated conditions pooled:

| Field | In contract | n | Accepted | Reads edit |
|---|---|---|---|---|
| agent | yes | 180 | 0.000 [0.000,0.021] | 0.378 [0.310,0.450] |
| attribution | yes | 180 | 0.033 [0.015,0.071] | 0.433 [0.363,0.506] |
| causation | no | 180 | 0.439 [0.368,0.512] | 0.439 [0.368,0.512] |
| modality | no | 180 | 0.300 [0.238,0.371] | 0.300 [0.238,0.371] |
| patient | no | 180 | 0.433 [0.363,0.506] | 0.433 [0.363,0.506] |
| polarity | yes | 180 | 0.028 [0.012,0.063] | 0.383 [0.315,0.456] |
| quantity | yes | 180 | 0.017 [0.006,0.048] | 0.444 [0.374,0.517] |
| time_dir | yes | 180 | 0.000 [0.000,0.021] | 0.450 [0.379,0.523] |

## Contract `full9`

| Edit | Condition | n | Accepted | Reads edit |
|---|---|---|---|---|
| in contract | clean | 480 | 0.008 [0.003,0.021] | 0.490 [0.445,0.534] |
| in contract | ko | 480 | 0.010 [0.004,0.024] | 0.242 [0.206,0.282] |
| in contract | ar | 480 | 0.002 [0.000,0.012] | 0.069 [0.049,0.095] |
| in contract | de | 480 | 0.010 [0.004,0.024] | 0.367 [0.325,0.411] |
| in contract | translated | 1440 | 0.008 [0.004,0.014] | 0.226 [0.205,0.248] |

Per edited field, translated conditions pooled:

| Field | In contract | n | Accepted | Reads edit |
|---|---|---|---|---|
| agent | yes | 180 | 0.000 [0.000,0.021] | 0.189 [0.138,0.252] |
| attribution | yes | 180 | 0.011 [0.003,0.040] | 0.233 [0.178,0.300] |
| causation | yes | 180 | 0.006 [0.001,0.031] | 0.233 [0.178,0.300] |
| modality | yes | 180 | 0.028 [0.012,0.063] | 0.144 [0.101,0.203] |
| patient | yes | 180 | 0.000 [0.000,0.021] | 0.256 [0.197,0.324] |
| polarity | yes | 180 | 0.011 [0.003,0.040] | 0.228 [0.173,0.294] |
| quantity | yes | 180 | 0.006 [0.001,0.031] | 0.239 [0.182,0.306] |
| time_dir | yes | 180 | 0.000 [0.000,0.021] | 0.283 [0.223,0.353] |
