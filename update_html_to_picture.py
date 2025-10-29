#!/usr/bin/env python3
import csv
import os
import re
from typing import Dict, List, Optional, Tuple


BASE_DIR = os.path.abspath(
    "/Users/nilsandersson/Library/CloudStorage/GoogleDrive-nils@several.club/My Drive/Several/Several Projects/Websites/Several.Club"
)
CSV_PATH = os.path.join(BASE_DIR, "assets_proposals.csv")


class ImgNode:
    def __init__(self, full: str, src: str, alt: str, attrs: Dict[str, str]):
        self.full = full
        self.src = src
        self.alt = alt
        self.attrs = attrs


IMG_TAG_RE = re.compile(r"<img\b([^>]*)>", re.IGNORECASE)
ATTR_RE = re.compile(r"(\w+)\s*=\s*\"([^\"]*)\"", re.IGNORECASE)


def parse_attrs(attr_text: str) -> Dict[str, str]:
    attrs: Dict[str, str] = {}
    for k, v in ATTR_RE.findall(attr_text):
        attrs[k.lower()] = v
    return attrs


def find_imgs(html: str) -> List[ImgNode]:
    nodes: List[ImgNode] = []
    for m in IMG_TAG_RE.finditer(html):
        full_tag = m.group(0)
        attr_text = m.group(1) or ""
        attrs = parse_attrs(attr_text)
        src = attrs.get("src", "")
        alt = attrs.get("alt", "")
        if src:
            nodes.append(ImgNode(full_tag, src, alt, attrs))
    return nodes


def src_to_variant_lists(rel_src: str) -> Optional[Dict[str, List[Tuple[str, int]]]]:
    # Map Assets/.../name.ext -> existing Assets/_generated/.../name-{w}.{fmt}
    rel_src = rel_src.split("?")[0].split("#")[0]
    if not rel_src.lower().startswith("assets/"):
        return None
    directory, filename = os.path.split(rel_src)
    name, ext = os.path.splitext(filename)
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


def get_image_dims(rel_src: str) -> Tuple[Optional[int], Optional[int]]:
    abs_path = os.path.join(BASE_DIR, rel_src.split("?")[0].split("#")[0])
    try:
        from PIL import Image
        with Image.open(abs_path) as im:
            w, h = im.size
            return w, h
    except Exception:
        return None, None


def build_img_from_attrs(attrs: Dict[str, str], src: str, alt: str, width: Optional[int], height: Optional[int]) -> str:
    # Preserve attributes like class, id, style, sizes; override src/alt/decoding/loading/width/height
    preserved_keys = [k for k in attrs.keys() if k not in {"src", "alt", "decoding", "loading", "width", "height", "srcset"}]
    parts: List[str] = ["<img"]
    # src and alt first
    parts.append(f"src=\"{src}\"")
    parts.append(f"alt=\"{alt}\"")
    # loading/decoding: keep eager if set, else lazy
    loading = attrs.get("loading", "lazy")
    parts.append(f"loading=\"{loading}\"")
    parts.append("decoding=\"async\"")
    if width and height:
        parts.append(f"width=\"{width}\"")
        parts.append(f"height=\"{height}\"")
    for k in preserved_keys:
        v = attrs[k]
        parts.append(f"{k}=\"{v}\"")
    return " " .join(parts) + ">"


def build_picture(rel_src: str, alt: str, attrs: Dict[str, str]) -> str:
    variants = src_to_variant_lists(rel_src)
    # Determine sizes: prefer existing sizes attr if present
    sizes_attr = attrs.get("sizes", "(min-width: 1024px) 50vw, 100vw")
    # Compute image intrinsic dimensions
    w, h = get_image_dims(rel_src)
    fallback_img = build_img_from_attrs(attrs, rel_src, alt, w, h)
    if not variants:
        return fallback_img
    avif_srcset = ", ".join([f"{path} {w}w" for path, w in variants["avif"]]) if variants.get("avif") else ""
    webp_srcset = ", ".join([f"{path} {w}w" for path, w in variants["webp"]]) if variants.get("webp") else ""
    lines: List[str] = ["<picture>"]
    if avif_srcset:
        lines.append(f"  <source type=\"image/avif\" srcset=\"{avif_srcset}\" sizes=\"{sizes_attr}\">")
    if webp_srcset:
        lines.append(f"  <source type=\"image/webp\" srcset=\"{webp_srcset}\" sizes=\"{sizes_attr}\">")
    lines.append(f"  {fallback_img}")
    lines.append("</picture>")
    return "\n".join(lines)


def update_file(path: str, alt_by_rel: Dict[str, Dict[str, str]]) -> bool:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    changed = False
    for node in find_imgs(html):
        rel_src = node.src
        # Try to pull alt from CSV mapping if available
        alt_meta = alt_by_rel.get(rel_src) or alt_by_rel.get(os.path.basename(rel_src))
        alt_text = (alt_meta or {}).get("alt_short_sv", node.alt)
        picture = build_picture(rel_src, alt_text, node.attrs)
        if picture != node.full:
            html = html.replace(node.full, picture)
            changed = True

    if changed:
        with open(path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(html)
    return changed


def collect_alt_map() -> Dict[str, Dict[str, str]]:
    alt_map: Dict[str, Dict[str, str]] = {}
    if not os.path.isfile(CSV_PATH):
        return alt_map
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rel = (row.get("original_path") or "").strip()
            if not rel:
                continue
            alt_map[rel] = {
                "alt_short_sv": (row.get("alt_short_sv") or "").strip(),
                # width/height could be filled later by a dimension pass
                "width": "",
                "height": "",
            }
            base = os.path.basename(rel)
            alt_map[base] = alt_map[rel]
    return alt_map


def main() -> int:
    alt_map = collect_alt_map()
    changed_total = 0
    for entry in os.listdir(BASE_DIR):
        if not entry.lower().endswith(".html"):
            continue
        path = os.path.join(BASE_DIR, entry)
        if update_file(path, alt_map):
            changed_total += 1
    print(f"Updated <picture> markup in {changed_total} HTML files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


