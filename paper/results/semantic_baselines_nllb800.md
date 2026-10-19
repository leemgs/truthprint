# Matched-FPR semantic/robust-hash baselines on real MT (W2/W3, Tasks 2-4)

All methods run in-repo on cached **real** LLM-MT translations (800 base items x 6 conditions) with a real multilingual embedding backend (`minishlab/potion-multilingual-128M`). TPR is reported at a **common 1% FPR** calibrated per method on a null (unrelated-content) population over 300 bootstrap documents of 16 sentences (seed 20270101). Wilson 95% CI.

## TPR at matched 1% FPR, per translation condition

| Method | rt | ko | hi | zh | ar | de |
|---|---|---|---|---|---|---|
| meaning-digest | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| SemStamp | 0.423 | 0.027 | 0.077 | 0.040 | 0.010 | 0.020 |
| SimHash-hash | 0.973 | 0.587 | 0.560 | 0.767 | 0.050 | 0.500 |
| MinHash-hash | 0.753 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| exact-hash | 0.020 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

> `rt` = English round-trip; `ko/hi/zh/ar` = direct translation. SemStamp (embedding region) survives round-trip but degrades cross-lingually as embedding buckets drift; surface/token hashes collapse under translation; the typed meaning-digest survives cross-lingually. All at the same FPR.

## Tamper rejection: single-field meaning-altering edit (closed domain)

Fraction of single-field tampers correctly REJECTED (n=200 minimal pairs). A similarity/hash gate cannot localize a typed field change; the typed contract can.

| Method | Tamper-rejection (95% CI) |
|---|---|
| meaning-digest | 1.000 [0.981, 1.000] |
| SimHash-hash | 0.000 [0.000, 0.019] |
| MinHash-hash | 0.000 [0.000, 0.019] |
| exact-hash | 1.000 [0.981, 1.000] |
