#!/usr/bin/env python3
import csv
import os
import sys
from typing import Dict, List, Tuple


BASE_DIR = os.path.abspath(
    "/Users/nilsandersson/Library/CloudStorage/GoogleDrive-nils@several.club/My Drive/Several/Several Projects/Websites/Several.Club"
)
CSV_PATH = os.path.join(BASE_DIR, "assets_proposals.csv")


def list_html_files() -> List[str]:
    html_files: List[str] = []
    for entry in os.listdir(BASE_DIR):
        if entry.lower().endswith(".html"):
            html_files.append(os.path.join(BASE_DIR, entry))
    return html_files


def ensure_unique_destination(dest_path: str) -> str:
    if not os.path.exists(dest_path):
        return dest_path
    root, ext = os.path.splitext(dest_path)
    counter = 2
    while True:
        candidate = f"{root}-{counter}{ext}"
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def apply_renames(rows: List[dict]) -> List[Tuple[str, str]]:
    """Rename files based on CSV rows. Returns list of (old_rel, new_rel)."""
    renames: List[Tuple[str, str]] = []
    for row in rows:
        orig_rel = (row.get("original_path") or "").strip()
        proposed_name = (row.get("proposed_filename") or "").strip()
        if not orig_rel or not proposed_name:
            continue
        src_abs = os.path.join(BASE_DIR, orig_rel)
        if not os.path.exists(src_abs):
            # Skip missing files silently
            continue
        # Build destination path in same directory
        dir_rel = os.path.dirname(orig_rel)
        dest_rel = os.path.join(dir_rel, proposed_name).replace("\\", "/")
        dest_abs = os.path.join(BASE_DIR, dest_rel)

        # If paths are the same (already renamed), skip
        if os.path.abspath(src_abs) == os.path.abspath(dest_abs):
            continue

        # Ensure destination doesn't collide
        dest_abs_unique = ensure_unique_destination(dest_abs)
        dest_rel_unique = os.path.relpath(dest_abs_unique, BASE_DIR).replace("\\", "/")

        # Create directory if needed (should already exist)
        os.makedirs(os.path.dirname(dest_abs_unique), exist_ok=True)

        os.rename(src_abs, dest_abs_unique)
        renames.append((orig_rel, dest_rel_unique))
        # Update CSV row to reflect new path
        row["original_path"] = dest_rel_unique

    return renames


def update_html_references(renames: List[Tuple[str, str]], html_files: List[str]) -> int:
    if not renames:
        return 0
    # Sort by descending length of source to avoid partial overlaps
    renames_sorted = sorted(renames, key=lambda x: len(x[0]), reverse=True)
    total_changes = 0
    for html_path in html_files:
        try:
            with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue
        original_content = content
        for old_rel, new_rel in renames_sorted:
            content = content.replace(old_rel, new_rel)
        if content != original_content:
            with open(html_path, "w", encoding="utf-8", errors="ignore") as f:
                f.write(content)
            total_changes += 1
    return total_changes


def write_csv(rows: List[dict], fieldnames: List[str]) -> None:
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_log(renames: List[Tuple[str, str]]) -> None:
    log_path = os.path.join(BASE_DIR, "rename_log.csv")
    with open(log_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["from", "to"]) 
        for s, d in renames:
            writer.writerow([s, d])


def main() -> int:
    if not os.path.isfile(CSV_PATH):
        print(f"CSV not found: {CSV_PATH}", file=sys.stderr)
        return 1

    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    renames = apply_renames(rows)
    write_log(renames)

    if renames:
        # Update HTML references
        html_files = list_html_files()
        changed_files = update_html_references(renames, html_files)
        print(f"Renamed {len(renames)} files; updated {changed_files} HTML files")
        # Persist CSV with updated paths
        write_csv(rows, fieldnames)
    else:
        print("No files to rename")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


