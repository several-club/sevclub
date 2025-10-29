#!/usr/bin/env python3
import os
import re
from typing import Dict, List, Optional


BASE_DIR = os.path.abspath(
    "/Users/nilsandersson/Library/CloudStorage/GoogleDrive-nils@several.club/My Drive/Several/Several Projects/Websites/Several.Club"
)
ASSETS_DIR = os.path.join(BASE_DIR, "Assets")


HREF_RE = re.compile(r"href=\"([^\"]+)\"", re.IGNORECASE)
SRC_RE = re.compile(r"src=\"([^\"]+)\"", re.IGNORECASE)


def norm_key(name: str) -> str:
    base = os.path.basename(name)
    base = base.split("?")[0].split("#")[0]
    root, ext = os.path.splitext(base)
    key = re.sub(r"[^a-z0-9]", "", root.lower()) + ext.lower()
    return key


def build_assets_index() -> Dict[str, List[str]]:
    index: Dict[str, List[str]] = {}
    for root, _, files in os.walk(ASSETS_DIR):
        for fn in files:
            if fn.startswith("."):
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, BASE_DIR).replace("\\", "/")
            key = norm_key(fn)
            index.setdefault(key, []).append(rel)
    return index


def choose_best_match(candidates: List[str], page_name: str) -> Optional[str]:
    if not candidates:
        return None
    # Prefer candidate whose path contains page slug
    page_slug = os.path.splitext(page_name.lower())[0]
    ranked = sorted(
        candidates,
        key=lambda p: (
            0 if page_slug and page_slug in p.lower() else 1,
            len(p),
        ),
    )
    return ranked[0]


def replace_refs_in_html(path: str, assets_index: Dict[str, List[str]]) -> bool:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()

    changed = False

    def repl(match: re.Match) -> str:
        nonlocal changed
        orig = match.group(1)
        if not orig or "://" in orig or orig.startswith(("mailto:", "tel:", "#")):
            return match.group(0)
        ref_clean = orig.split("?")[0].split("#")[0]
        ref_abs = os.path.join(BASE_DIR, ref_clean.lstrip("/"))
        if os.path.exists(ref_abs):
            return match.group(0)
        # Special-case common images/ -> Assets/images/ mapping
        special_map = {
            "images/favicon.png": "Assets/images/images-favicon.png",
            "images/webclip.png": "Assets/images/images-webclip.png",
            "images/Property-1Default.svg": "Assets/images/images-property-1default.svg",
            "images/Property-1Variant2.svg": "Assets/images/images-property-1variant2.svg",
            # About page legacy
            "images/hej.jpg": "Assets/About/about-hej.jpg",
            "images/About_02.jpg": "Assets/About/about-02-01.jpg",
            "images/About_04.jpg": "Assets/About/about-04-01.jpg",
            "images/About_06.jpg": "Assets/About/about-04-01.jpg",
            "images/Frame-1000001961.jpg": "Assets/About/about-01-01.jpg",
            # Index/Bord legacy
            "Assets/index/bord_thumbnail.jpg": "Assets/Index/index-bord-cover.jpg",
            "Assets/Index/Cervera_cover.jpg": "Assets/Cervera/cervera-01.avif",
            "Assets/Cervera/cervera_1.avif": "Assets/Cervera/cervera-01.avif",
            # Style guide placeholders
            "images/image.svg": "Assets/images/images-property-1default.svg",
            "images/client-first-logo-white.svg": "Assets/images/images-property-1default.svg",
            "images/hamburger-close.svg": "Assets/images/images-property-1default.svg",
            "images/hamburger_open.svg": "Assets/images/images-property-1variant2.svg",
            # Contact/Services hero
            "images/hemsida-jobb_1hemsida-jobb.avif": "Assets/images/images-og-image-635.webp",
            # Shop placeholders
            "images/shop_img_02.jpg": "Assets/Shop/shop-184dd2a85fb3742d04350fe3e3e67f2f-shop-img-02-p-800.jpg",
            "images/shop_img_2shop_img_01.avif": "Assets/Shop/shop-184dd2a85fb3742d04350fe3e3e67f2f-shop-img-02-p-800.jpg",
            "images/shop_img_4shop_img_03.avif": "Assets/Shop/shop-184dd2a85fb3742d04350fe3e3e67f2f-shop-img-02-p-800.jpg",
            # Gallnö fallbacks
            "images/gallno2_1gallno2.avif": "Assets/Gallno/gallno-02-01.avif",
            "images/gallno3_1gallno3.avif": "Assets/Gallno/gallno-06.avif",
            "images/gallno4_1gallno4.avif": "Assets/Gallno/gallno-07.avif",
            "images/gallno6_1gallno6.avif": "Assets/Gallno/gallno-06.avif",
            "images/gallno7_1gallno7.avif": "Assets/Gallno/gallno-07.avif",
            "images/gallno9_1gallno9.avif": "Assets/Gallno/gallno-07.avif",
            "images/gallno10_1gallno10.avif": "Assets/Gallno/gallno-07.avif",
            # Bord specifics
            "Assets/Bord/Bord_1.jpg": "Assets/Bord/bord-01-01.jpg",
            "Assets/Bord/Bord_6.jpg": "Assets/Bord/bord-06-01.jpg",
        }
        if ref_clean in special_map:
            new_rel = special_map[ref_clean]
            changed = True
            return match.group(0).replace(orig, new_rel)

        # Pattern: Assets/Index/{Name}_cover.jpg -> Assets/Index/index-{name}-cover.jpg
        if ref_clean.lower().startswith("assets/index/") and ref_clean.lower().endswith("_cover.jpg"):
            name_part = os.path.splitext(os.path.basename(ref_clean))[0][:-6]
            slug = re.sub(r"[^a-z0-9]+", "-", name_part.lower()).strip("-")
            candidate = f"Assets/Index/index-{slug}-cover.jpg"
            if os.path.exists(os.path.join(BASE_DIR, candidate)):
                changed = True
                return match.group(0).replace(orig, candidate)

        # Pattern: Goalplan xN(.M).ext -> goalplan-xN-0M.ext or goalplan-xN.ext
        if ref_clean.lower().startswith("assets/goalplan/x"):
            base = os.path.basename(ref_clean)
            m = re.match(r"x(\d+)(?:\.(\d+))?(\.[a-zA-Z0-9]+)$", base, re.IGNORECASE)
            if m:
                n1, n2, ext = m.groups()
                if n2:
                    candidate = f"Assets/Goalplan/goalplan-x{int(n1)}-{int(n2):02d}{ext.lower()}"
                else:
                    candidate = f"Assets/Goalplan/goalplan-x{int(n1)}{ext.lower()}"
                if os.path.exists(os.path.join(BASE_DIR, candidate)):
                    changed = True
                    return match.group(0).replace(orig, candidate)

        # Pattern: Assets/Bord/Bord_[N][.M].ext -> try known bord names
        if ref_clean.lower().startswith("assets/bord/bord_"):
            base = os.path.basename(ref_clean)
            m = re.match(r"bord_(\d+)(?:\.(\d+))?\.[a-zA-Z0-9]+$", base, re.IGNORECASE)
            if m:
                n1, n2 = m.groups()
                candidates_try = []
                if n2:
                    candidates_try.append(f"Assets/Bord/bord-{int(n1):02d}-{int(n2):02d}.jpg")
                # Also try single index variant names
                candidates_try.append(f"Assets/Bord/bord-{int(n1):02d}.jpg")
                # Known special cases
                if int(n1) == 2:
                    candidates_try.append("Assets/Bord/bord-02.gif")
                for cand in candidates_try:
                    if os.path.exists(os.path.join(BASE_DIR, cand)):
                        changed = True
                        return match.group(0).replace(orig, cand)

        # Try lookup by normalized basename in Assets
        key = norm_key(ref_clean)
        candidates = assets_index.get(key) or []
        best = choose_best_match(candidates, os.path.basename(path))
        if best:
            changed = True
            return match.group(0).replace(orig, best)
        # Fuzzy fallback: find any asset whose normalized key contains the normalized base (or vice versa)
        base_key = norm_key(ref_clean)
        fuzzy_candidates: List[str] = []
        for k, vals in assets_index.items():
            if base_key and (base_key in k or k in base_key):
                fuzzy_candidates.extend(vals)
        best = choose_best_match(fuzzy_candidates, os.path.basename(path))
        if best:
            changed = True
            return match.group(0).replace(orig, best)
        return match.group(0)

    new_html = SRC_RE.sub(repl, html)
    new_html = HREF_RE.sub(repl, new_html)

    if new_html != html:
        with open(path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(new_html)
        return True
    return False


def main() -> int:
    index = build_assets_index()
    changed_files = 0
    for entry in os.listdir(BASE_DIR):
        if not entry.lower().endswith(".html"):
            continue
        html_path = os.path.join(BASE_DIR, entry)
        if replace_refs_in_html(html_path, index):
            changed_files += 1
    print(f"Fixed references in {changed_files} HTML files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


