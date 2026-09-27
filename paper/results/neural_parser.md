# Neural vs lexicon invariant extractor on real MT (W5)

96 sentences. Field recovery = prediction equals gold after canonical normalization (Wilson 95% CI). The lexicon column is the in-repo Stage-2 extractor run on the same text, so the neural frontend is measured head-to-head against it.

## Per-field recovery

| Field | Neural | Lexicon |
|---|---|---|
| agent | 0.094 [0.050,0.169] | 0.625 [0.525,0.715] |
| patient | 0.177 [0.114,0.265] | 0.604 [0.504,0.696] |
| predicate | 0.896 [0.819,0.942] | 0.625 [0.525,0.715] |
| polarity | 0.979 [0.927,0.994] | 0.990 [0.943,0.998] |
| quantity | 0.500 [0.402,0.598] | 0.917 [0.844,0.957] |
| time_dir | 0.688 [0.589,0.771] | 0.625 [0.525,0.715] |
| modality | 0.938 [0.870,0.971] | 0.896 [0.819,0.942] |
| attribution | 0.938 [0.870,0.971] | 0.885 [0.806,0.935] |
| causation | 0.948 [0.884,0.978] | 0.917 [0.844,0.957] |
| **all-exact** | **0.000** [0.000,0.038] | **0.479** [0.382,0.578] |

## By domain (field-level recovery)

| Domain | Neural | Lexicon |
|---|---|---|
| template | 0.726 [0.687,0.762] | 0.970 [0.952,0.982] |
| open | 0.614 [0.560,0.666] | 0.481 [0.428,0.536] |

The decisive W5 result is the `open` (or non-template) domain row: the lexicon abstains or misreads out-of-vocabulary wording, so a neural frontend that holds up there is the wide-coverage parser the paper listed as the next step.
