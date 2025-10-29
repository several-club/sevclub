#!/usr/bin/env python3
import csv
import os
import sys
from typing import Dict, List, Optional, Tuple


BASE_DIR = os.path.abspath(
    "/Users/nilsandersson/Library/CloudStorage/GoogleDrive-nils@several.club/My Drive/Several/Several Projects/Websites/Several.Club"
)
ASSETS_DIR = os.path.join(BASE_DIR, "Assets")
CSV_PATH = os.path.join(BASE_DIR, "assets_proposals.csv")
GENERATED_DIR = os.path.join(ASSETS_DIR, "_generated")


def is_image_path(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in {".jpg", ".jpeg", ".png", ".webp", ".avif"}


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def try_import_pillow():
    try:
        from PIL import Image  # noqa: F401
    except Exception as e:
        print("Pillow is required. Install with: python3 -m pip install --user pillow pillow-avif-plugin", file=sys.stderr)
        raise
    # Try to register avif plugin if present
    try:
        import pillow_avif  # noqa: F401
    except Exception:
        pass


def open_image_abs(abs_path: str):
    from PIL import Image
    img = Image.open(abs_path)
    # Defer loading until needed; convert when saving
    return img


def save_variant(img, dest_abs: str, format_hint: str, width: int, quality: int = 82, lossless: bool = False) -> bool:
    try:
        # Compute height with aspect ratio
        w0, h0 = img.size
        if width >= w0:
            # Skip upscaling
            return False
        height = int(h0 * (width / float(w0))) or 1
        from PIL import Image
        resized = img.resize((width, height), Image.LANCZOS)

        params = {}
        fmt = format_hint.upper()
        if fmt == "WEBP":
            params = {"quality": quality}
            if lossless:
                params["lossless"] = True
        elif fmt == "JPEG" or fmt == "JPG":
            params = {"quality": quality, "optimize": True, "progressive": True}
        elif fmt == "AVIF":
            # Pillow-AVIF plugin registers format "AVIF"
            params = {"quality": max(30, min(62, int(quality * 0.75)))}
        else:
            # Fallback to PNG
            fmt = "PNG"
        ensure_dir(os.path.dirname(dest_abs))
        resized.save(dest_abs, fmt, **params)
        return True
    except Exception as e:
        return False


def main() -> int:
    try_import_pillow()

    if not os.path.isfile(CSV_PATH):
        print(f"CSV not found: {CSV_PATH}", file=sys.stderr)
        return 1

    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    widths = [320, 640, 960, 1280, 1600, 2000]
    generated_count = 0
    avif_supported = True

    # Quick probe if AVIF is supported by Pillow
    try:
        from PIL import Image
        if "AVIF" not in Image.registered_extensions().values():
            avif_supported = False
    except Exception:
        avif_supported = False

    for row in rows:
        rel = (row.get("original_path") or "").strip()
        if not rel or not is_image_path(rel):
            continue
        abs_path = os.path.join(BASE_DIR, rel)
        if not os.path.isfile(abs_path):
            continue
        subdir = os.path.dirname(os.path.relpath(abs_path, ASSETS_DIR))
        base = os.path.splitext(os.path.basename(abs_path))[0]
        try:
            img = open_image_abs(abs_path)
        except Exception:
            continue
        w0, h0 = getattr(img, "size", (0, 0))
        if not w0 or not h0:
            continue
        # Determine if PNG is transparent to choose lossless webp
        lossless_webp = False
        try:
            lossless_webp = (img.mode in ("RGBA", "LA")) or ("transparency" in img.info)
        except Exception:
            lossless_webp = False

        # Generate WebP
        for w in widths:
            if w >= w0 and w != widths[0]:
                # allow smallest width even if upscale? No. Skip all >= original
                continue
            dest_rel = os.path.join("Assets/_generated", subdir, f"{base}-{w}.webp").replace("\\", "/")
            dest_abs = os.path.join(BASE_DIR, dest_rel)
            if os.path.exists(dest_abs):
                continue
            if save_variant(img, dest_abs, "WEBP", w, quality=80, lossless=lossless_webp):
                generated_count += 1

        # Generate AVIF if supported
        if avif_supported:
            for w in widths:
                if w >= w0 and w != widths[0]:
                    continue
                dest_rel = os.path.join("Assets/_generated", subdir, f"{base}-{w}.avif").replace("\\", "/")
                dest_abs = os.path.join(BASE_DIR, dest_rel)
                if os.path.exists(dest_abs):
                    continue
                if save_variant(img, dest_abs, "AVIF", w, quality=50):
                    generated_count += 1

    print(f"Generated {generated_count} image variants into {GENERATED_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


