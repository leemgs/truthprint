# Stage-2 multilingual invariant extractor on real MT output

Field-level recovery of the typed invariants from **real** NLLB translations, per condition (ko/hi = direct translation; rt = round-trip English). Wilson 95% CIs. Contrast: the Stage-1 surface parser recovers 0/192 (Section real-MT pilot).

## Aggregate field recovery (all conditions)

| Field | Recovery (95% CI) | |
|---|---|---|
| agent | 0.996 [0.989, 0.998] | `####################` |
| patient | 0.906 [0.886, 0.923] | `##################..` |
| predicate | 0.963 [0.949, 0.973] | `###################.` |
| polarity | 0.990 [0.981, 0.994] | `####################` |
| quantity | 0.978 [0.967, 0.986] | `####################` |
| time_dir | 0.997 [0.991, 0.999] | `####################` |
| modality | 0.901 [0.881, 0.918] | `##################..` |
| attribution | 0.971 [0.958, 0.980] | `###################.` |
| causation | 0.972 [0.959, 0.981] | `###################.` |

## Per-condition detail

| Condition (lang) | agent | patient | predicate | polarity | quantity | time_dir | modality | attribution | causation | all-exact |
|---|---|---|---|---|---|---|---|---|---|---|
| ar (ar) | 0.98 | 0.54 | 0.89 | 1.00 | 0.88 | 1.00 | 0.99 | 0.84 | 0.99 | 0.34 |
| de (de) | 1.00 | 1.00 | 0.97 | 1.00 | 1.00 | 1.00 | 0.81 | 1.00 | 1.00 | 0.80 |
| hi (hi) | 0.99 | 1.00 | 0.97 | 0.97 | 1.00 | 1.00 | 0.99 | 1.00 | 0.92 | 0.88 |
| ko (ko) | 1.00 | 1.00 | 0.98 | 1.00 | 0.99 | 1.00 | 0.89 | 1.00 | 0.99 | 0.86 |
| rt (en) | 1.00 | 0.94 | 0.99 | 0.97 | 1.00 | 0.98 | 0.84 | 0.98 | 0.94 | 0.74 |
| zh (zh) | 1.00 | 0.96 | 0.96 | 0.99 | 1.00 | 1.00 | 0.88 | 1.00 | 1.00 | 0.81 |

> Meaning-layer fields (polarity, quantity, temporal direction, attribution, causation, modality) survive real translation and are recoverable by a lexicon-level semantic frontend; entities a translator renders inconsistently (e.g. config drift) are recovered less reliably. This is a closed-domain Stage-2 result, not a wide-coverage parser.
