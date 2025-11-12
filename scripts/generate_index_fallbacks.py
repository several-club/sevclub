#!/usr/bin/env python3
import os
import re
from pathlib import Path
from typing import Optional

try:
    from PIL import Image  # type: ignore
except Exception as exc:
    raise SystemExit("Pillow is required (pip install Pillow). Error: {}".format(exc))


WORKSPACE = Path("/Users/nilsandersson/Library/CloudStorage/GoogleDrive-nils@several.club/My Drive/Several/Several Projects/Websites/several.club")
GENERATED_DIR = WORKSPACE / "Assets" / "_generated" / "Index"
TARGET_DIR = WORKSPACE / "Assets" / "Index"


WEBP_PATTERN = re.compile(r"^index-(?P<slug>[a-z0-9\-]+)-cover-(?P<size>\d+)\.webp$", re.IGNORECASE)

# Preferred sizes for source images (descending priority)
PREFERRED_SIZES = ["1280", "960", "640", "320", "1600", "2000"]


def find_slug_to_sources() -> dict[str, dict[str, Path]]:
    slug_to_size_to_path: dict[str, dict[str, Path]] = {}
    if not GENERATED_DIR.exists():
        return slug_to_size_to_path
    for entry in GENERATED_DIR.iterdir():
        if not entry.is_file():
            continue
        m = WEBP_PATTERN.match(entry.name)
        if not m:
            continue
        slug = m.group("slug")
        size = m.group("size")
        slug_to_size_to_path.setdefault(slug, {})[size] = entry
    return slug_to_size_to_path


def pick_best_source(size_to_path: dict[str, Path]) -> Optional[Path]:
    for size in PREFERRED_SIZES:
        if size in size_to_path:
            return size_to_path[size]
    # fallback: any available
    if size_to_path:
        # deterministic pick
        return size_to_path[sorted(size_to_path.keys())[0]]
    return None


def convert_image_to_jpg(src_path: Path, dest_path: Path) -> None:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src_path) as im:
        # Ensure RGB (drop alpha if present)
        if im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        elif im.mode == "L":
            im = im.convert("RGB")
        im.save(dest_path, format="JPEG", quality=82, optimize=True, progressive=True)


def ensure_coop73_from_png():
    src_png = TARGET_DIR / "index-coop73-cover.png"
    dest_jpg = TARGET_DIR / "index-coop73-cover.jpg"
    if src_png.exists() and not dest_jpg.exists():
        convert_image_to_jpg(src_png, dest_jpg)


def main() -> int:
    slug_to_sources = find_slug_to_sources()
    # Generate JPG for each slug found in _generated
    for slug, size_to_path in slug_to_sources.items():
        dest = TARGET_DIR / f"index-{slug}-cover.jpg"
        if dest.exists():
            continue
        best_src = pick_best_source(size_to_path)
        if not best_src:
            continue
        try:
            convert_image_to_jpg(best_src, dest)
        except Exception as exc:
            print(f"[WARN] Failed to convert {best_src} -> {dest}: {exc}")
            continue

    # Special case: coop73 PNG -> JPG
    ensure_coop73_from_png()
    print("Done generating index JPG fallbacks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


