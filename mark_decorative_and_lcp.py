#!/usr/bin/env python3
import csv
import os
import re
from typing import Dict, List, Optional, Tuple


BASE_DIR = os.path.abspath(
    "/Users/nilsandersson/Library/CloudStorage/GoogleDrive-nils@several.club/My Drive/Several/Several Projects/Websites/Several.Club"
)
CSV_PATH = os.path.join(BASE_DIR, "assets_proposals.csv")


IMG_TAG_RE = re.compile(r"<img\b([^>]*)>", re.IGNORECASE)
ATTR_RE = re.compile(r"(\w+)\s*=\s*\"([^\"]*)\"", re.IGNORECASE)
HEAD_END_RE = re.compile(r"</head>", re.IGNORECASE)


def parse_attrs(attr_text: str) -> Dict[str, str]:
    attrs: Dict[str, str] = {}
    for k, v in ATTR_RE.findall(attr_text or ""):
        attrs[k.lower()] = v
    return attrs


def serialize_img(attrs: Dict[str, str]) -> str:
    # Ensure deterministic order: src, alt, fetchpriority, loading, decoding, width, height, then others
    order = ["src", "alt", "fetchpriority", "loading", "decoding", "width", "height"]
    parts: List[str] = ["<img"]
    used = set()
    for key in order:
        if key in attrs and attrs[key] is not None:
            parts.append(f"{key}=\"{attrs[key]}\"")
            used.add(key)
    for k, v in attrs.items():
        if k in used:
            continue
        parts.append(f"{k}=\"{v}\"")
    return " ".join(parts) + ">"


def src_to_variant_lists(rel_src: str) -> Optional[Dict[str, List[Tuple[str, int]]]]:
    rel_src = rel_src.split("?")[0].split("#")[0]
    if not rel_src.lower().startswith("assets/"):
        return None
    directory, filename = os.path.split(rel_src)
    name, _ = os.path.splitext(filename)
    sub = directory[len("Assets/"):]
    base_generated = f"Assets/_generated/{sub}/{name}"
    widths = [320, 640, 960, 1280, 1600, 2000]
    results: Dict[str, List[Tuple[str, int]]] = {"avif": [], "webp": []}
    for w in widths:
        avif_rel = f"{base_generated}-{w}.avif"
        webp_rel = f"{base_generated}-{w}.webp"
        avif_abs = os.path.join(BASE_DIR, avif_rel)
        webp_abs = os.path.join(BASE_DIR, webp_rel)
        if os.path.exists(avif_abs):
            results["avif"].append((avif_rel, w))
        if os.path.exists(webp_abs):
            results["webp"].append((webp_rel, w))
    if not results["avif"] and not results["webp"]:
        return None
    return results


def add_preload_link(html: str, rel_src: str, sizes: str = "(min-width: 1024px) 50vw, 100vw") -> str:
    # Build a preload link using WEBP srcset when available
    variants = src_to_variant_lists(rel_src)
    # Avoid duplicates
    if f"href=\"{rel_src}\"" in html and "rel=\"preload\"" in html:
        return html
    if variants:
        webp_srcset = ", ".join([f"{path} {w}w" for path, w in variants.get("webp", [])])
        if not webp_srcset:
            # fallback to avif if webp missing
            webp_srcset = ", ".join([f"{path} {w}w" for path, w in variants.get("avif", [])])
        if webp_srcset:
            preload = (
                f"<link rel=\"preload\" as=\"image\" href=\"{rel_src}\" imagesrcset=\"{webp_srcset}\" imagesizes=\"{sizes}\">\n"
            )
        else:
            preload = f"<link rel=\"preload\" as=\"image\" href=\"{rel_src}\">\n"
    else:
        # No generated variants; preload the fallback src only
        preload = f"<link rel=\"preload\" as=\"image\" href=\"{rel_src}\">\n"
    m = HEAD_END_RE.search(html)
    if not m:
        return html
    idx = m.start()
    return html[:idx] + preload + html[idx:]


def update_csv_decorative(paths: List[str]) -> None:
    if not os.path.isfile(CSV_PATH) or not paths:
        return
    # Normalize paths to match CSV
    norm_paths = set(p.replace("\\", "/") for p in paths)
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    changed = False
    for row in rows:
        rel = (row.get("original_path") or "").strip()
        if rel in norm_paths:
            if row.get("dekorativ", "nej").lower() != "ja":
                row["dekorativ"] = "ja"
                # Clear alts for decorative
                row["alt_short_sv"] = ""
                row["alt_long_sv"] = ""
                changed = True
    if changed:
        with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


def process_file(path: str) -> bool:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    changed = False
    decorative_paths_for_csv: List[str] = []

    # 1) Mark decorative UI icons (images/...) as decorative
    def mark_decorative(match: re.Match) -> str:
        nonlocal changed
        full_tag = match.group(0)
        attrs = parse_attrs(match.group(1))
        src = attrs.get("src", "")
        if not src:
            return full_tag
        # Only treat UI assets (outside Assets/) as decorative
        if src.startswith("images/"):
            # Skip explicit logos
            is_logo = ("logo" in (attrs.get("alt", "").lower() or "")) or ("logo" in os.path.basename(src).lower())
            if not is_logo:
                attrs["alt"] = ""
                attrs["role"] = "presentation"
                changed = True
                return serialize_img(attrs)
        return full_tag

    html_new = IMG_TAG_RE.sub(mark_decorative, html)
    html = html_new

    # 2) Set LCP fetchpriority and preload
    filename = os.path.basename(path).lower()
    eager_targets: List[Tuple[int, Dict[str, str]]] = []  # (pos, attrs)
    asset_img_targets: List[Tuple[int, Dict[str, str]]] = []

    first_img_attrs: Optional[Dict[str, str]] = None
    first_img_pos: Optional[int] = None
    for m in IMG_TAG_RE.finditer(html):
        attrs = parse_attrs(m.group(1))
        src = attrs.get("src", "")
        if not src:
            continue
        pos = m.start()
        if first_img_attrs is None:
            first_img_attrs = attrs
            first_img_pos = pos
        if attrs.get("loading", "").lower() == "eager":
            eager_targets.append((pos, attrs))
        if src.startswith("Assets/"):
            asset_img_targets.append((pos, attrs))

    def set_fetchpriority_and_preload(target_attrs: Dict[str, str]) -> None:
        nonlocal html, changed
        src = target_attrs.get("src", "")
        if not src:
            return
        # Add fetchpriority
        if target_attrs.get("fetchpriority") != "high":
            target_attrs["fetchpriority"] = "high"
            changed = True
        # Ensure decoding/loading present
        if "decoding" not in target_attrs:
            target_attrs["decoding"] = "async"
        if "loading" not in target_attrs or target_attrs["loading"] == "eager":
            # keep eager or leave absent
            pass
        # Replace the first occurrence of this specific <img ...>
        # Find the exact match again to rebuild only once
        pattern = re.compile(r"<img\b[^>]*src=\"" + re.escape(src) + r"\"[^>]*>", re.IGNORECASE)
        def repl(m: re.Match) -> str:
            return serialize_img(target_attrs)
        html = pattern.sub(repl, html, count=1)
        # Add preload link in <head>
        html = add_preload_link(html, src)

    if filename == "index.html":
        # apply to all eager images
        for _, attrs in eager_targets:
            set_fetchpriority_and_preload(dict(attrs))
    else:
        # first asset image on page is likely hero
        if asset_img_targets:
            # choose earliest occurrence
            asset_img_targets.sort(key=lambda x: x[0])
            _, first_attrs = asset_img_targets[0]
            set_fetchpriority_and_preload(dict(first_attrs))
        # Special-case pages where hero is not under Assets (e.g., services/about)
        if filename in ("services.html", "about.html") and first_img_attrs is not None:
            set_fetchpriority_and_preload(dict(first_img_attrs))

    if changed:
        with open(path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(html)

    # Update CSV for decorative Assets paths (unlikely here; kept for completeness)
    if decorative_paths_for_csv:
        update_csv_decorative(decorative_paths_for_csv)

    return changed


def main() -> int:
    changed_files = 0
    for entry in os.listdir(BASE_DIR):
        if not entry.lower().endswith(".html"):
            continue
        path = os.path.join(BASE_DIR, entry)
        if process_file(path):
            changed_files += 1
    print(f"Updated decorative and LCP in {changed_files} HTML files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


