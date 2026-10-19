# Nature submission package

Manuscript: `nature_main.tex` → `nature_main.pdf` (single PDF with figures,
legends with their figures, line numbers, double spacing, as Nature asks for
initial submissions).

## Build

```bash
cd paper
make nature   # regenerates tables/figure data and references, builds, audits
make refs     # checks every references.bib entry against arXiv / Crossref / Anthology
```

`make_nature_assets.py` writes every table body and figure dataset in
`generated/` from `paper/results/*.json`; `make_nature_refs.py` writes the
Nature-style reference list (numbered by first citation, surname + initials,
"et al." beyond five authors, titles kept) from `../references.bib`. No number
in the tables or figures is typed by hand. `make nature` fails on overfull
boxes, floats taller than a page or undefined references, then runs the page
ink audit (line numbers allowed in the left margin).

## Compliance with Nature's Article guidelines (checked 2026-10-19)

| Requirement | Guideline | Manuscript |
|---|---|---|
| Title | ≤ 75 characters; no numbers, acronyms or punctuation | 69 characters |
| Summary paragraph | referenced, ~200 words, few numbers or abbreviations, "Here we show" | 189 words |
| Main text | ~2,500 words with 4 display items (6-page article) | ~2,000 words, 2 figures + 2 tables |
| Subheadings | ≤ 40 characters | longest 38 |
| Methods | ≤ ~3,000 words, no figures or tables | ~900 words |
| Extended Data | ≤ 10 items | 9 tables |
| References | ≤ 50 in main text, numbered, titles included | 27 |
| Figure legends | < 300 words, start with a brief title | 87 and 121 words |
| Figure size | 90 / 180 mm wide, ≤ 170 mm deep | within the 160 mm text block |
| Statements | Data availability, Code availability, author contributions, competing interests | present |
| AI tools | disclose use; AI is not an author | disclosed in Methods |
| Line numbers | required in the PDF | present |

## Before submitting

See `../../NATURE_REVIEW_KO.md` for the reviewer assessment and the P0 work.
Author items: affiliation city/country and ORCID; confirm the AI-use wording;
record the language model that translated the 16-sentence pilot; commit the
KGW raw scores; choose single- or double-anonymous review (double-anonymous
needs an anonymized copy without the author block or repository links); cover
letter. Do not submit the ACL build (`../acl_main.*`): Nature requires that the
results are not under consideration elsewhere.
