# Edited-text tamper under real translation

800 source sentences, each with one field edited in the text and re-realized with the same template; 4800 NLLB translations (5 languages + Korean round trip). The verifier authenticates against the tag registered for the *unedited* source (id-addressed, 32-bit keyed tag). `accepted` for an in-contract field is a false accept; `reads edit` is the share whose re-extracted record equals the edited one (the rejection is caused by seeing the edit, not by an extraction failure). Wilson 95% CI.

## Contract `core6`

False accept over in-contract edits: **0.002 [0.001,0.005]** (n=3000); edit read back: 0.742 [0.726,0.757].
Accepted when the edit is outside the contract (by design): 0.751 [0.730,0.770] (n=1800).

| Edited field | In contract | n | Accepted | Reads edit |
|---|---|---|---|---|
| agent | yes | 600 | 0.000 [0.000,0.006] | 0.737 [0.700,0.770] |
| attribution | yes | 600 | 0.003 [0.001,0.012] | 0.732 [0.695,0.766] |
| causation | no | 600 | 0.768 [0.733,0.800] | 0.768 [0.733,0.800] |
| modality | no | 600 | 0.748 [0.712,0.781] | 0.748 [0.712,0.781] |
| patient | no | 600 | 0.735 [0.698,0.769] | 0.735 [0.698,0.769] |
| polarity | yes | 600 | 0.007 [0.003,0.017] | 0.762 [0.726,0.794] |
| quantity | yes | 600 | 0.002 [0.000,0.009] | 0.705 [0.667,0.740] |
| time_dir | yes | 600 | 0.000 [0.000,0.006] | 0.773 [0.738,0.805] |

False accept (in-contract edits) by condition: ar 0.006; de 0.000; hi 0.000; ko 0.002; rt 0.006; zh 0.000

## Contract `full9`

False accept over in-contract edits: **0.009 [0.007,0.013]** (n=4800); edit read back: 0.458 [0.443,0.472].

| Edited field | In contract | n | Accepted | Reads edit |
|---|---|---|---|---|
| agent | yes | 600 | 0.000 [0.000,0.006] | 0.442 [0.402,0.482] |
| attribution | yes | 600 | 0.002 [0.000,0.009] | 0.447 [0.407,0.487] |
| causation | yes | 600 | 0.045 [0.031,0.065] | 0.472 [0.432,0.512] |
| modality | yes | 600 | 0.023 [0.014,0.039] | 0.450 [0.411,0.490] |
| patient | yes | 600 | 0.000 [0.000,0.006] | 0.457 [0.417,0.497] |
| polarity | yes | 600 | 0.003 [0.001,0.012] | 0.473 [0.434,0.513] |
| quantity | yes | 600 | 0.002 [0.000,0.009] | 0.447 [0.407,0.487] |
| time_dir | yes | 600 | 0.000 [0.000,0.006] | 0.473 [0.434,0.513] |

False accept (in-contract edits) by condition: ar 0.003; de 0.009; hi 0.005; ko 0.013; rt 0.019; zh 0.009
