# Same-text fluency proxy (perplexity under GPT-2)

800 clean English sentences per variant, scored by `openai-community/gpt2` (not the generator). Geometric-mean perplexity with a 95% CI, and the paired mean difference in log-perplexity to the unwatermarked first sample (> 0 means less predictable wording). An automatic proxy, not a human quality judgment.

| Variant | Perplexity (95% CI) | Δ log-PPL vs. first sample (95% CI) |
|---|---|---|
| Unwatermarked, first sample | 95.6 [91.9,99.4] | +0.000 [+0.000,+0.000] |
| KGW | 84.4 [81.4,87.6] | -0.124 [-0.161,-0.087] |
| SynthID-Text | 107.7 [103.5,112.0] | +0.119 [+0.086,+0.152] |
| Truthprint (validated) | 87.3 [84.1,90.8] | -0.090 [-0.109,-0.071] |
