#!/usr/bin/env python3
"""
Build Universal Music feed from filenames.
Actions:
- Clean _generated/UniversalMusic directory (non-recursive)
- Generate AVIF/WEBP variants for images in Assets/UniversalMusic
- Rebuild the case feed inside universal-music.html based on naming:
  universal-music-01.jpg  -> full width
  universal-music-02-01.jpg + universal-music-02-02.jpg -> two on one row
"""
from __future__ import annotations

import os
import re
from typing import Dict, List, Tuple


def get_repo_root() -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, ".."))


def list_images(directory: str) -> List[str]:
    exts = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
    out: List[str] = []
    for name in os.listdir(directory):
        lower = name.lower()
        _, ext = os.path.splitext(lower)
        if ext in exts:
            out.append(name)
    return sorted(out)


def parse_groups(files: List[str]) -> Dict[str, List[str]]:
    """
    Returns mapping: group 'NN' -> list of base names without extension
    """
    pat = re.compile(r"^universal-music-(\d{2})(?:-(\d{2}))?$", re.I)
    groups: Dict[str, List[str]] = {}
    for name in files:
        base = os.path.splitext(name)[0]
        m = pat.match(base)
        if not m:
            # Skip non-matching
            continue
        g, sub = m.group(1), m.group(2)
        groups.setdefault(g, [])
        groups[g].append(base)
    for g in list(groups.keys()):
        groups[g].sort()
    return dict(sorted(groups.items(), key=lambda kv: int(kv[0])))


def try_import_pillow():
    try:
        from PIL import Image  # noqa: F401
    except Exception:
        return False
    try:
        import pillow_avif  # noqa: F401
    except Exception:
        # ok if not available; AVIF may still be supported
        pass
    return True


def gen_variants_for_file(src_abs: str, gen_dir: str) -> List[str]:
    """
    Create AVIF/WEBP variants for one image.
    Returns the list of generated relative filenames (within gen_dir).
    """
    generated: List[str] = []
    try:
        from PIL import Image
    except Exception:
        return generated

    base_name = os.path.splitext(os.path.basename(src_abs))[0]
    widths = [320, 640, 960, 1280, 1600, 2000]
    try:
        with Image.open(src_abs) as img:
            w0, h0 = img.size
    except Exception:
        return generated

    def save_variant(fmt: str, width: int):
        nonlocal generated
        if width >= w0 and width != widths[0]:
            return
        # Resize with aspect ratio
        try:
            from PIL import Image as PILImage
            height = max(1, int(h0 * (width / float(w0))))
            resized = img.resize((width, height), PILImage.LANCZOS)
            if fmt == "webp":
                params = {"quality": 80}
            elif fmt == "avif":
                # Pillow AVIF quality scale differs; keep moderate value
                params = {"quality": 50}
            else:
                return
            out_name = f"{base_name}-{width}.{fmt}"
            out_abs = os.path.join(gen_dir, out_name)
            os.makedirs(os.path.dirname(out_abs), exist_ok=True)
            resized.save(out_abs, fmt.upper(), **params)
            generated.append(out_name)
        except Exception:
            return

    # Reopen to avoid potential lazy load issues in Pillow
    try:
        from PIL import Image
        img = Image.open(src_abs)
    except Exception:
        return generated

    for w in widths:
        save_variant("webp", w)
        save_variant("avif", w)
    try:
        img.close()
    except Exception:
        pass
    return generated


def rebuild_case_html(html_abs: str, groups: Dict[str, List[str]], assets_rel_dir: str, gen_rel_dir: str) -> None:
    """
    Replace the content inside the .case-images-container with new markup.
    """
    with open(html_abs, "r", encoding="utf-8") as f:
        html = f.read()

    container_marker = '<div class="case-images-container">'
    end_marker = '<div id="w-node-_6d701267'
    start_idx = html.find(container_marker)
    if start_idx == -1:
        return
    start_idx += len(container_marker)
    end_idx = html.find(end_marker, start_idx)
    if end_idx == -1:
        # Fallback: close of container's parent
        end_idx = html.find("</div>", start_idx)
        if end_idx == -1:
            return

    def picture_block(base: str, alt_label: str) -> str:
        # Use the same sizes signature used elsewhere in the site
        # Two tiers: large and small (mirroring other cases)
        avif_large = f'{gen_rel_dir}/{base}-640.avif 640w, {gen_rel_dir}/{base}-1280.avif 1280w, {gen_rel_dir}/{base}-2000.avif 2000w'
        webp_large = f'{gen_rel_dir}/{base}-640.webp 640w, {gen_rel_dir}/{base}-1280.webp 1280w, {gen_rel_dir}/{base}-2000.webp 2000w'
        avif_small = f'{gen_rel_dir}/{base}-320.avif 320w, {gen_rel_dir}/{base}-640.avif 640w'
        webp_small = f'{gen_rel_dir}/{base}-320.webp 320w, {gen_rel_dir}/{base}-640.webp 640w'
        img_src = f'{assets_rel_dir}/{base}.jpg'
        # Indentation matches surrounding HTML (two spaces)
        return (
            "\n              <picture>\n"
            f"  <source type=\"image/avif\" srcset=\"{avif_large}\" sizes=\"(min-width: 1024px) 50vw, 100vw\">\n"
            f"  <source type=\"image/webp\" srcset=\"{webp_large}\" sizes=\"(min-width: 1024px) 50vw, 100vw\">\n"
            "  <picture>\n"
            f"  <source type=\"image/avif\" srcset=\"{avif_small}\" sizes=\"(min-width: 1024px) 50vw, 100vw\">\n"
            f"  <source type=\"image/webp\" srcset=\"{webp_small}\" sizes=\"(min-width: 1024px) 50vw, 100vw\">\n"
            f"  <img src=\"{img_src}\" alt=\"Universal Music – image {alt_label}\" loading=\"lazy\" decoding=\"async\">\n"
            "  </picture>\n"
            "</picture>\n"
        )

    # Build markup
    blocks: List[str] = []
    for group, bases in groups.items():
        # Determine if pair (has -01 and -02) or single
        parts = sorted(bases)
        if any(b.endswith("-01") for b in parts) and any(b.endswith("-02") for b in parts):
            # pair
            pair = []
            for suffix, label in [("-01", f"{group}.1"), ("-02", f"{group}.2")]:
                base = next((b for b in parts if b.endswith(suffix)), None)
                if base:
                    pair.append(picture_block(base, label))
            if pair:
                blocks.append("\n              <div class=\"half-width-container\">" + "".join(pair) + "              </div>\n")
        else:
            # single: pick the first
            base = parts[0]
            blocks.append(picture_block(base, group))

    new_inner = "\n" + "".join(blocks) + "              "
    new_html = html[:start_idx] + new_inner + html[end_idx:]

    # Update preload in head to the first single image (first group)
    first_group = next(iter(groups.keys()), None)
    if first_group:
        # Prefer a single-item group; else use the first image of the first group
        first_bases = groups[first_group]
        first_base = sorted(first_bases)[0]
        href = f'{assets_rel_dir}/{first_base}.jpg'
        imagesrcset = f'{gen_rel_dir}/{first_base}-320.webp 320w, {gen_rel_dir}/{first_base}-640.webp 640w'
        new_html = re.sub(
            r'<link rel="preload" as="image" href="[^"]+" imagesrcset="[^"]+" imagesizes="[^"]+">',
            f'<link rel="preload" as="image" href="{href}" imagesrcset="{imagesrcset}" imagesizes="(min-width: 1024px) 50vw, 100vw">',
            new_html,
            count=1,
        )

    with open(html_abs, "w", encoding="utf-8") as f:
        f.write(new_html)


def main() -> int:
    root = get_repo_root()
    assets_dir = os.path.join(root, "Assets/UniversalMusic")
    gen_dir = os.path.join(root, "Assets/_generated/UniversalMusic")
    html_abs = os.path.join(root, "universal-music.html")
    assets_rel_dir = "Assets/UniversalMusic"
    gen_rel_dir = "Assets/_generated/UniversalMusic"

    # Ensure directories
    os.makedirs(assets_dir, exist_ok=True)
    os.makedirs(gen_dir, exist_ok=True)

    # Enumerate files and build groups
    files = list_images(assets_dir)
    bases = [os.path.splitext(n)[0] for n in files]
    groups = parse_groups(files)
    if not groups:
        print("No Universal Music images found to build feed.")
        return 0

    # Clear _generated/UniversalMusic to avoid stale files
    for name in os.listdir(gen_dir):
        try:
            os.remove(os.path.join(gen_dir, name))
        except Exception:
            pass

    # Generate variants (if Pillow available)
    pillow_ok = try_import_pillow()
    if pillow_ok:
        for name in files:
            src_abs = os.path.join(assets_dir, name)
            gen_variants_for_file(src_abs, gen_dir)
        print("Generated AVIF/WEBP variants for Universal Music.")
    else:
        print("Pillow not available; skipped generating variants. Markup will fall back to <img>.")

    # Rewrite HTML feed
    rebuild_case_html(html_abs, groups, assets_rel_dir, gen_rel_dir)
    print("Rewrote universal-music.html feed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


