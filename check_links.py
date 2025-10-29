#!/usr/bin/env python3
import os
import re
from typing import List, Tuple

BASE_DIR = os.path.abspath(
    "/Users/nilsandersson/Library/CloudStorage/GoogleDrive-nils@several.club/My Drive/Several/Several Projects/Websites/Several.Club"
)

IMG_TAG_RE = re.compile(r"<img\b([^>]*)>", re.IGNORECASE)
ATTR_RE = re.compile(r"(\w+)\s*=\s*\"([^\"]*)\"", re.IGNORECASE)
HREF_RE = re.compile(r"href=\"([^\"]+)\"", re.IGNORECASE)
SRC_RE = re.compile(r"src=\"([^\"]+)\"", re.IGNORECASE)


def parse_attrs(attr_text: str):
    attrs = {}
    for k, v in ATTR_RE.findall(attr_text or ""):
        attrs[k.lower()] = v
    return attrs


def collect_paths_from_html(html: str) -> List[str]:
    paths: List[str] = []
    for m in SRC_RE.finditer(html):
        paths.append(m.group(1))
    for m in HREF_RE.finditer(html):
        paths.append(m.group(1))
    return paths


def is_local_path(p: str) -> bool:
    if not p or "://" in p or p.startswith("mailto:") or p.startswith("tel:"):
        return False
    if p.startswith("#"):
        return False
    return True


def main() -> int:
    broken: List[Tuple[str, str]] = []
    for entry in os.listdir(BASE_DIR):
        if not entry.lower().endswith(".html"):
            continue
        path = os.path.join(BASE_DIR, entry)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                html = f.read()
        except Exception:
            continue
        for ref in collect_paths_from_html(html):
            if not is_local_path(ref):
                continue
            # Normalize
            ref_clean = ref.split("?")[0].split("#")[0]
            if ref_clean.startswith("/"):
                # treat as project-root relative
                ref_clean = ref_clean.lstrip("/")
            fs_path = os.path.join(BASE_DIR, ref_clean)
            if not os.path.exists(fs_path):
                broken.append((entry, ref))
    if broken:
        print("Broken references:")
        for page, ref in broken:
            print(f"- {page}: {ref}")
        print(f"Total broken: {len(broken)}")
        return 1
    print("No broken local references found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
