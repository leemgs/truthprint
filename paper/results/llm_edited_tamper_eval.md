# Tamper test with free LLM wording (edited fact, reworded, translated)

800 sentences (50 documents), each with one field edited, reworded once by `Qwen/Qwen2.5-0.5B-Instruct` (same prompt as the same-text run, no resampling), translated by `facebook/nllb-200-distilled-600M` into ko/ar/de. Verified against the tag of the *original* source (id-addressed). `accepted` on an in-contract edit is a false accept; `reads edit` = the re-extracted record equals the edited one. Wilson 95% CI.

## Contract `core6`

| Edit | Condition | n | Accepted | Reads edit |
|---|---|---|---|---|
| in contract | clean | 500 | 0.008 [0.003,0.020] | 0.596 [0.552,0.638] |
| in contract | ko | 500 | 0.008 [0.003,0.020] | 0.350 [0.309,0.393] |
| in contract | ar | 500 | 0.022 [0.012,0.039] | 0.364 [0.323,0.407] |
| in contract | de | 500 | 0.004 [0.001,0.014] | 0.540 [0.496,0.583] |
| in contract | translated | 1500 | 0.011 [0.007,0.018] | 0.418 [0.393,0.443] |
| outside contract | clean | 300 | 0.597 [0.540,0.651] | 0.597 [0.540,0.651] |
| outside contract | ko | 300 | 0.330 [0.279,0.385] | 0.330 [0.279,0.385] |
| outside contract | ar | 300 | 0.353 [0.301,0.409] | 0.353 [0.301,0.409] |
| outside contract | de | 300 | 0.530 [0.474,0.586] | 0.530 [0.474,0.586] |
| outside contract | translated | 900 | 0.404 [0.373,0.437] | 0.404 [0.373,0.437] |

Per edited field, translated conditions pooled:

| Field | In contract | n | Accepted | Reads edit |
|---|---|---|---|---|
| agent | yes | 300 | 0.000 [0.000,0.013] | 0.380 [0.327,0.436] |
| attribution | yes | 300 | 0.023 [0.011,0.047] | 0.390 [0.337,0.446] |
| causation | no | 300 | 0.417 [0.362,0.473] | 0.417 [0.362,0.473] |
| modality | no | 300 | 0.373 [0.321,0.429] | 0.373 [0.321,0.429] |
| patient | no | 300 | 0.423 [0.369,0.480] | 0.423 [0.369,0.480] |
| polarity | yes | 300 | 0.017 [0.007,0.038] | 0.427 [0.372,0.483] |
| quantity | yes | 300 | 0.017 [0.007,0.038] | 0.433 [0.378,0.490] |
| time_dir | yes | 300 | 0.000 [0.000,0.013] | 0.460 [0.404,0.517] |

## Contract `full9`

| Edit | Condition | n | Accepted | Reads edit |
|---|---|---|---|---|
| in contract | clean | 800 | 0.007 [0.003,0.016] | 0.499 [0.464,0.533] |
| in contract | ko | 800 | 0.010 [0.005,0.020] | 0.228 [0.200,0.258] |
| in contract | ar | 800 | 0.004 [0.001,0.011] | 0.065 [0.050,0.084] |
| in contract | de | 800 | 0.010 [0.005,0.020] | 0.366 [0.334,0.400] |
| in contract | translated | 2400 | 0.008 [0.005,0.012] | 0.220 [0.203,0.237] |

Per edited field, translated conditions pooled:

| Field | In contract | n | Accepted | Reads edit |
|---|---|---|---|---|
| agent | yes | 300 | 0.000 [0.000,0.013] | 0.190 [0.150,0.238] |
| attribution | yes | 300 | 0.007 [0.002,0.024] | 0.227 [0.183,0.277] |
| causation | yes | 300 | 0.010 [0.003,0.029] | 0.233 [0.189,0.284] |
| modality | yes | 300 | 0.030 [0.016,0.056] | 0.173 [0.135,0.220] |
| patient | yes | 300 | 0.000 [0.000,0.013] | 0.243 [0.198,0.295] |
| polarity | yes | 300 | 0.007 [0.002,0.024] | 0.210 [0.168,0.260] |
| quantity | yes | 300 | 0.010 [0.003,0.029] | 0.233 [0.189,0.284] |
| time_dir | yes | 300 | 0.000 [0.000,0.013] | 0.247 [0.201,0.298] |
