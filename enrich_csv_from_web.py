#!/usr/bin/env python3
import csv
import os
import re
import ssl
import sys
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple

try:
    # Python 3
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError
except Exception:  # pragma: no cover
    print("Requires Python 3", file=sys.stderr)
    raise


BASE_DIR = os.path.abspath(
    "/Users/nilsandersson/Library/CloudStorage/GoogleDrive-nils@several.club/My Drive/Several/Several Projects/Websites/Several.Club"
)


class ImgTagParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.imgs: List[Tuple[str, str]] = []  # (src, alt)

    def handle_starttag(self, tag: str, attrs):
        if tag.lower() == "img":
            attr_dict = {k.lower(): v for k, v in attrs}
            src = (attr_dict.get("src") or attr_dict.get("data-src") or "").strip()
            alt = (attr_dict.get("alt") or "").strip()
            if src:
                self.imgs.append((src, alt))


def collect_local_html_files() -> List[str]:
    html_files: List[str] = []
    for entry in os.listdir(BASE_DIR):
        if entry.lower().endswith(".html"):
            html_files.append(os.path.join(BASE_DIR, entry))
    return html_files


def filenames_to_paths(html_files: List[str]) -> List[Tuple[str, List[str]]]:
    # Returns list of (filename, [candidate_paths]) where candidate_paths are URL paths on the site
    result: List[Tuple[str, List[str]]] = []
    for fp in html_files:
        name = os.path.basename(fp)
        if not name.lower().endswith(".html"):
            continue
        stem = name[:-5]
        candidates = [f"/{name}", f"/{stem}"]
        if name.lower() == "index.html":
            candidates.append("/")
        result.append((name, candidates))
    return result


def normalize_src_to_rel(src: str) -> str:
    # Strip scheme and domain if present
    src = re.sub(r"^https?://[^/]+", "", src, flags=re.IGNORECASE)
    # Remove any URL params and fragments
    src = src.split("?")[0].split("#")[0]
    # Normalize slashes and leading ./ or /
    src = src.replace("\\", "/")
    src = re.sub(r"^\./", "", src)
    src = re.sub(r"^/", "", src)
    return src


def fetch_url(url: str, timeout: int = 10) -> Optional[str]:
    headers = {"User-Agent": "Mozilla/5.0 (asset-alt-fetcher)"}
    req = Request(url, headers=headers)
    try:
        context = ssl.create_default_context()
        with urlopen(req, timeout=timeout, context=context) as resp:
            if resp.status != 200:
                return None
            return resp.read().decode("utf-8", errors="ignore")
    except (HTTPError, URLError, ssl.SSLError):
        return None
    except Exception:
        return None


def build_alt_map_from_domains(domains: List[str], page_paths: List[Tuple[str, List[str]]]) -> Dict[str, str]:
    alt_by_relpath: Dict[str, str] = {}
    alt_by_basename: Dict[str, str] = {}

    def record(src: str, alt: str):
        rel = normalize_src_to_rel(src)
        base = os.path.basename(rel)
        # prefer first non-empty alt
        if rel not in alt_by_relpath or (not alt_by_relpath[rel] and alt):
            alt_by_relpath[rel] = alt
        if base not in alt_by_basename or (not alt_by_basename[base] and alt):
            alt_by_basename[base] = alt

    for domain in domains:
        for _, candidates in page_paths:
            content: Optional[str] = None
            # Try https first then http if needed
            for path in candidates:
                url_https = f"https://{domain}{path}"
                content = fetch_url(url_https)
                if content is None:
                    url_http = f"http://{domain}{path}"
                    content = fetch_url(url_http)
                if content:
                    break
            if not content:
                continue
            parser = ImgTagParser()
            try:
                parser.feed(content)
            except Exception:
                continue
            for src, alt in parser.imgs:
                record(src, alt)

    combined: Dict[str, str] = {}
    combined.update(alt_by_relpath)
    for base, alt in alt_by_basename.items():
        combined[f"__basename__/{base}"] = alt
    return combined


def enrich_csv(csv_path: str, alt_map: Dict[str, str]) -> int:
    rows: List[dict] = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        for row in reader:
            rows.append(row)

    fieldnames = list(dict.fromkeys(fieldnames + [
        "original_path",
        "proposed_filename",
        "alt_short_sv",
        "alt_long_sv",
        "dekorativ",
        "recommended_widths",
        "used_on_pages",
    ]))

    updated_count = 0
    for row in rows:
        rel = (row.get("original_path") or "").strip()
        rel_norm = normalize_src_to_rel(rel)
        base = os.path.basename(rel_norm)
        alt = alt_map.get(rel_norm)
        if alt is None:
            alt = alt_map.get(f"__basename__/{base}")
        if alt is None:
            continue
        alt = alt.strip()
        if alt:
            row["alt_short_sv"] = alt
            row["alt_long_sv"] = alt
            row["dekorativ"] = row.get("dekorativ", "nej") or "nej"
        else:
            row["alt_short_sv"] = ""
            row["alt_long_sv"] = ""
            row["dekorativ"] = "ja"
        updated_count += 1

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return updated_count


def main() -> int:
    csv_path = os.path.join(BASE_DIR, "assets_proposals.csv")
    if not os.path.isfile(csv_path):
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        return 1

    html_files = collect_local_html_files()
    page_paths = filenames_to_paths(html_files)

    domains = [
        "www.sevral.club",
        "www.several.club",
    ]

    alt_map = build_alt_map_from_domains(domains, page_paths)
    updated = enrich_csv(csv_path, alt_map)
    print(f"Updated {updated} rows with alt texts fetched from web")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


