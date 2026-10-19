#!/usr/bin/env python3
"""Write Nature-style reference lists for nature_main.tex from ../references.bib.

References are numbered in order of first citation. Keys first cited before the
``%%METHODS%%`` marker form the main list; keys first cited after it form the
Methods list, whose numbering continues from the main list (Nature style).
Style: surname, initials; more than five authors -> first author et al.;
article title kept as written; journal italic, volume bold; preprints as
"Preprint at <url>".
"""
from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
BIB = HERE.parent / "references.bib"
TEX = HERE / "nature_main.tex"
OUT = HERE / "generated"


def parse_bib(text: str) -> dict[str, dict[str, str]]:
    entries = {}
    for m in re.finditer(r"@(\w+)\{([^,]+),", text):
        kind, key, i = m.group(1).lower(), m.group(2).strip(), m.end()
        depth, j = 1, i
        while depth:
            depth += {"{": 1, "}": -1}.get(text[j], 0)
            j += 1
        body, fields = text[i:j - 1], {"_type": kind}
        for f in re.finditer(r"(\w+)\s*=\s*\{", body):
            k, a = f.group(1).lower(), f.end()
            d, b = 1, a
            while d:
                d += {"{": 1, "}": -1}.get(body[b], 0)
                b += 1
            fields[k] = body[a:b - 1].strip()
        entries[key] = fields
    return entries


def initials(given: str) -> str:
    parts = []
    for word in given.replace(".", " ").split():
        sub = [w for w in word.split("-") if w]
        parts.append("-".join(w[0] + "." for w in sub))
    return " ".join(parts)


def person(name: str) -> str:
    name = name.strip()
    if name.startswith("{") and name.endswith("}"):
        return name[1:-1]  # corporate author
    if "," in name:
        last, given = [x.strip() for x in name.split(",", 1)]
    else:
        bits = name.split()
        last, given = bits[-1], " ".join(bits[:-1])
    return f"{last}, {initials(given)}" if given else last


def split_names(field: str) -> list[str]:
    """Split on top-level ' and ' only, so {Corporate and Name} stays whole."""
    names, depth, cur, i = [], 0, "", 0
    while i < len(field):
        ch = field[i]
        depth += {"{": 1, "}": -1}.get(ch, 0)
        if depth == 0 and field.startswith(" and ", i):
            names.append(cur)
            cur, i = "", i + 5
            continue
        cur += ch
        i += 1
    names.append(cur)
    return [n.strip() for n in names if n.strip()]


def authors(field: str) -> str:
    names = split_names(field)
    if len(names) > 5:
        return person(names[0]) + " et al."
    people = [person(n) for n in names]
    if len(people) == 1:
        return people[0]
    return ", ".join(people[:-1]) + r" \& " + people[-1]


def clean_title(t: str) -> str:
    t = re.sub(r"(?<!\\)[{}]", "", t).strip()
    return t if t.endswith((".", "?", "!")) else t + "."


def pages(p: str) -> str:
    return p.replace("--", "–")


def fmt(e: dict[str, str]) -> str:
    a = authors(e.get("author", ""))
    a = a if a.endswith(".") else a + "."
    title = clean_title(e.get("title", ""))
    year = e.get("year", "")
    url = e.get("url", "")
    arxiv = re.search(r"arxiv\.org/abs/([0-9.]+)", url)
    if e["_type"] == "article":
        vol = f" \\textbf{{{e['volume']}}}" if e.get("volume") else ""
        pg = f", {pages(e['pages'])}" if e.get("pages") else ""
        return f"{a} {title} \\emph{{{e['journal']}}}{vol}{pg} ({year})."
    if e["_type"] == "inproceedings":
        pg = f" {pages(e['pages'])}" if e.get("pages") else ""
        return f"{a} {title} In \\emph{{{e['booktitle']}}}{pg} ({year})."
    if arxiv:
        return f"{a} {title} Preprint at \\url{{https://arxiv.org/abs/{arxiv.group(1)}}} ({year})."
    where = e.get("howpublished", "")
    link = f" \\url{{{url}}}" if url else (f" \\url{{https://doi.org/{e['doi']}}}" if e.get("doi") else "")
    return f"{a} {title} {where}{link} ({year})."


def main() -> int:
    bib = parse_bib(BIB.read_text(encoding="utf-8"))
    tex = TEX.read_text(encoding="utf-8")
    cut = tex.index("%%METHODS%%")
    order, seen = [], set()
    for m in re.finditer(r"\\cite\{([^}]+)\}", tex):
        for k in (x.strip() for x in m.group(1).split(",")):
            if k not in seen:
                if k not in bib:
                    raise SystemExit(f"undefined citation: {k}")
                seen.add(k)
                order.append((k, m.start() < cut))
    main_keys = [k for k, is_main in order if is_main]
    meth_keys = [k for k, is_main in order if not is_main]
    if any(is_main for _, is_main in order[len(main_keys):]):
        raise SystemExit("a main-text key is first cited after a Methods-only key")
    OUT.mkdir(exist_ok=True)
    for name, keys, start in (("refs_main.tex", main_keys, 0),
                              ("refs_methods.tex", meth_keys, len(main_keys))):
        if not keys:
            (OUT / name).write_text("% no references first cited here\n", encoding="utf-8")
            continue
        lines = [f"\\begin{{thebibliography}}{{{len(main_keys) + len(meth_keys)}}}",
                 f"\\setcounter{{enumiv}}{{{start}}}"]
        lines += [f"\\bibitem{{{k}}} {fmt(bib[k])}" for k in keys]
        lines.append("\\end{thebibliography}")
        (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[written] {len(main_keys)} main + {len(meth_keys)} Methods references")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
