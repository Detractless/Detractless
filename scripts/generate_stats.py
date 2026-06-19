#!/usr/bin/env python3
"""
scripts/generate_stats.py
Fetches GitHub stats and patches the live values directly into assets/header-typing.svg.
Zero dependencies outside Python stdlib — no pip installs required.

Usage:
    GITHUB_TOKEN=ghp_... GITHUB_USERNAME=Detractless python scripts/generate_stats.py
"""

import json
import os
import re
import sys
import urllib.error
import urllib.request

USERNAME = os.environ.get("GITHUB_USERNAME", "Detractless")
TOKEN    = os.environ.get("GITHUB_TOKEN", "")
ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ensure this matches your actual file name
SVG_PATH = os.path.join(ROOT, "assets", "header.svg")


# ── API layer ─────────────────────────────────────────────────────────────────

def _req(url: str, accept: str = "application/vnd.github+json") -> dict | list:
    req = urllib.request.Request(url)
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", accept)
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "stats-gen/1.0")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"  WARN HTTP {e.code}: {url}", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"  WARN {e}", file=sys.stderr)
        return {}


def _search_count(q: str) -> int:
    d = _req(f"https://api.github.com/search/issues?q={q}&per_page=1")
    return int(d.get("total_count", 0)) if isinstance(d, dict) else 0


def _commit_count() -> int:
    d = _req(
        f"https://api.github.com/search/commits?q=author:{USERNAME}&per_page=1",
        accept="application/vnd.github.cloak-preview+json",
    )
    return int(d.get("total_count", 0)) if isinstance(d, dict) else 0


def _repos() -> list[dict]:
    pages, page = [], 1
    while True:
        chunk = _req(
            f"https://api.github.com/users/{USERNAME}/repos"
            f"?per_page=100&page={page}&type=owner"
        )
        if not isinstance(chunk, list) or not chunk:
            break
        pages.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return pages


def _fmt(n: int) -> str:
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


# ── SVG patcher ───────────────────────────────────────────────────────────────
#
# We use the <g class="slide-X"> wrappers as our anchor points.
# Slide 1 = Commits, Slide 2 = Stars, Slide 3 = Repos, Slide 4 = Issues, Slide 5 = Lang

def _patch_stat(svg: str, slide_num: int, value: str) -> str:
    """Replace the text content of the first <text> immediately inside <g class="slide-X">."""
    pattern = rf'(<g class="slide-{slide_num}">\s*<text [^>]*>)[^<]*(</text>)'
    result, n = re.subn(pattern, rf'\g<1>{value}\g<2>', svg)
    if n == 0:
        print(f"  WARN: <g class='slide-{slide_num}'> not found in SVG", file=sys.stderr)
    return result


def _patch_lang(svg: str, lang: str) -> str:
    """Replace language badge text and resize the pill width to fit in slide-5."""
    # Update text (we target class="stat-lang" specifically)
    svg = re.sub(
        r'(<g class="slide-5">.*?<text [^>]*class="stat-lang"[^>]*>)[^<]*(</text>)',
        rf'\g<1>{lang}\g<2>',
        svg,
        flags=re.DOTALL
    )
    # Resize pill width: 9px per char + 20px padding
    new_w = len(lang) * 9 + 20
    svg = re.sub(
        r'(<g class="slide-5">.*?<rect [^>]*?)width="[^"]*"',
        rf'\g<1>width="{new_w}"',
        svg,
        flags=re.DOTALL
    )
    return svg


def patch_svg(
    commits: int,
    stars: int,
    repos: int,
    issues: int,
    lang: str,
) -> None:
    if not os.path.exists(SVG_PATH):
        print(f"[stats] ERROR: {SVG_PATH} not found", file=sys.stderr)
        sys.exit(1)

    with open(SVG_PATH, encoding="utf-8") as f:
        svg = f.read()

    svg = _patch_stat(svg, 1, _fmt(commits))
    svg = _patch_stat(svg, 2, _fmt(stars))
    svg = _patch_stat(svg, 3, str(repos))
    svg = _patch_stat(svg, 4, _fmt(issues))
    svg = _patch_lang(svg, lang)

    with open(SVG_PATH, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"[stats] Patched → {SVG_PATH}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"[stats] Fetching @{USERNAME} …")

    repos_data = _repos()

    stars = sum(r.get("stargazers_count", 0) for r in repos_data)

    lang_counts: dict[str, int] = {}
    for r in repos_data:
        if lang := r.get("language"):
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
    lang = max(lang_counts, key=lang_counts.get) if lang_counts else "N/A"

    commits = _commit_count()
    issues  = _search_count(f"author:{USERNAME}+type:issue")

    data = dict(
        commits=commits, stars=stars,
        repos=len(repos_data), issues=issues, lang=lang,
    )
    for k, v in data.items():
        print(f"  {k}: {v}")

    patch_svg(**data)


if __name__ == "__main__":
    main()
