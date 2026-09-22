# Stage-2 multilingual invariant extractor on real MT output

Field-level recovery of the typed invariants from **real** NLLB translations, per condition (ko/hi = direct translation; rt = round-trip English). Wilson 95% CIs. Contrast: the Stage-1 surface parser recovers 0/192 (Section real-MT pilot).

## Aggregate field recovery (all conditions)

| Field | Recovery (95% CI) | |
|---|---|---|
| agent | 0.984 [0.955, 0.995] | `####################` |
| patient | 0.958 [0.920, 0.979] | `###################.` |
| predicate | 0.948 [0.907, 0.971] | `###################.` |
| polarity | 0.943 [0.900, 0.968] | `###################.` |
| quantity | 0.979 [0.948, 0.992] | `####################` |
| time_dir | 1.000 [0.980, 1.000] | `####################` |
| modality | 0.901 [0.851, 0.936] | `##################..` |
| attribution | 0.995 [0.971, 0.999] | `####################` |
| causation | 0.891 [0.839, 0.927] | `##################..` |

## Per-condition detail

| Condition (lang) | agent | patient | predicate | polarity | quantity | time_dir | modality | attribution | causation | all-exact |
|---|---|---|---|---|---|---|---|---|---|---|
| hi (hi) | 0.97 | 0.97 | 0.98 | 1.00 | 1.00 | 1.00 | 0.91 | 1.00 | 0.89 | 0.73 |
| ko (ko) | 0.98 | 0.98 | 0.91 | 0.92 | 0.95 | 1.00 | 0.91 | 1.00 | 0.88 | 0.62 |
| rt (en) | 1.00 | 0.92 | 0.95 | 0.91 | 0.98 | 1.00 | 0.89 | 0.98 | 0.91 | 0.69 |

> Meaning-layer fields (polarity, quantity, temporal direction, attribution, causation, modality) survive real translation and are recoverable by a lexicon-level semantic frontend; entities a translator renders inconsistently (e.g. config drift) are recovered less reliably. This is a closed-domain Stage-2 result, not a wide-coverage parser.
