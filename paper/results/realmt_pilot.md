# Real-MT pilot — objective frontend measurement

- transformations: 192
- Metric: fraction of transformed sentences the closed-domain frontend
  can actually parse (a carrier is unrecoverable if its text cannot be
  read). This is measured from the real translation output, not asserted
  by annotation.

| Condition | Frontend parse coverage (95% CI) | parseable/total |
|---|---|---|
| hi | 0.000 [0.000, 0.057] | 0/64 |
| ko | 0.000 [0.000, 0.057] | 0/64 |
| rt | 0.000 [0.000, 0.057] | 0/64 |
| **all** | **0.000 [0.000, 0.020]** | |

> Carrier recovery requires the frontend to read the transformed text. 0% parse coverage means the closed-domain Stage-1 frontend cannot recover any carrier from real MT output, so payload recovery is impossible without a wide-coverage semantic frontend.
