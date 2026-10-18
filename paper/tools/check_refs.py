#!/usr/bin/env python3
"""Check every references.bib entry against its source of record.

arXiv entries: title and full ordered author list against the arXiv abstract
page's citation metadata, and the venue arXiv reports is printed next to the
bib venue; an entry still cited as a preprint fails if Crossref holds a
published version with the same title. DOI entries: title, volume, issue, pages and author count against
Crossref. ACL Anthology entries: title, booktitle, pages and year against
the Anthology BibTeX record. Needs network access; exits non-zero on any mismatch.
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BIB = Path(__file__).resolve().parent.parent / "references.bib"
LATEX_ACCENTS = {r'{\"a}': "ä", r'{\"o}': "ö", r'{\"u}': "ü", r"{\'c}": "ć", r"{\'e}": "é"}


def fetch(url: str, attempts: int = 5) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (reference-check)"})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as err:
            if err.code not in (429, 503) or attempt == attempts - 1:
                raise
            time.sleep(2 ** (attempt + 1))  # rate-limited: back off and retry
    raise AssertionError("unreachable")


def norm(text: str) -> str:
    for latex, char in LATEX_ACCENTS.items():
        text = text.replace(latex, char)
    text = unicodedata.normalize("NFKD", re.sub(r"[{}\\]", "", text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", text.lower())


def field(body: str, name: str) -> str | None:
    match = re.search(r"\b" + name + r"=\{", body)
    if not match:
        return None
    i = j = match.end()
    depth = 1
    while depth:
        depth += {"{": 1, "}": -1}.get(body[j], 0)
        j += 1
    return body[i:j - 1]


def check_arxiv(arxiv_id: str, body: str) -> list[str]:
    page = fetch(f"https://arxiv.org/abs/{arxiv_id}")
    title = html.unescape(re.search(r'name="citation_title" content="([^"]*)"', page).group(1))
    authors = [html.unescape(a) for a in re.findall(r'name="citation_author" content="([^"]*)"', page)]
    bib_authors = [a.strip() for a in field(body, "author").split(" and ")]
    problems = []
    if norm(field(body, "title")) != norm(title):
        problems.append(f"title differs: arXiv '{title}'")
    if [norm(a) for a in bib_authors] != [norm(a) for a in authors]:
        problems.append(f"authors differ: arXiv {authors}")
    comment = re.search(r'class="tablecell (?:jref|comments[^"]*)">\s*(.*?)\s*</td>', page, re.S)
    venue = field(body, "booktitle") or field(body, "journal") or "arXiv preprint"
    stated = re.sub("<[^>]+>", "", comment.group(1))[:70] if comment else "-"
    print(f"    venue: bib '{venue} {field(body, 'year')}' | arXiv says '{html.unescape(stated)}'")
    if venue == "arXiv preprint":
        problems += published_version(title)
    return problems


def published_version(title: str) -> list[str]:
    """Flag a preprint citation when Crossref holds a journal/proceedings
    record with the same title (arXiv comments are often never updated)."""
    query = urllib.parse.quote(title)
    found = json.loads(fetch(f"https://api.crossref.org/works?query.title={query}&rows=5"))
    return [f"published version exists: {item['container-title'][0]} "
            f"{item['issued']['date-parts'][0][0]}, doi {item['DOI']}"
            for item in found["message"]["items"]
            if item.get("title") and norm(item["title"][0]) == norm(title)
            and item.get("container-title") and item.get("type") != "posted-content"]


def check_anthology(url: str, body: str) -> list[str]:
    record = fetch(url.rstrip("/") + ".bib")
    problems = []
    for name in ("title", "pages", "year"):
        theirs = re.search(name + r'\s*=\s*"([^"]*)"', record)
        if field(body, name) and theirs and norm(field(body, name)) != norm(theirs.group(1)):
            problems.append(f"{name} {field(body, name)} vs Anthology {theirs.group(1)}")
    if norm(field(body, "booktitle") or "") != norm(re.search(r'booktitle\s*=\s*"([^"]*)"', record).group(1)):
        problems.append("booktitle differs from the Anthology record")
    return problems


def check_doi(doi: str, body: str) -> list[str]:
    msg = json.loads(fetch(f"https://api.crossref.org/works/{doi}"))["message"]
    problems = []
    if norm(field(body, "title")) != norm(msg["title"][0]):
        problems.append(f"title differs: Crossref '{msg['title'][0]}'")
    for name, key in (("volume", "volume"), ("number", "issue")):
        if field(body, name) and field(body, name) != msg.get(key):
            problems.append(f"{name} {field(body, name)} vs Crossref {msg.get(key)}")
    if field(body, "pages") and field(body, "pages").replace("--", "-") != msg.get("page"):
        problems.append(f"pages {field(body, 'pages')} vs Crossref {msg.get('page')}")
    if len(field(body, "author").split(" and ")) != len(msg.get("author", [])):
        problems.append(f"author count vs Crossref {len(msg.get('author', []))}")
    return problems


def main() -> int:
    entries = re.findall(r"@\w+\{(\w+),(.*?)\n\n", BIB.read_text(encoding="utf-8") + "\n\n", re.S)
    failed = 0
    for key, body in entries:
        arxiv = re.search(r"arxiv\.org/abs/([0-9.]+)", body)
        doi = field(body, "doi")
        url = field(body, "url") or ""
        if arxiv:
            source, check, arg = "arXiv", check_arxiv, arxiv.group(1)
        elif doi:
            source, check, arg = "Crossref", check_doi, doi
        elif "aclanthology.org" in url:
            source, check, arg = "ACL Anthology", check_anthology, url
        else:
            print(f"{key}: no arXiv id, DOI or Anthology record; check by hand ({url})")
            continue
        print(f"{key} ({source})")
        try:
            problems = check(arg, body)
        except (urllib.error.URLError, TimeoutError) as err:
            problems = [f"source unreachable ({err}); re-run later"]
        if arxiv:
            time.sleep(1)  # be polite to arxiv.org
        failed += bool(problems)
        print(f"    {'MISMATCH' if problems else 'ok'}")
        for problem in problems:
            print(f"    {problem}")
    print(f"{len(entries)} entries, {failed} mismatches")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
