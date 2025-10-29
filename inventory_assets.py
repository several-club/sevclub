#!/usr/bin/env python3
import csv
import os
import re
import sys
import unicodedata
from typing import Dict, List, Tuple


BASE_DIR = os.path.abspath(
    "/Users/nilsandersson/Library/CloudStorage/GoogleDrive-nils@several.club/My Drive/Several/Several Projects/Websites/Several.Club"
)
ASSETS_DIR = os.path.join(BASE_DIR, "Assets")


def normalize_swedish(text: str) -> str:
    replacements = {
        "å": "a",
        "ä": "a",
        "ö": "o",
        "Å": "a",
        "Ä": "a",
        "Ö": "o",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    # General unicode normalization (remove diacritics)
    text = (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    return text


def slugify_kebab(text: str) -> str:
    text = normalize_swedish(text)
    # Replace separators with hyphen
    text = re.sub(r"[\s_.]+", "-", text)
    # Remove any character not alnum or hyphen
    text = re.sub(r"[^a-zA-Z0-9-]", "-", text)
    # Collapse repeated hyphens
    text = re.sub(r"-+", "-", text)
    text = text.strip("-")
    return text.lower()


def is_video_extension(ext: str) -> bool:
    return ext.lower() in {".mp4", ".webm", ".mov", ".m4v"}


def is_image_extension(ext: str) -> bool:
    return ext.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"}


def is_svg_extension(ext: str) -> bool:
    return ext.lower() == ".svg"


def propose_filename(asset_path: str) -> str:
    rel_path = os.path.relpath(asset_path, ASSETS_DIR)
    directory, filename = os.path.split(rel_path)
    name, ext = os.path.splitext(filename)

    # First-level collection name (e.g., Backfabrik, Blankens, Index)
    parts = [p for p in directory.split(os.sep) if p]
    collection = parts[0] if parts else "assets"

    base_tokens: List[str] = []
    # Start with collection name
    base_tokens.append(slugify_kebab(collection))

    # Derive tokens from original name
    name_slug = slugify_kebab(name)
    # Remove duplicate collection prefix from name_slug
    if name_slug.startswith(base_tokens[0] + "-"):
        name_slug = name_slug[len(base_tokens[0]) + 1 :]
    elif name_slug == base_tokens[0]:
        name_slug = ""

    # Tokenize by hyphen
    if name_slug:
        tokens = [t for t in name_slug.split("-") if t]
    else:
        tokens = []

    # Normalize numeric tokens to two-digits (e.g., 1 -> 01)
    normalized_tokens: List[str] = []
    for tok in tokens:
        if tok.isdigit():
            normalized_tokens.append(tok.zfill(2))
        else:
            # split dotted numbers like 1.2 into 01 and 02
            if re.fullmatch(r"\d+\.\d+", tok):
                for sub in tok.split("."):
                    normalized_tokens.append(sub.zfill(2))
            else:
                normalized_tokens.append(tok)

    # Build final name
    if normalized_tokens:
        base_tokens.extend(normalized_tokens)
    base = "-".join(base_tokens)

    return f"{base}{ext.lower()}"


def generate_alt_texts(asset_path: str) -> Tuple[str, str, str]:
    rel_path = os.path.relpath(asset_path, ASSETS_DIR)
    directory, filename = os.path.split(rel_path)
    name, ext = os.path.splitext(filename)
    parts = [p for p in directory.split(os.sep) if p]
    collection = parts[0] if parts else "Bild"

    # Heuristics for alt texts
    collection_clean = collection.replace("-", " ")
    name_clean = normalize_swedish(os.path.splitext(filename)[0]).replace("_", " ").replace("-", " ")

    dekorativ = "nej"
    if is_svg_extension(ext):
        if re.search(r"logo|logotyp", name, flags=re.IGNORECASE):
            alt_short = f"Logotyp: {collection_clean}"
            alt_long = f"Logotyp för {collection_clean}"
            dekorativ = "nej"
        else:
            # Many SVGs are decorative; mark as likely decorative but reviewable
            alt_short = f"Dekorativ grafik ({collection_clean})"
            alt_long = f"Dekorativ vektorikon relaterad till {collection_clean} (uppdatera om informativ)"
            dekorativ = "ja"
    elif is_video_extension(ext):
        alt_short = f"Video: {collection_clean}"
        alt_long = f"Video från projektet {collection_clean} (beskriv motiv)"
        dekorativ = "nej"
    else:
        # Raster image: suggest neutral but useful texts
        # Extract descriptive tokens from the filename minus collection
        name_slug = slugify_kebab(name)
        coll_slug = slugify_kebab(collection)
        if name_slug.startswith(coll_slug + "-"):
            name_slug = name_slug[len(coll_slug) + 1 :]
        tokens = [t for t in name_slug.split("-") if t and not t.isdigit()]
        # drop two-digit numeric tokens
        tokens = [t for t in tokens if not re.fullmatch(r"\d{2}", t)]
        descriptor = " ".join(tokens[:4]).strip()
        if descriptor:
            alt_short = f"{collection_clean} – {descriptor}"
            alt_long = f"{collection_clean}: {descriptor}. Uppdatera till exakt motivbeskrivning"
        else:
            alt_short = f"{collection_clean} – bild"
            alt_long = f"Bild från projektet {collection_clean} (uppdatera med motiv)"
        dekorativ = "nej"

    return alt_short, alt_long, dekorativ


def find_usages(asset_rel_path: str, html_files: List[str]) -> List[str]:
    usages: List[str] = []
    needle = asset_rel_path.replace("\\", "/")
    filename = os.path.basename(asset_rel_path)
    for html_path in html_files:
        try:
            with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue
        if needle in content or filename in content:
            usages.append(os.path.basename(html_path))
    return usages


def collect_html_files() -> List[str]:
    # All .html files in BASE_DIR (non-recursive per current project layout)
    html_files: List[str] = []
    for entry in os.listdir(BASE_DIR):
        if entry.lower().endswith(".html"):
            html_files.append(os.path.join(BASE_DIR, entry))
    return html_files


def collect_assets() -> List[str]:
    asset_files: List[str] = []
    for root, dirs, files in os.walk(ASSETS_DIR):
        # Skip generated output directories
        dirs[:] = [d for d in dirs if not d.startswith("_") and d != "_generated"]
        for fn in files:
            if fn.startswith("."):
                continue
            full_path = os.path.join(root, fn)
            asset_files.append(full_path)
    return asset_files


def main() -> int:
    if not os.path.isdir(ASSETS_DIR):
        print(f"Assets directory not found: {ASSETS_DIR}", file=sys.stderr)
        return 1

    html_files = collect_html_files()
    assets = collect_assets()

    csv_path = os.path.join(BASE_DIR, "assets_proposals.csv")
    recommended_widths_images = "320;640;960;1280;1600;2000"

    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "original_path",
                "proposed_filename",
                "alt_short_sv",
                "alt_long_sv",
                "dekorativ",
                "recommended_widths",
                "used_on_pages",
            ]
        )

        for asset in sorted(assets):
            rel_from_base = os.path.relpath(asset, BASE_DIR)
            rel_from_base = rel_from_base.replace("\\", "/")
            _, ext = os.path.splitext(asset)

            proposed = propose_filename(asset)
            alt_short, alt_long, dekorativ = generate_alt_texts(asset)
            usages = find_usages(rel_from_base, html_files)
            recommended = recommended_widths_images if (is_image_extension(ext) or is_svg_extension(ext)) else ""

            writer.writerow(
                [
                    rel_from_base,
                    proposed,
                    alt_short,
                    alt_long,
                    dekorativ,
                    recommended,
                    ";".join(usages),
                ]
            )

    print(f"Wrote proposals to {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


