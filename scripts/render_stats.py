"""Render assets/stats.svg from the GitHub GraphQL API.

Self-hosted replacement for github-readme-stats: that public instance is shared
by everyone and answers 503 most of the time. This commits a plain SVG to the
repo, so the README always loads.

Usage: GITHUB_TOKEN=... python scripts/render_stats.py
"""

import collections
import json
import os
import pathlib
import urllib.request

USER = "wlofy"
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets" / "stats.svg"

# ponytail: languages counted per-repo, not per-byte. Byte counts read 94%
# "Jupyter Notebook" because notebooks embed their own image outputs.
QUERY = """
{
  user(login: "%s") {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes { stargazerCount primaryLanguage { name } }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      contributionCalendar { totalContributions }
    }
  }
}
""" % USER

LANG_COLORS = {
    "Python": "#3572A5", "Jupyter Notebook": "#DA5B0B", "JavaScript": "#F1E05A",
    "TypeScript": "#3178C6", "Kotlin": "#A97BFF", "C": "#555555",
    "C++": "#F34B7D", "HTML": "#E34C26", "CSS": "#663399",
}
FALLBACK = "#8B949E"


def fetch():
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if "errors" in body:
        raise SystemExit(f"GraphQL error: {body['errors']}")
    return body["data"]["user"]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(user):
    repos = user["repositories"]["nodes"]
    contrib = user["contributionsCollection"]
    stats = [
        ("Repos", user["repositories"]["totalCount"]),
        ("Stars", sum(r["stargazerCount"] for r in repos)),
        ("Commits (1y)", contrib["totalCommitContributions"]),
        ("Pull requests", contrib["totalPullRequestContributions"]),
        ("Contributions (1y)", contrib["contributionCalendar"]["totalContributions"]),
    ]

    counts = collections.Counter(
        r["primaryLanguage"]["name"] for r in repos if r["primaryLanguage"]
    )
    top = counts.most_common(6)
    total = sum(n for _, n in top) or 1

    # --- stat columns -----------------------------------------------------
    parts = []
    col_w = 690 / len(stats)
    for i, (label, value) in enumerate(stats):
        cx = 15 + col_w * (i + 0.5)
        parts.append(
            f'<g class="row r{i + 1}">'
            f'<text class="num" x="{cx:.0f}" y="96" text-anchor="middle">{value}</text>'
            f'<text class="lbl" x="{cx:.0f}" y="118" text-anchor="middle">{esc(label)}</text>'
            f"</g>"
        )

    # --- stacked language bar --------------------------------------------
    x = 30.0
    bar_w = 660.0
    for i, (lang, n) in enumerate(top):
        w = bar_w * n / total
        color = LANG_COLORS.get(lang, FALLBACK)
        # first/last segments get the rounded ends
        parts.append(
            f'<rect class="bar b{i + 1}" x="{x:.1f}" y="152" width="{w:.1f}" '
            f'height="12" fill="{color}"/>'
        )
        x += w

    # --- legend, two rows of three ---------------------------------------
    for i, (lang, n) in enumerate(top):
        lx = 30 + (i % 3) * 230
        ly = 200 + (i // 3) * 26
        pct = 100 * n / total
        color = LANG_COLORS.get(lang, FALLBACK)
        parts.append(
            f'<g class="row r{i + 1}">'
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{color}"/>'
            f'<text class="lgd" x="{lx + 18}" y="{ly}">{esc(lang)} '
            f'<tspan class="dim">{pct:.0f}%</tspan></text>'
            f"</g>"
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="270" viewBox="0 0 720 270" role="img"
     aria-label="GitHub stats for {USER}">
  <style>
    .mono {{ font-family: ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; }}
    .num {{ fill: #39d353; font-size: 26px; font-weight: 600 }}
    .lbl {{ fill: #7d8590; font-size: 11px }}
    .lgd {{ fill: #c9d1d9; font-size: 12px }}
    .dim {{ fill: #7d8590 }}
    .row {{ opacity: 0; animation: in .45s ease-out forwards }}
    .r1 {{ animation-delay: .10s }} .r2 {{ animation-delay: .22s }} .r3 {{ animation-delay: .34s }}
    .r4 {{ animation-delay: .46s }} .r5 {{ animation-delay: .58s }} .r6 {{ animation-delay: .70s }}
    @keyframes in {{ from {{ opacity: 0; transform: translateY(6px) }} to {{ opacity: 1; transform: none }} }}
    .bar {{ transform: scaleX(0); transform-origin: left center; animation: grow .6s ease-out .5s forwards }}
    .b2 {{ animation-delay: .60s }} .b3 {{ animation-delay: .70s }} .b4 {{ animation-delay: .80s }}
    .b5 {{ animation-delay: .90s }} .b6 {{ animation-delay: 1.0s }}
    @keyframes grow {{ to {{ transform: scaleX(1) }} }}
    @media (prefers-reduced-motion: reduce) {{
      .row {{ animation: none; opacity: 1 }}
      .bar {{ animation: none; transform: none }}
    }}
  </style>

  <rect x="1" y="1" width="718" height="268" rx="10" fill="#0d1117" stroke="#30363d"/>
  <path d="M1 11a10 10 0 0 1 10-10h698a10 10 0 0 1 10 10v27H1z" fill="#161b22"/>
  <line x1="1" y1="38" x2="719" y2="38" stroke="#30363d"/>
  <circle cx="22" cy="20" r="5" fill="#ff5f56"/>
  <circle cx="40" cy="20" r="5" fill="#ffbd2e"/>
  <circle cx="58" cy="20" r="5" fill="#27c93f"/>
  <text class="mono" fill="#7d8590" x="82" y="25" font-size="13">saad@github: ~/stats</text>

  <g class="mono">
  {chr(10).join("  " + p for p in parts)}
  </g>
</svg>
"""


def demo():
    """Self-check: render from a canned payload, no network."""
    fake = {
        "repositories": {
            "totalCount": 3,
            "nodes": [
                {"stargazerCount": 31, "primaryLanguage": {"name": "Python"}},
                {"stargazerCount": 1, "primaryLanguage": {"name": "Python"}},
                {"stargazerCount": 0, "primaryLanguage": None},
            ],
        },
        "contributionsCollection": {
            "totalCommitContributions": 57,
            "totalPullRequestContributions": 8,
            "contributionCalendar": {"totalContributions": 175},
        },
    }
    svg = build(fake)
    import xml.etree.ElementTree as ET

    ET.fromstring(svg)  # well-formed
    assert ">32<" in svg, "stars should sum to 32"
    assert ">175<" in svg, "contributions should render"
    assert "Python <tspan" in svg, "language legend missing"
    assert "None" not in svg, "repos with no language must be skipped"
    print("demo ok")


if __name__ == "__main__":
    if os.environ.get("DEMO"):
        demo()
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(build(fetch()), encoding="utf-8")
        print(f"wrote {OUT}")
