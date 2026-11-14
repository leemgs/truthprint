# Same-text fact fidelity (extractor-based proxy)

Proxy: Stage-2 extractor reads back the source core6 record (clean English); 800 sentences per variant; Wilson 95% CI. A mismatch may be a dropped fact or unread wording; no human judgment.

| Variant | core6 read back |
|---|---|
| Unwatermarked, first sample | 0.609 [0.574,0.642] |
| KGW | 0.504 [0.469,0.538] |
| SynthID-Text | 0.517 [0.483,0.552] |
| Truthprint (validated, up to 4 draws) | 0.868 [0.842,0.889] |

Truthprint draws per sentence: mean 1.80, histogram {'1': 487, '2': 124, '3': 51, '4': 138}; 106 sentences had no valid realization.
