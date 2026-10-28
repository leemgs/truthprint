# Same-text fact fidelity (extractor-based proxy)

Proxy: Stage-2 extractor reads back the source core6 record (clean English); 480 sentences per variant; Wilson 95% CI. A mismatch may be a dropped fact or unread wording; no human judgment.

| Variant | core6 read back |
|---|---|
| Unwatermarked, first sample | 0.590 [0.545,0.633] |
| KGW | 0.463 [0.418,0.507] |
| SynthID-Text | 0.504 [0.460,0.549] |
| Truthprint (validated, up to 4 draws) | 0.896 [0.865,0.920] |

Truthprint draws per sentence: mean 1.79, histogram {'1': 283, '2': 90, '3': 33, '4': 74}; 50 sentences had no valid realization.
