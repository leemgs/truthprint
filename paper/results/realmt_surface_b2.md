# Surface-carrier parse coverage on the committed real-MT run (4,800 NLLB outputs)

- transformations: 4800
- Metric: fraction of transformed sentences the closed-domain frontend
  can actually parse (a carrier is unrecoverable if its text cannot be
  read). This is measured from the real translation output, not asserted
  by annotation.

| Condition | Frontend parse coverage (95% CI) | parseable/total |
|---|---|---|
| ar | 0.000 [0.000, 0.005] | 0/800 |
| de | 0.000 [0.000, 0.005] | 0/800 |
| hi | 0.000 [0.000, 0.005] | 0/800 |
| ko | 0.000 [0.000, 0.005] | 0/800 |
| rt | 0.001 [0.000, 0.007] | 1/800 |
| zh | 0.000 [0.000, 0.005] | 0/800 |
| **all** | **0.000 [0.000, 0.001]** | |

> Carrier recovery requires the frontend to read the transformed text. 0% parse coverage means the closed-domain Stage-1 frontend cannot recover any carrier from real MT output, so payload recovery is impossible without a wide-coverage semantic frontend.

Control: the same Stage-1 parser reads 800/800 English source sentences before translation.
