#!/usr/bin/env python3
import os
import re
import shutil
from pathlib import Path
from typing import Optional

try:
    from PIL import Image  # type: ignore
except Exception as exc:
    raise SystemExit("Pillow is required (pip install Pillow). Error: {}".format(exc))


WORKSPACE = Path("/Users/nilsandersson/Library/CloudStorage/GoogleDrive-nils@several.club/My Drive/Several/Several Projects/Websites/several.club")
ASSETS = WORKSPACE / "Assets"
GENERATED = ASSETS / "_generated"

PREFERRED_SIZES = ["1280", "960", "640", "320", "1600", "2000"]


def convert_to_jpg(src: Path, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(src) as im:
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            elif im.mode == "L":
                im = im.convert("RGB")
            im.save(dest, format="JPEG", quality=82, optimize=True, progressive=True)
        return True
    except Exception as exc:
        print(f"[WARN] Cannot convert {src} -> {dest}: {exc}")
        return False


def find_best_generated_source(case_dir_name: str, base: str) -> Optional[Path]:
    gen_dir = GENERATED / case_dir_name
    if not gen_dir.exists():
        return None
    candidates = []
    for size in PREFERRED_SIZES:
        for ext in ("webp", "avif"):
            p = gen_dir / f"{base}-{size}.{ext}"
            if p.exists():
                candidates.append(p)
        # early exit on first by order
        if candidates:
            return candidates[0]
    # fallback: any webp of that base
    for p in gen_dir.glob(f"{base}-*.webp"):
        return p
    return None


def generate_fallbacks_for_case_dir(case_dir: Path) -> None:
    if not case_dir.is_dir():
        return
    case_name = case_dir.name
    for entry in case_dir.iterdir():
        if not entry.is_file():
            continue
        if entry.suffix.lower() not in (".webp", ".avif", ".png", ".jpeg"):
            continue
        base = entry.stem  # without suffix
        dest = case_dir / f"{base}.jpg"
        if dest.exists():
            continue
        src_for_conversion: Optional[Path] = None
        if entry.suffix.lower() in (".webp", ".png", ".jpg", ".jpeg"):
            src_for_conversion = entry
        else:
            # e.g. .avif: prefer generated webp
            src_for_conversion = find_best_generated_source(case_name, base)
            if src_for_conversion is None:
                # try sibling with .webp or .png
                for alt_ext in (".webp", ".png", ".jpg", ".jpeg"):
                    alt = case_dir / f"{base}{alt_ext}"
                    if alt.exists():
                        src_for_conversion = alt
                        break
        if src_for_conversion:
            convert_to_jpg(src_for_conversion, dest)


def ensure_about_assets():
    src_dir = ASSETS / "About_NILS GÅ IGENOM"
    dst_dir = ASSETS / "About"
    if not src_dir.exists():
        return
    dst_dir.mkdir(parents=True, exist_ok=True)
    copy_names = [
        "about-hej.jpg",
        "about-02-01.jpg",
        "about-01-01.jpg",
        "about-04-01.jpg",
        # hashed file referenced by contact/services
    ]
    # copy by explicit names
    for name in copy_names:
        s = src_dir / name
        d = dst_dir / name
        if s.exists() and not d.exists():
            shutil.copy2(s, d)
    # copy any 'about-86726...' if present
    for f in src_dir.glob("about-86726*.webp"):
        d = dst_dir / f.name
        if not d.exists():
            shutil.copy2(f, d)


def main() -> int:
    # Generate JPG fallbacks for each case directory under Assets (excluding known non-case folders)
    exclude = {"Index", "_generated", "images", "videos"}
    for case_dir in ASSETS.iterdir():
        if not case_dir.is_dir():
            continue
        if case_dir.name in exclude:
            continue
        generate_fallbacks_for_case_dir(case_dir)
    ensure_about_assets()
    print("Done generating case JPG fallbacks and ensuring About assets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


