#!/usr/bin/env python3
import csv
import os
import re
from html.parser import HTMLParser
from typing import Dict, List, Optional, Set, Tuple


BASE_DIR = os.path.abspath(
    "/Users/nilsandersson/Library/CloudStorage/GoogleDrive-nils@several.club/My Drive/Several/Several Projects/Websites/Several.Club"
)
CSV_PATH = os.path.join(BASE_DIR, "assets_proposals.csv")


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


class TagCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_tags_container = False
        self.in_case_title = False
        self.current_tags: List[str] = []
        self.case_titles: List[str] = []
        self._stack: List[str] = []

    def handle_starttag(self, tag: str, attrs):
        self._stack.append(tag)
        classes = {k: v for k, v in attrs}.get("class", "")
        if tag == "div" and "container-text" in classes and "tags" in classes:
            self.in_tags_container = True
        if tag in ("h1", "h2", "h3"):
            if ("heading-style-h3" in classes) or (tag == "h1"):
                self.in_case_title = True

    def handle_endtag(self, tag: str):
        if self._stack:
            self._stack.pop()
        if tag == "div" and self.in_tags_container:
            self.in_tags_container = False
        if tag in ("h1", "h2", "h3") and self.in_case_title:
            self.in_case_title = False

    def handle_data(self, data: str):
        text = data.strip()
        if not text:
            return
        if self.in_tags_container:
            # Tags often reside in <p> or <h3> within the container
            # Filter out slashes used as separators
            if text != "/":
                self.current_tags.append(text)
        if self.in_case_title:
            # Capture likely case titles (will filter later)
            self.case_titles.append(text)


class ImgAltCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.alts: Dict[str, str] = {}
        self._stack: List[str] = []

    def handle_starttag(self, tag: str, attrs):
        self._stack.append(tag)
        if tag.lower() == "img":
            attr = {k.lower(): v for k, v in attrs}
            src = (attr.get("src") or "").strip()
            alt = (attr.get("alt") or "").strip()
            if src:
                self.alts[src] = alt
        if tag.lower() == "video":
            attr = {k.lower(): v for k, v in attrs}
            label = (attr.get("aria-label") or "").strip()
            # We'll store video aria-labels under a pseudo src key later when we see <source>

    def handle_endtag(self, tag: str):
        if self._stack:
            self._stack.pop()


def read_file(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None


def collect_project_tags() -> Dict[str, Set[str]]:
    tags_by_project: Dict[str, Set[str]] = {}
    for entry in os.listdir(BASE_DIR):
        if not entry.lower().endswith(".html"):
            continue
        html_path = os.path.join(BASE_DIR, entry)
        content = read_file(html_path)
        if not content:
            continue
        parser = TagCollector()
        parser.feed(content)
        # Determine project slug from filename (e.g., backfabrik.html -> backfabrik)
        proj_slug = slugify(os.path.splitext(entry)[0])
        # Collect tags that look like services (avoid generic words)
        tags: Set[str] = set()
        for t in parser.current_tags:
            t_clean = re.sub(r"\s+", " ", t).strip()
            # skip separators or empty
            if not t_clean or t_clean == "/":
                continue
            # Normalize capitalization (Title Case for readability)
            t_norm = t_clean.strip()
            tags.add(t_norm)
        if tags:
            tags_by_project.setdefault(proj_slug, set()).update(tags)
    return tags_by_project


def detect_subject_from_name(name: str, ext: str, existing_alt: str) -> str:
    name_l = name.lower()
    alt_l = (existing_alt or "").lower()
    if "logo" in name_l or "logotyp" in name_l or "logo" in alt_l:
        return "Logo"
    if ext.lower() == ".svg" and ("icon" in name_l or "icons" in name_l or "illustration" in alt_l):
        return "Illustration"
    if any(k in name_l for k in ["menu", "poster", "print", "card"]):
        return "Print Materials"
    if any(k in name_l for k in ["web", "site", "ui", "ux"]) or "website" in alt_l:
        return "Website"
    if any(k in name_l for k in ["typo", "type", "font"]):
        return "Typography"
    if any(k in name_l for k in ["guideline", "manual"]):
        return "Brand Guidelines"
    if any(k in name_l for k in ["video", ".mp4", ".webm", ".mov"]):
        return "Video"
    if any(k in name_l for k in ["photo", "photography", "interior"]):
        return "Photography"
    if any(k in name_l for k in ["element", "detail"]):
        return "Design Elements"
    return "Brand Identity"


def is_generic_alt(text: str) -> bool:
    if not text:
        return True
    t = text.strip().lower()
    # Generic patterns to replace
    generic_words = [
        "visual ",
        "branding design",
        "branding material",
        "brand elements",
        "brand application",
        "final design",
        "final showcase",
        "case logo",
        "case thumbnail",
        "thumbnail image",
    ]
    if any(g in t for g in generic_words):
        return True
    # Visual 1.1, 8.2 etc
    if re.search(r"visual\s*\d+(?:\.\d+)?", t):
        return True
    if re.search(r"\b\d+\.\d+\b", t):
        return True
    return False


def compose_alt(project_name: str, subject: str, services: List[str]) -> Tuple[str, str]:
    # Choose up to two relevant services to keep alt short
    svc = [s for s in services if s and s != "/"]
    if subject == "Logo" and not any("Logo" in s for s in svc):
        svc = ["Logo Design"] + svc
    # Deduplicate while preserving order
    seen: Set[str] = set()
    svc_unique: List[str] = []
    for s in svc:
        if s not in seen:
            svc_unique.append(s)
            seen.add(s)
    svc_short = ", ".join(svc_unique[:2]) if svc_unique else "Visual Identity"

    alt_short = f"{project_name} — {subject.lower()}, {svc_short}".strip().rstrip(", ")
    # Long: concise sentence
    # Example: Backfabrik: visual identity and logo applied across brand elements.
    subject_phrase = subject.lower()
    services_phrase = ", ".join(svc_unique[:3]) if svc_unique else "brand design"
    alt_long = f"{project_name}: {subject_phrase} within {services_phrase}."
    return alt_short, alt_long


def map_project_name_from_asset_path(asset_rel: str) -> str:
    # asset_rel like Assets/Backfabrik/Backfabrik_02.webp
    parts = asset_rel.split("/")
    if len(parts) >= 2 and parts[0].lower() == "assets":
        return parts[1]
    return ""


def main() -> int:
    if not os.path.isfile(CSV_PATH):
        print(f"CSV not found: {CSV_PATH}")
        return 1

    # Collect tags per project from all local HTML pages
    tags_by_project_slug = collect_project_tags()

    # Read CSV
    with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    # Ensure columns exist
    for col in ["alt_short_sv", "alt_long_sv", "dekorativ"]:
        if col not in fieldnames:
            fieldnames.append(col)

    updated = 0
    for row in rows:
        asset_rel = (row.get("original_path") or "").strip()
        if not asset_rel:
            continue
        project_dir = map_project_name_from_asset_path(asset_rel)
        project_slug = slugify(project_dir)
        project_name = project_dir.replace("-", " ").strip() or "Case"
        services = sorted(tags_by_project_slug.get(project_slug, set()))

        proposed_alt_short = (row.get("alt_short_sv") or "").strip()
        proposed_alt_long = (row.get("alt_long_sv") or "").strip()
        dekorativ = (row.get("dekorativ") or "nej").strip().lower()

        # Skip decorative assets
        _, ext = os.path.splitext(asset_rel)
        filename = os.path.basename(asset_rel)

        # Decide if we should overwrite/generate
        should_generate = is_generic_alt(proposed_alt_short)

        if dekorativ == "ja":
            # Keep decorative empty alts
            continue

        if should_generate:
            subject = detect_subject_from_name(filename, ext, proposed_alt_short or proposed_alt_long)
            alt_short, alt_long = compose_alt(project_name, subject, services)
            row["alt_short_sv"] = alt_short
            row["alt_long_sv"] = alt_long
            # Most brand/work images are informative
            row["dekorativ"] = "nej"
            updated += 1

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {updated} rows with brand-toned alt texts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


