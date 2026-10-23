#!/usr/bin/env python3
"""ACL/ARR format gates on the rendered review PDF (desk-reject triggers).

* A4 paper, every font embedded, no author/title in the PDF metadata;
* abstract at most 200 words (rendered text);
* the body ends by page 8: the page that holds the ``Limitations`` heading has
  no body text above it unless that page is <= 8;
* no unresolved references (``??``) in the rendered text.

Usage: python3 tools/check_submission.py acl_main.pdf
"""
import re
import subprocess
import sys

MAX_BODY_PAGES, MAX_ABSTRACT_WORDS = 8, 200


def run(*cmd: str) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def page_text(pdf: str, page: int) -> list[str]:
    lines = run("pdftotext", "-f", str(page), "-l", str(page), pdf, "-").splitlines()
    return [l for l in lines if l.strip() and not re.fullmatch(r"\s*\d+\s*", l)]  # drop line numbers


def main(pdf: str) -> int:
    errors = []
    info = run("pdfinfo", pdf)
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
    if "595.276 x 841.89" not in info:
        errors.append("paper size is not A4")
    for key in ("Author", "Title"):
        m = re.search(rf"^{key}:[ \t]*(.*)$", info, re.M)
        if m and m.group(1).strip():
            errors.append(f"PDF metadata {key} is set: {m.group(1).strip()!r}")
    fonts = run("pdffonts", pdf).splitlines()[2:]
    unembedded = [f.split()[0] for f in fonts if f.split()[-5] != "yes"]
    if unembedded:
        errors.append(f"fonts not embedded: {unembedded}")

    first = page_text(pdf, 1)
    i = next(k for k, l in enumerate(first) if l.strip() == "Abstract")
    j = next(k for k, l in enumerate(first) if re.fullmatch(r"(1\s+)?Introduction", l.strip()))
    words = len(" ".join(first[i + 1:j]).split())
    if words > MAX_ABSTRACT_WORDS:
        errors.append(f"abstract has {words} words (> {MAX_ABSTRACT_WORDS})")

    lim_page = next(p for p in range(1, pages + 1) if "Limitations" in [l.strip() for l in page_text(pdf, p)])
    text = page_text(pdf, lim_page)
    if lim_page > MAX_BODY_PAGES + 1 or (lim_page == MAX_BODY_PAGES + 1 and text[0].strip() != "Limitations"):
        errors.append(f"body runs past page {MAX_BODY_PAGES} (Limitations on page {lim_page})")

    if "??" in run("pdftotext", pdf, "-"):
        errors.append("unresolved reference '??' in the PDF")

    for e in errors:
        print("FAIL:", e)
    if not errors:
        print(f"{pages} pages, A4, fonts embedded, metadata empty, abstract {words} words, "
              f"body ends by page {lim_page - (text[0].strip() == 'Limitations')}, no '??'")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "acl_main.pdf"))
