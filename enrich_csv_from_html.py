#!/usr/bin/env python3
import csv
import os
import re
from html.parser import HTMLParser
from typing import Dict, List, Tuple


BASE_DIR = os.path.abspath(
    "/Users/nilsandersson/Library/CloudStorage/GoogleDrive-nils@several.club/My Drive/Several/Several Projects/Websites/Several.Club"
)


class ImgTagParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.imgs: List[Tuple[str, str]] = []  # (src, alt)

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() == "img":
            attr_dict = {k.lower(): v for k, v in attrs}
            src = attr_dict.get("src", "").strip()
            alt = attr_dict.get("alt", "").strip()
            if src:
                self.imgs.append((src, alt))


def collect_html_files() -> List[str]:
    html_files: List[str] = []
    for entry in os.listdir(BASE_DIR):
        if entry.lower().endswith(".html"):
            html_files.append(os.path.join(BASE_DIR, entry))
    return html_files


def normalize_src_to_rel(src: str) -> str:
    # Remove any URL params and fragments
    src = src.split("?")[0].split("#")[0]
    # Normalize slashes
    src = src.replace("\\", "/")
    # Remove leading ./ or /
    src = re.sub(r"^\./", "", src)
    src = re.sub(r"^/", "", src)
    return src


def build_alt_map_from_html(html_files: List[str]) -> Dict[str, str]:
    alt_by_relpath: Dict[str, str] = {}
    alt_by_basename: Dict[str, str] = {}

    for html_path in html_files:
        try:
            with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue
        parser = ImgTagParser()
        try:
            parser.feed(content)
        except Exception:
            # If parser fails on malformed HTML, skip file
            continue
        for src, alt in parser.imgs:
            if not src:
                continue
            rel = normalize_src_to_rel(src)
            # Keep the first non-empty alt encountered for a given image
            if rel not in alt_by_relpath or (not alt_by_relpath[rel] and alt):
                alt_by_relpath[rel] = alt
            base = os.path.basename(rel)
            if base not in alt_by_basename or (not alt_by_basename[base] and alt):
                alt_by_basename[base] = alt

    # Merge: prefer relpath-specific, fallback to basename mapping
    # Return combined dict where keys are relpaths and basenames for matching flexibility
    combined: Dict[str, str] = {}
    combined.update(alt_by_relpath)
    # Store basename keys with a special prefix to distinguish if needed
    for base, alt in alt_by_basename.items():
        combined[f"__basename__/{base}"] = alt
    return combined


def enrich_csv(csv_path: str, alt_map: Dict[str, str]) -> None:
    rows: List[dict] = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            rows.append(row)

    # Ensure required fields exist
    required_fields = [
        "original_path",
        "proposed_filename",
        "alt_short_sv",
        "alt_long_sv",
        "dekorativ",
        "recommended_widths",
        "used_on_pages",
    ]
    fieldnames = list(dict.fromkeys(fieldnames + required_fields))

    updated_count = 0
    for row in rows:
        rel = (row.get("original_path") or "").strip()
        rel_norm = normalize_src_to_rel(rel)
        base = os.path.basename(rel_norm)
        alt = alt_map.get(rel_norm)
        if alt is None:
            alt = alt_map.get(f"__basename__/{base}")

        if alt is not None:
            alt = alt.strip()
            if alt:
                row["alt_short_sv"] = alt
                row["alt_long_sv"] = alt
                # If previously marked decorative but now descriptive alt found, set nej
                row["dekorativ"] = row.get("dekorativ", "nej") or "nej"
            else:
                # Empty alt indicates decorative
                row["alt_short_sv"] = ""
                row["alt_long_sv"] = ""
                row["dekorativ"] = "ja"
            updated_count += 1

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {updated_count} rows with alt texts from HTML")


def main() -> int:
    csv_path = os.path.join(BASE_DIR, "assets_proposals.csv")
    if not os.path.isfile(csv_path):
        print(f"CSV not found: {csv_path}")
        return 1

    html_files = collect_html_files()
    alt_map = build_alt_map_from_html(html_files)
    enrich_csv(csv_path, alt_map)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


