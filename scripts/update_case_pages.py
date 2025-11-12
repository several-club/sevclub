#!/usr/bin/env python3
import re
from pathlib import Path
from typing import Optional

WORKSPACE = Path("/Users/nilsandersson/Library/CloudStorage/GoogleDrive-nils@several.club/My Drive/Several/Several Projects/Websites/several.club")
ASSETS = WORKSPACE / "Assets"

CASE_FILES = [
    "backfabrik.html",
    "bailet.html",
    "blankens.html",
    "bord.html",
    "cervera.html",
    "claes-dalen.html",
    "coop-port-73.html",
    "coop-skargarden.html",
    "cucina-povera.html",
    "gallno.html",
    "goalplan.html",
    "hyper-island.html",
    "jeanerica.html",
    "jeanerica-imparfaite.html",
    "lindbergs.html",
    "modha.html",
    "remm.html",
    "snacka-om-sjukt.html",
    "stefan-ekengren.html",
    "stelly.html",
    "universal-music.html",
]

IMG_FALLBACK_RE = re.compile(r'(<img[^>]+src=")(Assets/([^/]+)/([^"]+?))\.(webp|avif|png)("[^>]*>)', re.IGNORECASE)
VIDEO_TAG_RE = re.compile(r'(<video)([^>]*)(>)', re.IGNORECASE)
VIDEO_SOURCE_RE = re.compile(r'(<source[^>]+src=")([^"]+)(")', re.IGNORECASE)


def pick_existing_fallback(case_dir: Path, basename: str) -> Optional[str]:
    # prefer .jpg then .jpeg then .png then .webp
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = case_dir / f"{basename}{ext}"
        if p.exists():
            return f"Assets/{case_dir.name}/{basename}{ext}"
    return None


def get_default_poster(case_dir: Path) -> Optional[str]:
    jpgs = sorted(case_dir.glob("*.jpg"))
    if jpgs:
        return f"Assets/{case_dir.name}/{jpgs[0].name}"
    return None


def asset_exists(url: str) -> bool:
    # Only check local assets under Assets/
    if not url.startswith("Assets/"):
        return True
    path = WORKSPACE / url
    return path.exists()


def update_file(html_path: Path) -> None:
    text = html_path.read_text(encoding="utf-8")

    # Update <img> fallbacks within <picture>
    def repl_img(m: re.Match) -> str:
        prefix, asset_prefix, case_name, file_base, _ext, suffix = m.groups()
        case_dir = ASSETS / case_name
        target = pick_existing_fallback(case_dir, file_base)
        if target:
            return f'{prefix}{target}{suffix}'
        return m.group(0)

    text = IMG_FALLBACK_RE.sub(repl_img, text)

    # Add poster to <video> if missing
    def repl_video(m: re.Match) -> str:
        open_tag, attrs, close_char = m.groups()
        if "poster=" in attrs:
            return m.group(0)
        # try to infer case dir by finding first local source in the next lines
        # fallback to filename-derived case
        case_dir_name = infer_case_dir_from_filename(html_path.name)
        case_dir = ASSETS / case_dir_name if case_dir_name else None
        poster = None
        if case_dir and case_dir.exists():
            poster = get_default_poster(case_dir)
        if poster:
            return f'{open_tag}{attrs} poster="{poster}"{close_char}'
        return m.group(0)

    text = VIDEO_TAG_RE.sub(repl_video, text)

    # Drop or fix broken <source> tags pointing to non-existent local files
    def repl_source(m: re.Match) -> str:
        prefix, url, suffix = m.groups()
        if url.startswith("Assets/") and not asset_exists(url):
            # attempt simple fix: if .mov -> .webm, if .webm -> .mp4
            alt_order = []
            if url.endswith(".mov"):
                alt_order = [url[:-4] + ".webm", url[:-4] + ".mp4"]
            elif url.endswith(".webm"):
                alt_order = [url[:-5] + ".mp4"]
            else:
                alt_order = []
            for alt in alt_order:
                if asset_exists(alt):
                    return f'{prefix}{alt}{suffix}'
            # otherwise, remove this source entirely
            return ""
        # Coop Port 73 local → remote CDN
        if url.startswith("Assets/Coop73/"):
            remote = "https://several-storage.b-cdn.net/Coop%20Port%2073/" + url.split("Assets/Coop73/")[1]
            return f'{prefix}{remote}{suffix}'
        return m.group(0)

    text = VIDEO_SOURCE_RE.sub(repl_source, text)

    # Also rewrite any direct video src attributes that are local Coop73 paths
    text = re.sub(
        r'(src=")Assets/Coop73/([^"]+)(")',
        r'\1https://several-storage.b-cdn.net/Coop%20Port%2073/\2\3',
        text,
        flags=re.IGNORECASE,
    )

    html_path.write_text(text, encoding="utf-8")


def infer_case_dir_from_filename(filename: str) -> Optional[str]:
    base = filename.replace(".html", "")
    mapping = {
        "claes-dalen": "claes-dalen",
        "coop-port-73": "Coop73",
        "coop-skargarden": "CoopSkargarden",
        "cucina-povera": "Cucina",
        "stefan-ekengren": "StefanEkengren",
        "universal-music": "UniversalMusic",
        "snacka-om-sjukt": "SnackaOmSjukt",
        "jeanerica-imparfaite": "jeanerica-imparfaite",
        # default: TitleCase of hyphenated names
    }
    if base in mapping:
        return mapping[base]
    # Try TitleCase without hyphens (Index directories often TitleCase)
    parts = base.split("-")
    guess = "".join(p.capitalize() for p in parts)
    if (ASSETS / guess).exists():
        return guess
    # Try as-is (already TitleCase directories like Backfabrik)
    if (ASSETS / base).exists():
        return base
    return None


def main() -> int:
    for fname in CASE_FILES:
        path = WORKSPACE / fname
        if path.exists():
            update_file(path)
    print("Case pages updated: fallbacks standardized and posters added where possible.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


