#!/usr/bin/env python3
"""Build self-hosted SVG cards (projects + language stack) for the profile README."""
import datetime
import json
import os
import re
import sys
import urllib.request
from xml.sax.saxutils import escape

USER = os.environ.get("GH_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "EXELYN404"
TOKEN = os.environ.get("GITHUB_TOKEN")
PROJECTS = ["EX-NODE", "EXELYN404-PANEL", "exelyn.88.io"]
OUT = "assets"
FONT = "'JetBrains Mono','Fira Code','SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"
GREENS = ["#00ff41", "#00c93a", "#0a8a2c", "#06521a", "#0a3d14"]


def api(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "exelyn404-cards"}
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request("https://api.github.com" + path, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    except Exception as e:  # network or rate limit: fall back gracefully
        print("api failed:", path, e, file=sys.stderr)
        return None


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def ago(iso):
    if not iso:
        return "unknown"
    try:
        t = datetime.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return "unknown"
    days = (datetime.datetime.utcnow() - t).days
    if days <= 0:
        return "today"
    if days < 31:
        return f"{days}d ago"
    if days < 365:
        return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


def clip(text, n):
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def project_card(info):
    name = escape(info["name"])
    desc = escape(clip(info.get("description") or "no description // classified", 46))
    lang = escape(info.get("language") or "unknown")
    stars = int(info.get("stars") or 0)
    upd = escape(ago(info.get("pushed_at")))
    w, h = 430, 128
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{name}">',
        f'<style>text{{font-family:{FONT}}}</style>',
        f'<defs><clipPath id="c"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="10"/></clipPath>'
        '<pattern id="l" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity="0.25"/></pattern></defs>',
        '<g clip-path="url(#c)">',
        f'<rect width="{w}" height="{h}" fill="#030603"/>',
        f'<rect width="{w}" height="30" fill="#07100a"/>',
        f'<line x1="0" y1="30" x2="{w}" y2="30" stroke="#00ff41" stroke-opacity="0.2"/>',
        '<circle cx="18" cy="15" r="4.5" fill="#ff5f56"/><circle cx="34" cy="15" r="4.5" fill="#ffbd2e"/><circle cx="50" cy="15" r="4.5" fill="#27c93f"/>',
        f'<text x="70" y="19" font-size="11.5" fill="#6bb97b">~/projects/{escape(info["name"].lower())}</text>',
        f'<text x="22" y="64" font-size="19" font-weight="700" fill="#00ff41">&#9656; {name}</text>',
        f'<text x="22" y="88" font-size="12.5" fill="#9be7ab">{desc}</text>',
        '<circle cx="27" cy="109" r="4.5" fill="#00ff41"/>',
        f'<text x="38" y="113" font-size="12" fill="#4f9a5d">{lang}</text>',
        f'<text x="170" y="113" font-size="12" fill="#4f9a5d">&#9733; {stars}</text>',
        f'<text x="230" y="113" font-size="12" fill="#4f9a5d">updated {upd}</text>',
        f'<rect width="{w}" height="{h}" fill="url(#l)"/>',
        "</g>",
        f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="10" fill="none" stroke="#00ff41" stroke-opacity="0.4"/>',
        "</svg>",
    ]
    return "\n".join(parts)


def language_card(langs):
    w = 560
    rows = len(langs) if langs else 1
    h = 44 + 24 + rows * 36 + 14
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="language stack">',
        f'<style>text{{font-family:{FONT}}}</style>',
        f'<defs><clipPath id="c"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="10"/></clipPath>'
        '<pattern id="l" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity="0.25"/></pattern></defs>',
        '<g clip-path="url(#c)">',
        f'<rect width="{w}" height="{h}" fill="#030603"/>',
        f'<rect width="{w}" height="34" fill="#07100a"/>',
        f'<line x1="0" y1="34" x2="{w}" y2="34" stroke="#00ff41" stroke-opacity="0.2"/>',
        '<circle cx="18" cy="17" r="4.5" fill="#ff5f56"/><circle cx="34" cy="17" r="4.5" fill="#ffbd2e"/><circle cx="50" cy="17" r="4.5" fill="#27c93f"/>',
        '<text x="72" y="21" font-size="12" fill="#6bb97b">language.stack</text>',
        f'<text x="{w-18}" y="21" font-size="11" fill="#4f9a5d" text-anchor="end">stack.scan</text>',
    ]
    if not langs:
        parts.append('<text x="28" y="84" font-size="13" fill="#9be7ab">awaiting signal... no data yet</text>')
    else:
        y = 78
        for i, (name, pct) in enumerate(langs):
            col = GREENS[min(i, len(GREENS) - 1)]
            bar = max(3.0, 300 * pct / 100.0)
            parts.append(f'<text x="28" y="{y+4}" font-size="13.5" fill="#d8ffe2">{escape(name)}</text>')
            parts.append(f'<rect x="170" y="{y-6}" width="300" height="12" rx="3" fill="#0a1f0a"/>')
            parts.append(f'<rect x="170" y="{y-6}" width="{bar:.1f}" height="12" rx="3" fill="{col}"/>')
            parts.append(f'<text x="{w-24}" y="{y+4}" font-size="13" fill="#7fcf8f" text-anchor="end">{pct:.1f}%</text>')
            y += 36
    parts += [
        f'<rect width="{w}" height="{h}" fill="url(#l)"/>',
        "</g>",
        f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="10" fill="none" stroke="#00ff41" stroke-opacity="0.4"/>',
        "</svg>",
    ]
    return "\n".join(parts)


def main():
    os.makedirs(OUT, exist_ok=True)
    repos = api(f"/users/{USER}/repos?per_page=100&type=owner") or []
    by_name = {r["name"].lower(): r for r in repos}

    for name in PROJECTS:
        r = by_name.get(name.lower()) or api(f"/repos/{USER}/{name}") or {}
        info = {
            "name": r.get("name", name),
            "description": r.get("description"),
            "language": r.get("language"),
            "stars": r.get("stargazers_count", 0),
            "pushed_at": r.get("pushed_at"),
        }
        with open(os.path.join(OUT, f"project-{slug(name)}.svg"), "w", encoding="utf-8") as f:
            f.write(project_card(info))

    totals = {}
    for r in repos:
        if r.get("fork") or r["name"].lower() == USER.lower():
            continue
        data = api(f"/repos/{USER}/{r['name']}/languages") or {}
        for lang, n in data.items():
            totals[lang] = totals.get(lang, 0) + n
    all_bytes = sum(totals.values())
    langs = []
    if all_bytes:
        top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:5]
        langs = [(k, 100.0 * v / all_bytes) for k, v in top]
    with open(os.path.join(OUT, "language-stack.svg"), "w", encoding="utf-8") as f:
        f.write(language_card(langs))
    print("done:", len(PROJECTS), "projects,", len(langs), "languages")


if __name__ == "__main__":
    main()
