#!/usr/bin/env python3
"""
scrape_position.py <url>

Fetches a job posting URL and extracts structured job data as compact JSON.

Extraction strategy (priority order):
  1. JSON-LD schema.org/JobPosting — common on Greenhouse, Lever, LinkedIn, Workday
  2. <main>/<article> content fallback — raw text extraction from main content area

Output (stdout): compact JSON with keys:
  title, company, location, remote, salary, description, requirements, url

Errors go to stderr; non-zero exit on failure.
"""

import json
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser


TIMEOUT = 15
DESC_MAX_CHARS = 3000

SKIP_TAGS = {"script", "style", "noscript", "nav", "header", "footer",
             "aside", "meta", "link", "svg", "path", "button"}
MAIN_TAGS = {"main", "article", "section", "[role=main]"}


class TextExtractor(HTMLParser):
    """Extract visible text from HTML, skipping non-content tags."""

    def __init__(self):
        super().__init__()
        self._skip_depth = 0
        self._main_depth = 0
        self._in_main = False
        self._current_tag = None
        self.chunks = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        # Detect main content containers
        if (tag in ("main", "article") or
                attr_dict.get("role") in ("main",) or
                any("job" in (attr_dict.get(a) or "").lower()
                    for a in ("id", "class"))):
            self._main_depth += 1
            self._in_main = True

        if tag in SKIP_TAGS:
            self._skip_depth += 1
        self._current_tag = tag

    def handle_endtag(self, tag):
        if tag in SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        if tag in ("main", "article"):
            self._main_depth = max(0, self._main_depth - 1)
            if self._main_depth == 0:
                self._in_main = False

    def handle_data(self, data):
        if self._skip_depth > 0:
            return
        text = data.strip()
        if text:
            self.chunks.append(text)

    def get_text(self):
        return "\n".join(self.chunks)


class JsonLdExtractor(HTMLParser):
    """Extract JSON-LD blocks from HTML."""

    def __init__(self):
        super().__init__()
        self._in_jsonld = False
        self._depth = 0
        self.blocks = []
        self._buf = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            attr_dict = dict(attrs)
            if attr_dict.get("type") == "application/ld+json":
                self._in_jsonld = True
                self._buf = []

    def handle_endtag(self, tag):
        if tag == "script" and self._in_jsonld:
            self._in_jsonld = False
            raw = "".join(self._buf).strip()
            if raw:
                self.blocks.append(raw)

    def handle_data(self, data):
        if self._in_jsonld:
            self._buf.append(data)


def clean_html_text(html_fragment: str) -> str:
    """Strip HTML tags from a fragment, returning plain text."""
    parser = TextExtractor()
    parser.feed(html_fragment)
    return " ".join(parser.get_text().split())


def extract_jsonld_job(html: str) -> dict | None:
    """Try to extract a JobPosting from JSON-LD. Returns dict or None."""
    extractor = JsonLdExtractor()
    extractor.feed(html)

    for raw in extractor.blocks:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        # Handle both single object and @graph arrays
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            if data.get("@type") == "JobPosting":
                items = [data]
            elif "@graph" in data:
                items = data["@graph"]

        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("@type") != "JobPosting":
                continue

            # --- title ---
            title = item.get("title") or item.get("name") or ""

            # --- company ---
            org = item.get("hiringOrganization") or {}
            company = org.get("name") if isinstance(org, dict) else str(org)

            # --- location ---
            loc_raw = item.get("jobLocation") or {}
            location = ""
            if isinstance(loc_raw, list):
                loc_raw = loc_raw[0] if loc_raw else {}
            if isinstance(loc_raw, dict):
                addr = loc_raw.get("address") or {}
                if isinstance(addr, dict):
                    parts = filter(None, [
                        addr.get("addressLocality"),
                        addr.get("addressRegion"),
                        addr.get("addressCountry"),
                    ])
                    location = ", ".join(parts)
                elif isinstance(addr, str):
                    location = addr

            # --- remote ---
            work_setting = (item.get("jobLocationType") or "").lower()
            remote = "remote" in work_setting

            # --- salary ---
            salary = ""
            sal_raw = item.get("baseSalary") or item.get("estimatedSalary") or {}
            if isinstance(sal_raw, dict):
                val = sal_raw.get("value") or {}
                if isinstance(val, dict):
                    lo = val.get("minValue", "")
                    hi = val.get("maxValue", "")
                    currency = sal_raw.get("currency", "")
                    unit = val.get("unitText", "")
                    if lo and hi:
                        salary = f"{currency}{lo}–{currency}{hi} {unit}".strip()
                    elif lo:
                        salary = f"{currency}{lo}+ {unit}".strip()
                elif isinstance(val, (int, float, str)):
                    salary = str(val)

            # --- description / requirements ---
            desc_html = item.get("description") or ""
            desc = clean_html_text(desc_html)[:DESC_MAX_CHARS]

            quals_html = (item.get("qualifications") or
                          item.get("experienceRequirements") or
                          item.get("skills") or "")
            requirements = clean_html_text(quals_html)[:1000] if quals_html else ""

            return {
                "title": title,
                "company": company or "",
                "location": location,
                "remote": remote,
                "salary": salary,
                "description": desc,
                "requirements": requirements,
            }

    return None


def extract_text_fallback(html: str) -> dict:
    """Fall back to raw text extraction from main/article content."""
    extractor = TextExtractor()
    extractor.feed(html)
    text = extractor.get_text()

    # Heuristic: first non-empty line is often the title
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    title = lines[0] if lines else ""
    body = "\n".join(lines[1:])[:DESC_MAX_CHARS]

    return {
        "title": title,
        "company": "",
        "location": "",
        "remote": None,
        "salary": "",
        "description": body,
        "requirements": "",
    }


def infer_remote(data: dict, html: str) -> bool | None:
    """Fill in remote flag from page text if not already set."""
    if data.get("remote") is not None:
        return data["remote"]
    combined = (data.get("description", "") + " " + data.get("location", "") +
                " " + html[:5000]).lower()
    if "remote" in combined:
        return True
    if "on-site" in combined or "onsite" in combined or "in office" in combined:
        return False
    return None


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; career-flow/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}")
        charset = "utf-8"
        ct = resp.headers.get_content_charset()
        if ct:
            charset = ct
        return resp.read().decode(charset, errors="replace")


def main():
    if len(sys.argv) < 2:
        print("Usage: scrape_position.py <url>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]

    try:
        html = fetch(url)
    except urllib.error.HTTPError as e:
        print(f"Error fetching {url}: HTTP {e.code}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        sys.exit(1)

    data = extract_jsonld_job(html)
    if not data:
        data = extract_text_fallback(html)

    data["remote"] = infer_remote(data, html)
    data["url"] = url

    print(json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
    main()
