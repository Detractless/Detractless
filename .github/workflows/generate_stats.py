#!/usr/bin/env python3
"""
scripts/generate_stats.py
Fetches GitHub stats and writes a hexagonal radar-chart SVG to assets/stats.svg.
Zero dependencies outside Python stdlib — no pip installs required.

Usage:
    GITHUB_TOKEN=ghp_... GITHUB_USERNAME=Detractless python scripts/generate_stats.py
"""

import json
import math
import os
import sys
import urllib.error
import urllib.request

USERNAME = os.environ.get("GITHUB_USERNAME", "Detractless")
TOKEN    = os.environ.get("GITHUB_TOKEN", "")
ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
    """Return total_count from the issues search API."""
    d = _req(f"https://api.github.com/search/issues?q={q}&per_page=1")
    return int(d.get("total_count", 0)) if isinstance(d, dict) else 0


def _commit_count() -> int:
    """Approximate all-time commit count via the commit search API."""
    d = _req(
        f"https://api.github.com/search/commits?q=author:{USERNAME}&per_page=1",
        accept="application/vnd.github.cloak-preview+json",
    )
    return int(d.get("total_count", 0)) if isinstance(d, dict) else 0


def _repos() -> list[dict]:
    """Fetch all owned public repos, paginated."""
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


# ── SVG helpers ───────────────────────────────────────────────────────────────

def _polar(cx: float, cy: float, r: float, deg: float) -> tuple[float, float]:
    """Polar → SVG (x,y). deg=0 is top, increases clockwise."""
    rad = math.radians(deg - 90)
    return cx + r * math.cos(rad), cy + r * math.sin(rad)


def _poly(pairs: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in pairs)


def _fmt(n: int) -> str:
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


# ── SVG builder ───────────────────────────────────────────────────────────────

def build_svg(
    commits: int,
    stars: int,
    repos: int,
    prs: int,
    issues: int,
    followers: int,
    lang: str,
) -> str:
    # ── Normalisation ceilings ────────────────────────────────────────────────
    # Tune these as your numbers grow; values above the ceiling clamp to 100%.
    CEIL = {
        "Commits":   3000,
        "Stars":     300,
        "Repos":     30,
        "PRs":       150,
        "Issues":    150,
        "Followers": 300,
    }

    axes = [
        ("Commits",   _clamp(commits   / CEIL["Commits"]),   _fmt(commits)),
        ("Stars",     _clamp(stars     / CEIL["Stars"]),     _fmt(stars)),
        ("Repos",     _clamp(repos     / CEIL["Repos"]),     str(repos)),
        ("PRs",       _clamp(prs       / CEIL["PRs"]),       _fmt(prs)),
        ("Issues",    _clamp(issues    / CEIL["Issues"]),    _fmt(issues)),
        ("Followers", _clamp(followers / CEIL["Followers"]), _fmt(followers)),
    ]
    N    = len(axes)   # 6 → regular hexagon
    STEP = 360 / N     # 60° between axes

    # ── Layout constants ──────────────────────────────────────────────────────
    W,  H   = 680, 400   # card size
    CX, CY  = 205, 208   # radar centre
    MAX_R   = 110        # outer ring radius
    RINGS   = 5          # concentric grid rings
    LBL_R   = 134        # axis label radius

    DIV_X   = 378        # x of vertical rule splitting chart / legend
    LX      = 395        # legend left edge
    RX      = 660        # legend right edge
    BAR_W   = RX - LX   # 265 px progress bars

    # 6 evenly-spaced legend rows between y=96 and y=331
    ROW_Y   = [96 + i * 47 for i in range(N)]

    FOOT_Y  = 353        # y of horizontal footer rule
    BADGE_Y = 375        # y-centre of language badge

    # ── Colours (GitHub dark palette) ────────────────────────────────────────
    BG      = "#0d1117"
    BORDER  = "#30363d"
    GRID_IN = "#161b22"
    GRID_OT = "#30363d"
    DATA_F  = "#388bfd1a"
    DATA_S  = "#58a6ff"
    PRI     = "#e6edf3"
    SEC     = "#8b949e"
    LANG_C  = "#f78166"
    BAR_BG  = "#21262d"

    FONT = "ui-monospace,SFMono-Regular,Menlo,'Courier New',monospace"

    out: list[str] = []

    def w(*lines: str) -> None:
        out.extend(lines)

    # Card
    w(f'<svg xmlns="http://www.w3.org/2000/svg" width="680" height="{H}" viewBox="0 0 680 {H}">')
    w(f'  <rect x="0" y="0" width="680" height="{H}" rx="12" fill="{BG}" stroke="{BORDER}" stroke-width="1"/>')

    # Header
    w(f'  <text x="20" y="30" font-family="{FONT}" font-size="14" font-weight="600" fill="{PRI}">GitHub Stats</text>')
    w(f'  <text x="20" y="48" font-family="{FONT}" font-size="11" fill="{SEC}">@{USERNAME}</text>')
    w(f'  <line x1="20" y1="60" x2="660" y2="60" stroke="{BORDER}" stroke-width="0.7"/>')

    # ── Concentric hexagon grid ───────────────────────────────────────────────
    for ring in range(1, RINGS + 1):
        r  = MAX_R * ring / RINGS
        vs = [_polar(CX, CY, r, i * STEP) for i in range(N)]
        c  = GRID_OT if ring == RINGS else GRID_IN
        sw = "1" if ring == RINGS else "0.8"
        w(f'  <polygon points="{_poly(vs)}" fill="none" stroke="{c}" stroke-width="{sw}"/>')

    # Axis spokes
    for i in range(N):
        ex, ey = _polar(CX, CY, MAX_R, i * STEP)
        w(f'  <line x1="{CX:.2f}" y1="{CY:.2f}" x2="{ex:.2f}" y2="{ey:.2f}" stroke="{GRID_OT}" stroke-width="0.7"/>')

    # ── Data polygon ──────────────────────────────────────────────────────────
    dp = [_polar(CX, CY, MAX_R * v, i * STEP) for i, (_, v, _) in enumerate(axes)]
    w(f'  <polygon points="{_poly(dp)}" fill="{DATA_F}" stroke="{DATA_S}" stroke-width="2" stroke-linejoin="round"/>')

    # Vertex dots
    for x, y in dp:
        w(f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="3.5" fill="{DATA_S}" stroke="{BG}" stroke-width="1.5"/>')

    # ── Axis labels ───────────────────────────────────────────────────────────
    for i, (label, _, _) in enumerate(axes):
        lx, ly = _polar(CX, CY, LBL_R, i * STEP)
        anchor = "middle" if abs(lx - CX) < 12 else ("start" if lx > CX else "end")
        w(
            f'  <text x="{lx:.1f}" y="{ly:.1f}" dy="0.35em" text-anchor="{anchor}" '
            f'font-family="{FONT}" font-size="10" fill="{SEC}">{label}</text>'
        )

    # ── Legend panel ──────────────────────────────────────────────────────────
    w(f'  <line x1="{DIV_X}" y1="68" x2="{DIV_X}" y2="{FOOT_Y}" stroke="{BORDER}" stroke-width="0.7"/>')

    for (label, val, display), ry in zip(axes, ROW_Y):
        bar_fill = max(3.0, BAR_W * val)
        w(
            f'  <text x="{LX}" y="{ry}" font-family="{FONT}" font-size="9" fill="{SEC}">{label}</text>',
            f'  <text x="{RX}" y="{ry}" text-anchor="end" font-family="{FONT}" '
            f'font-size="12" font-weight="600" fill="{PRI}">{display}</text>',
            f'  <rect x="{LX}" y="{ry + 7}" width="{BAR_W}" height="3" rx="1.5" fill="{BAR_BG}"/>',
            f'  <rect x="{LX}" y="{ry + 7}" width="{bar_fill:.1f}" height="3" rx="1.5" fill="{DATA_S}"/>',
        )

    # ── Footer: language badge ────────────────────────────────────────────────
    badge_w = len(lang) * 9 + 20
    w(
        f'  <line x1="20" y1="{FOOT_Y}" x2="660" y2="{FOOT_Y}" stroke="{BORDER}" stroke-width="0.7"/>',
        f'  <text x="20" y="{BADGE_Y}" dy="0.35em" font-family="{FONT}" font-size="9" fill="{SEC}">Top language</text>',
        f'  <rect x="118" y="{BADGE_Y - 9}" width="{badge_w}" height="18" rx="9" '
        f'fill="{LANG_C}22" stroke="{LANG_C}" stroke-width="0.8"/>',
        f'  <text x="127" y="{BADGE_Y}" dy="0.35em" font-family="{FONT}" '
        f'font-size="10" font-weight="600" fill="{LANG_C}">{lang}</text>',
    )

    w("</svg>")
    return "\n".join(out)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"[stats] Fetching @{USERNAME} …")

    repos = _repos()

    stars = sum(r.get("stargazers_count", 0) for r in repos)

    lang_counts: dict[str, int] = {}
    for r in repos:
        if lang := r.get("language"):
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
    lang = max(lang_counts, key=lang_counts.get) if lang_counts else "N/A"

    user_data = _req(f"https://api.github.com/users/{USERNAME}")
    followers = int(user_data.get("followers", 0)) if isinstance(user_data, dict) else 0

    commits  = _commit_count()
    prs      = _search_count(f"author:{USERNAME}+type:pr")
    issues   = _search_count(f"author:{USERNAME}+type:issue")

    data = dict(
        commits=commits, stars=stars, repos=len(repos),
        prs=prs, issues=issues, followers=followers, lang=lang,
    )
    for k, v in data.items():
        print(f"  {k}: {v}")

    svg = build_svg(**data)

    out_path = os.path.join(ROOT, "assets", "stats.svg")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"[stats] Saved → {out_path}")


if __name__ == "__main__":
    main()
