# ACL/ARR submission source

`acl_main.tex` is the anonymous ACL/ARR-format draft. It intentionally retains
all Stage-1 qualifications from `main.tex`; the diagnostic simulation is not an
end-to-end multilingual result.

Build with:

```bash
make acl
```

Before submission, the following evidence is still required and must not be
replaced with simulated numbers:

- real model generations and official baseline implementations;
- held-out threshold calibration and document-level confidence intervals;
- real MT, paraphrase, summarization, and adaptive-attack outputs;
- multilingual invariant-parser accuracy against human annotations;
- quality, latency, carrier-capacity, and abstention measurements;
- the venue's current responsible-NLP checklist and artifact metadata.

The anonymous source contains no author identity. Restore author metadata only
in the camera-ready version.
