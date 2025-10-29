#!/usr/bin/env python3
import csv
import os
import re
from typing import Dict, List, Set


BASE_DIR = os.path.abspath(
    "/Users/nilsandersson/Library/CloudStorage/GoogleDrive-nils@several.club/My Drive/Several/Several Projects/Websites/Several.Club"
)
CSV_PATH = os.path.join(BASE_DIR, "assets_proposals.csv")

IMG_TAG_RE = re.compile(r"<img\b([^>]*)>", re.IGNORECASE)
ATTR_RE = re.compile(r"(\w+)\s*=\s*\"([^\"]*)\"", re.IGNORECASE)


def parse_attrs(attr_text: str) -> Dict[str, str]:
    attrs: Dict[str, str] = {}
    for k, v in ATTR_RE.findall(attr_text or ""):
        attrs[k.lower()] = v
    return attrs


def collect_decorative_assets() -> Set[str]:
    decorative: Set[str] = set()
    for entry in os.listdir(BASE_DIR):
        if not entry.lower().endswith(".html"):
            continue
        path = os.path.join(BASE_DIR, entry)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                html = f.read()
        except Exception:
            continue
        for m in IMG_TAG_RE.finditer(html):
            attrs = parse_attrs(m.group(1))
            src = (attrs.get("src") or "").strip()
            if not src or not src.startswith("Assets/"):
                continue
            alt = (attrs.get("alt") or "").strip()
            role = (attrs.get("role") or "").strip().lower()
            if alt == "" or role == "presentation":
                decorative.add(src.replace("\\", "/"))
    return decorative


def update_csv(decorative_paths: Set[str]) -> int:
    if not os.path.isfile(CSV_PATH):
        return 0
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    updated = 0
    for row in rows:
        rel = (row.get("original_path") or "").strip()
        if rel in decorative_paths:
            if row.get("dekorativ", "nej").lower() != "ja" or row.get("alt_short_sv") or row.get("alt_long_sv"):
                row["dekorativ"] = "ja"
                row["alt_short_sv"] = ""
                row["alt_long_sv"] = ""
                updated += 1
    if updated:
        with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    return updated


def main() -> int:
    decorative = collect_decorative_assets()
    updated = update_csv(decorative)
    print(f"Marked {updated} CSV rows as decorative (from HTML)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


