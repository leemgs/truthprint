#!/usr/bin/env python3
"""Page-by-page ink audit of the ACL PDF (no third-party Python packages).

Rasterizes every page with pdftoppm and fails if any ink lies outside the
A4 text block (25 mm margins) or below the 272 mm text bottom, other than the
page number. Pages whose ink crosses the column gutter are listed so they can
be checked against the full-width floats (figure*/table*).
"""
from __future__ import annotations

import glob
import subprocess
import sys
import tempfile
from pathlib import Path

DPI = 100
MM = DPI / 25.4
INK = 110  # grayscale threshold


def read_pgm(path: str) -> tuple[int, int, bytes]:
    data = Path(path).read_bytes()
    parts = data.split(maxsplit=4)
    width, height = int(parts[1]), int(parts[2])
    return width, height, parts[4][-width * height:]


def audit(pdf: str) -> int:
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", str(DPI), "-gray", pdf, f"{tmp}/p"], check=True)
        pages = sorted(glob.glob(f"{tmp}/p-*.pgm"))
        for page in pages:
            width, height, px = read_pgm(page)
            xmin, xmax, last_text_row, gutter_rows = width, 0, 0, 0
            for y in range(int(20 * MM), int(278 * MM)):
                row = px[y * width:(y + 1) * width]
                xs = [x for x in range(width) if row[x] < INK]
                if not xs:
                    continue
                xmin, xmax = min(xmin, xs[0]), max(xmax, xs[-1])
                if any(30 * MM < x < 185 * MM for x in xs):
                    last_text_row = y
                if any(103 * MM <= x <= 107 * MM for x in xs):
                    gutter_rows += 1
            name = Path(page).stem.split("-")[-1]
            if xmin < 24 * MM or xmax > 186 * MM or last_text_row > 274 * MM:
                failures.append(name)
            note = f"  (gutter-crossing ink: {gutter_rows} rows)" if gutter_rows else ""
            print(f"page {name}: x {xmin / MM:.1f}-{xmax / MM:.1f} mm, "
                  f"text bottom {last_text_row / MM:.1f} mm{note}")
    print(f"{len(pages)} pages, {len(failures)} outside the text block {failures or ''}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(audit(sys.argv[1] if len(sys.argv) > 1 else "acl_main.pdf"))
