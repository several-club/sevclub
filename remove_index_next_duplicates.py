#!/usr/bin/env python3
"""
Remove duplicate 'index-next-block' sections from case pages.

Rules (per plan):
- Keep the 'case-navigation' block as-is.
- Remove the header 'index-next-block' (the first occurrence) on all listed case pages.
- Remove any 'index-next-block' that appears AFTER the 'case-navigation' block.
- Do not add 'case-navigation' where it is missing.
"""
from __future__ import annotations

import re
from pathlib import Path

# Workspace root (this script is placed at the root)
ROOT = Path(__file__).resolve().parent

# Absolute file paths to target case pages
CASE_FILES = [
    ROOT / "universal-music.html",
    ROOT / "cervera.html",
    ROOT / "coop-skargarden.html",
    ROOT / "cucina-povera.html",
    ROOT / "claes-dalen.html",
    ROOT / "jeanerica.html",
    ROOT / "stelly.html",
    ROOT / "coop-port-73.html",
    ROOT / "modha.html",
    ROOT / "blankens.html",
    ROOT / "snacka-om-sjukt.html",
    ROOT / "bord.html",
    ROOT / "lindbergs.html",
    ROOT / "bailet.html",
    ROOT / "backfabrik.html",
    ROOT / "remm.html",
    ROOT / "goalplan.html",
    ROOT / "hyper-island.html",
    ROOT / "gallno.html",
    ROOT / "stefan-ekengren.html",
]

# Regex to match an entire index-next-block. It optionally consumes a preceding
# HTML comment like <!-- Index/Next Navigation --> and following whitespace.
INDEX_NEXT_BLOCK_RE = re.compile(
    r"(?:<!--\s*Index/Next Navigation\s*-->\s*)?"
    r"<div[^>]*class=(?:\"[^\"]*\bindex-next-block\b[^\"]*\"|'[^']*\bindex-next-block\b[^']*')[^>]*>"
    r"[\s\S]*?</div>",
    re.IGNORECASE,
)

# Regex to locate the opening of the case-navigation block
CASE_NAV_RE = re.compile(
    r"<div[^>]*class=(?:\"[^\"]*\bcase-navigation\b[^\"]*\"|'[^']*\bcase-navigation\b[^']*')",
    re.IGNORECASE,
)

CASE_NAV_BLOCK_RE = re.compile(
    r"<div[^>]*class=(?:\"[^\"]*\bcase-navigation\b[^\"]*\"|'[^']*\bcase-navigation\b[^']*')[^>]*>"
    r"[\s\S]*?</div>",
    re.IGNORECASE,
)


def compute_removals(html: str) -> list[tuple[int, int]]:
    """Return spans (start, end) to remove based on the rules."""
    removals: list[tuple[int, int]] = []

    # Find all index-next-block occurrences
    blocks = list(INDEX_NEXT_BLOCK_RE.finditer(html))
    if not blocks:
        return removals

    # NEW rule per follow-up: remove ALL index-next-block occurrences
    for m in blocks:
        span = m.span()
        if span not in removals:
            removals.append(span)

    # If file contains duplicated case-navigation blocks (possible from prior edits),
    # keep the first and remove any subsequent duplicates.
    nav_blocks = list(CASE_NAV_BLOCK_RE.finditer(html))
    if len(nav_blocks) > 1:
        for m in nav_blocks[1:]:
            span = m.span()
            if span not in removals:
                removals.append(span)

    # Sort in ascending order for safe splicing with a moving window.
    removals.sort(key=lambda s: s[0])
    return removals


def apply_removals(html: str, removals: list[tuple[int, int]]) -> str:
    if not removals:
        return html
    parts = []
    last = 0
    for start, end in removals:
        parts.append(html[last:start])
        last = end
    parts.append(html[last:])
    return "".join(parts)


def process_file(path: Path) -> tuple[bool, int]:
    """Process a single file. Returns (changed, num_removed_blocks)."""
    original = path.read_text(encoding="utf-8")
    spans = compute_removals(original)
    if not spans:
        return False, 0
    updated = apply_removals(original, spans)
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True, len(spans)
    return False, 0


def main() -> None:
    total_changed = 0
    total_blocks = 0
    for fp in CASE_FILES:
        if not fp.exists():
            print(f"Skip (missing): {fp}")
            continue
        changed, removed = process_file(fp)
        if changed:
            print(f"Updated {fp.name}: removed {removed} block(s)")
            total_changed += 1
            total_blocks += removed
        else:
            print(f"No changes needed: {fp.name}")
    print(f"\nDone. Files updated: {total_changed}, blocks removed: {total_blocks}")


if __name__ == "__main__":
    main()


