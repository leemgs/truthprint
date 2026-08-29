#!/usr/bin/env python3
"""Generate the anonymous ACL source from the canonical manuscript body."""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "main.tex"
OUTPUT = ROOT / "acl_main.tex"

PREAMBLE = r"""\documentclass[11pt]{article}
\usepackage[review]{acl}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{booktabs,multirow,array,graphicx,xcolor,url,listings,enumitem,microtype,tikz}
\usetikzlibrary{arrows.meta,positioning,fit,backgrounds}
\definecolor{codegray}{gray}{0.95}
\lstset{basicstyle=\ttfamily\footnotesize,backgroundcolor=\color{codegray},frame=single,breaklines=true,columns=fullflexible,keepspaces=true,showstringspaces=false,tabsize=2}
\newtheorem{theorem}{Theorem}
\newtheorem{proposition}{Proposition}
\newtheorem{definition}{Definition}
\newtheorem{assumption}{Assumption}
\title{Truthprint: Designing an Invariant-Constrained Semantic Intermediate Representation for Provenance Watermarking}
\author{Anonymous ACL Submission}

"""

IEEE_KEYWORDS = r"""\begin{IEEEkeywords}
Intermediate representation, LLM watermarking, paraphrase robustness, provenance, semantic watermarking, SynthID-Text, translation robustness
\end{IEEEkeywords}"""
ACL_KEYWORDS = (
    r"\paragraph{Keywords.} Intermediate representation, LLM watermarking, "
    r"provenance, semantic watermarking, translation robustness"
)


def render() -> str:
    source = SOURCE.read_text(encoding="utf-8")
    body = source[source.index(r"\begin{document}") :]
    body = body.replace(IEEE_KEYWORDS, ACL_KEYWORDS)
    body = body.replace("\n\\balance\n", "\n")
    return PREAMBLE + body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="fail if acl_main.tex is not synchronized")
    args = parser.parse_args()
    expected = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
            print("acl_main.tex is stale; run python3 make_acl_source.py")
            return 1
        return 0
    OUTPUT.write_text(expected, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
