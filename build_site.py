#!/usr/bin/env python3
"""
Chess portfolio site generator.

Reads site.json and writes a static site you can host on GitHub Pages:
  index.html, 404.html, assets/favicon.svg, robots.txt, sitemap.xml, .nojekyll

assets/style.css and assets/site.js are hand-written and not generated.

Usage:
  python build_site.py
  python -m http.server 8000      # then open http://localhost:8000

Standard library only.
"""
import argparse
import datetime
import json
import os
from html import escape

ROOT = os.path.dirname(os.path.abspath(__file__))

PIECES = {
    "pawn": ["....#....", "...###...", "...###...", "....#....", "...###...",
             "..#####..", "...###...", "..#####..", ".#######."],
    "knight": ["..##.....", ".####....", "######...", "##.###...", "....###..",
               "...####..", "..#####..", ".#######.", "#########"],
    "bishop": ["....#....", "...###...", "..##.##..", "..#####..", "..#####..",
               "...###...", "....#....", "..#####..", ".#######."],
    "rook": ["#.#.#.#.#", "#########", ".#######.", "..#####..", "..#####..",
             "..#####..", "..#####..", ".#######.", "#########"],
    "queen": ["#...#...#", "#.#.#.#.#", "#########", ".#######.", "..#####..",
              "..#####..", "...###...", ".#######.", "#########"],
    "king": ["....#....", "...###...", "....#....", ".#######.", ".#######.",
             "..#####..", "..#####..", ".#######.", "#########"],
}
DIFF_PIECES = ["pawn", "knight", "bishop", "rook", "queen"]
LAYER_PIECES = ["pawn", "knight", "bishop", "rook", "queen", "king"]
STATE_LABEL = {"done": "developed", "training": "developing now", "locked": "not yet on the board"}
STATUS = {"won": ("done", "Completed"), "in play": ("live", "In progress"), "puzzle": ("side", "Side project")}


def esc(s):
    return escape(str(s), quote=True)


# --------------------------------------------------------------------------- pixel pieces
def _cells(name):
    return {(c, r) for r, row in enumerate(PIECES[name]) for c, ch in enumerate(row) if ch == "#"}


def _path(cells):
    rows = {}
    for c, r in cells:
        rows.setdefault(r, []).append(c)
    d = []
    for r in sorted(rows):
        cols = sorted(rows[r])
        s = p = cols[0]
        for c in cols[1:] + [None]:
            if c is not None and c == p + 1:
                p = c
                continue
            w = p - s + 1
            d.append(f"M{s} {r}h{w}v1h-{w}z")
            if c is not None:
                s = p = c
    return "".join(d)


def piece_paths(name):
    cells = _cells(name)
    ring = {(c + dx, r + dy) for c, r in cells for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - cells
    return _path(ring), _path(cells)


def pixel(name, cls=""):
    ring, body = piece_paths(name)
    return (f'<svg class="pc {cls}" viewBox="-1 -1 11 11" aria-hidden="true" focusable="false" '
            f'shape-rendering="crispEdges"><path class="po" d="{ring}"/><path class="pf" d="{body}"/></svg>')


# --------------------------------------------------------------------------- sections
def skill_graph(layers):
    W = 960
    L = len(layers)
    maxn = max(len(l["skills"]) for l in layers)
    sp, top = 78, 78
    H = top + maxn * sp + 16
    xs = [110 + i * (W - 220) / (L - 1) for i in range(L)] if L > 1 else [W / 2]
    pos = {}
    for i, l in enumerate(layers):
        off = (maxn - len(l["skills"])) * sp / 2
        for k in range(len(l["skills"])):
            pos[(i, k)] = (xs[i], top + off + k * sp + 24)
    state = lambda i, k: layers[i]["skills"][k].get("state", "locked")

    edges = []
    for i in range(L - 1):
        for a in range(len(layers[i]["skills"])):
            for b in range(len(layers[i + 1]["skills"])):
                (xa, ya), (xb, yb) = pos[(i, a)], pos[(i + 1, b)]
                sa, sb = state(i, a), state(i + 1, b)
                cls = "lit" if sa == sb == "done" else ("dim" if "locked" in (sa, sb) else "warn")
                edges.append(f'<line class="edge {cls}" data-a="{i}-{a}" data-b="{i + 1}-{b}" '
                             f'x1="{xa + 24:.0f}" y1="{ya:.0f}" x2="{xb - 24:.0f}" y2="{yb:.0f}"/>')
    nodes = []
    for (i, k), (x, y) in pos.items():
        sk = layers[i]["skills"][k]
        st = state(i, k)
        pname = sk.get("piece") or layers[i].get("piece") or LAYER_PIECES[min(i, 5)]
        ring, body = piece_paths(pname)
        nodes.append(
            f'<g class="node st-{st}" data-id="{i}-{k}" data-name="{esc(sk["name"])}" data-state="{STATE_LABEL[st]}" '
            f'tabindex="0" role="img" aria-label="{esc(sk["name"])}: {STATE_LABEL[st]}">'
            f'<circle class="hit" cx="{x:.0f}" cy="{y:.0f}" r="34"/>'
            f'<g transform="translate({x - 13.5:.1f} {y - 20:.1f}) scale(3)"><path class="po" d="{ring}"/><path class="pf" d="{body}"/></g>'
            f'<text class="nl" x="{x:.0f}" y="{y + 36:.0f}" text-anchor="middle">{esc(sk["name"])}</text></g>'
        )
    titles = "".join(f'<text class="layer-title" x="{xs[i]:.0f}" y="26" text-anchor="middle">{esc(l["name"])}</text>'
                     for i, l in enumerate(layers))
    return (f'<svg class="graph" viewBox="0 0 {W} {H}" role="group" aria-label="Skill tree drawn as a neural network of chess pieces">'
            f'{titles}{"".join(edges)}{"".join(nodes)}</svg>')


def skill_list(layers):
    out = []
    for i, l in enumerate(layers):
        items = "".join(
            f'<li class="st-{sk.get("state", "locked")}">{pixel(sk.get("piece") or l.get("piece") or LAYER_PIECES[min(i, 5)], "sm")}'
            f'<span>{esc(sk["name"])}</span><em>{STATE_LABEL[sk.get("state", "locked")]}</em></li>'
            for sk in l["skills"])
        out.append(f'<div><h3>{esc(l["name"])}</h3><ul>{items}</ul></div>')
    return f'<div class="tree-list">{"".join(out)}</div>'


def project_card(p):
    cls, label = STATUS.get(p.get("status", "won"), ("side", "Project"))
    if cls == "live" and "progress" in p:
        label += f" ({int(p['progress'])}%)"
    d = max(1, min(5, int(p.get("difficulty", 3))))
    links = dict(p.get("links") or {})
    parts = []
    if p.get("repo"):
        parts.append(f'<a href="https://github.com/{esc(p["repo"])}" rel="noopener">Code</a>')
    if links.get("demo"):
        parts.append(f'<a href="{esc(links["demo"])}" rel="noopener">Live demo</a>')
    if links.get("writeup"):
        parts.append(f'<a href="{esc(links["writeup"])}" rel="noopener">Write-up</a>')
    case = ""
    cs = p.get("case_study")
    if cs:
        rows = "".join(f"<div><dt>{k}</dt><dd>{esc(cs[key])}</dd></div>"
                       for key, k in (("problem", "Problem"), ("approach", "Approach"),
                                      ("outcome", "Outcome"), ("learned", "What I learned")) if cs.get(key))
        case = f'<details class="case"><summary>Case study</summary><dl>{rows}</dl></details>'
    result = (f'<p class="result"><span>Result</span><strong>{esc(p["result"])}</strong></p>' if p.get("result") else "")
    role = f'<p class="role">{esc(p["role"])}</p>' if p.get("role") else ""
    tags = "".join(f"<li>{esc(t)}</li>" for t in p.get("tags", []))
    return (
        f'<article class="card reveal" data-cat="{esc(p.get("category", ""))}">'
        f'<div class="card-top"><span class="chip {cls}">{esc(label)}</span><span class="repo">{esc(p.get("repo", ""))}</span></div>'
        f'<div class="card-title">{pixel(DIFF_PIECES[d - 1], "md")}<h3>{esc(p["name"])}</h3></div>'
        f'{role}<p class="desc">{esc(p.get("desc", ""))}</p>{result}'
        f'<ul class="tags">{tags}</ul>'
        f'<div class="card-links">{"".join(parts)}</div>{case}</article>'
    )


def build_html(cfg):
    name = cfg.get("name", cfg["github"])
    piece = cfg.get("piece", "knight")
    if piece not in PIECES:
        piece = "knight"
    url = cfg.get("site_url", "").rstrip("/")
    desc = cfg.get("tagline", "")
    title = cfg.get("title") or f"{name} | {cfg.get('role', 'Portfolio')}"
    year = datetime.date.today().year

    sections = []  # (id, nav label)
    body = []

    def section(id_, label, heading, inner, cls=""):
        sections.append((id_, label))
        n = f"{len(sections):02d}"
        body.append(f'<section id="{id_}" class="section {cls}"><div class="wrap">'
                    f'<header class="sec-head reveal"><span class="sec-num">{n}</span><h2>{heading}</h2></header>{inner}</div></section>')

    # about
    about = cfg.get("about")
    if about:
        paras = "".join(f"<p>{esc(x)}</p>" for x in about.get("paragraphs", []))
        facts = "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in about.get("facts", []))
        card = ""
        if cfg.get("model_card"):
            rows = "".join(f"<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>" for k, v in cfg["model_card"])
            card = f'<aside class="model-card reveal" aria-label="Model card"><h3>Model card</h3><dl>{rows}</dl></aside>'
        section("about", "About", "About", f'<div class="about-grid"><div class="prose reveal">{paras}<dl class="facts">{facts}</dl></div>{card}</div>')

    # skills
    layers = cfg.get("skill_layers")
    if layers:
        legend = (f'<ul class="legend" aria-hidden="true"><li class="st-done">{pixel("pawn", "sm")} developed</li>'
                  f'<li class="st-training">{pixel("pawn", "sm")} developing now</li>'
                  f'<li class="st-locked">{pixel("pawn", "sm")} not yet on the board</li></ul>')
        inner = (f'<p class="lede reveal">Each skill is a piece, and the whole tree is a small neural network. '
                 f'A lit line joins two developed skills: a chain I can run end to end.</p>'
                 f'<div class="graph-wrap reveal">{skill_graph(layers)}<p class="graph-caption" data-caption aria-live="polite">Hover or focus a piece.</p>{legend}</div>'
                 f'{skill_list(layers)}')
        section("skills", "Skills", "Skill tree", inner)

    # projects
    projects = cfg.get("projects", [])
    if projects:
        cats = list(dict.fromkeys(p.get("category") for p in projects if p.get("category")))
        filt = ""
        if len(cats) > 1:
            filt = ('<div class="filters reveal" role="group" aria-label="Filter projects">'
                    '<button class="f on" data-filter="all" aria-pressed="true">All</button>'
                    + "".join(f'<button class="f" data-filter="{esc(c)}" aria-pressed="false">{esc(c)}</button>' for c in cats) + "</div>")
        section("projects", "Projects", "Projects",
                f'{filt}<div class="cards">{"".join(project_card(p) for p in projects)}</div>')

    # journey
    tl = cfg.get("timeline", [])
    if tl:
        items = "".join(
            f'<li class="reveal"><span class="when">{esc(m.get("when", ""))}</span><div><h3>{esc(m["title"])}'
            f'{(" <small>" + esc(m["where"]) + "</small>") if m.get("where") else ""}</h3>'
            f'{("<p>" + esc(m["detail"]) + "</p>") if m.get("detail") else ""}</div></li>' for m in tl)
        section("journey", "Journey", "Journey, move by move", f'<ol class="moves">{items}</ol>')

    # writing
    wr = cfg.get("writing", [])
    if wr:
        items = "".join(
            f'<li class="reveal"><a href="{esc(w.get("url", "#"))}" rel="noopener">{esc(w["title"])}</a>'
            f'<span>{esc(w.get("venue", ""))} {esc(w.get("year", ""))}</span></li>' for w in wr)
        section("writing", "Writing", "Writing and talks", f'<ul class="writing">{items}</ul>')

    # contact
    ct = cfg.get("contact", {})
    email = cfg.get("email", "")
    link_html = "".join(f'<a href="{esc(l["url"])}" rel="noopener">{esc(l["label"])}</a>' for l in cfg.get("links", []))
    if cfg.get("resume"):
        link_html += f'<a href="{esc(cfg["resume"])}">Resume (PDF)</a>'
    contact = (
        f'<section id="contact" class="section contact"><div class="wrap">'
        f'<p class="eyebrow reveal">{pixel(piece, "sm")} {esc(cfg.get("status", ""))}</p>'
        f'<h2 class="big reveal">{esc(ct.get("heading", "Your move."))}</h2>'
        f'<p class="lede reveal">{esc(ct.get("text", ""))}</p>'
        f'<div class="contact-row reveal"><a class="btn primary" href="mailto:{esc(email)}">{esc(email)}</a>'
        f'<button class="btn ghost" type="button" data-copy="{esc(email)}">Copy email</button></div>'
        f'<nav class="elsewhere reveal" aria-label="Elsewhere">{link_html}</nav></div></section>'
    )
    sections.append(("contact", "Contact"))

    nav = "".join(f'<a href="#{i}">{esc(l)}</a>' for i, l in sections)

    # hero
    hl = "".join(f'<li><strong>{esc(h["value"])}</strong><span>{esc(h["label"])}</span></li>' for h in cfg.get("highlights", []))
    start = (4, 6) if piece == "pawn" else (3, 4)
    hero_buttons = '<a class="btn primary" href="#projects">See my work</a>'
    if cfg.get("resume"):
        hero_buttons += f'<a class="btn ghost" href="{esc(cfg["resume"])}">Resume</a>'
    hero_buttons += f'<a class="btn ghost" href="#contact">Contact</a>'
    hero = (
        f'<section class="hero"><div class="wrap hero-grid"><div class="hero-copy">'
        f'<p class="eyebrow rise" style="--d:.05s"><span class="dot" aria-hidden="true"></span>{esc(cfg.get("status", ""))}</p>'
        f'<h1 class="rise" style="--d:.15s">{esc(name)}</h1>'
        f'<p class="role-line rise" style="--d:.25s">{esc(cfg.get("role", ""))}</p>'
        f'<p class="lead rise" style="--d:.35s">{esc(desc)}</p>'
        f'<div class="cta rise" style="--d:.45s">{hero_buttons}</div>'
        f'<ul class="stats rise" style="--d:.55s">{hl}</ul></div>'
        f'<div class="board-wrap rise" style="--d:.3s" data-board data-piece="{piece}">'
        f'<div class="ranks" aria-hidden="true">{"".join(f"<span>{8 - i}</span>" for i in range(8))}</div>'
        f'<div class="board" role="group" aria-label="Interactive chessboard with a {piece}">'
        f'<span class="piece static" style="--c:{start[0]};--r:{start[1]}">{pixel(piece)}</span></div>'
        f'<div class="files" aria-hidden="true">{"".join(f"<span>{c}</span>" for c in "abcdefgh")}</div>'
        f'<p class="board-status" data-status aria-live="polite">Try me: click the {piece}, then a marked square.</p>'
        f'</div></div></section>'
    )

    # structured data
    person = {"@context": "https://schema.org", "@type": "Person", "name": name,
              "jobTitle": cfg.get("role", ""), "description": desc,
              "sameAs": [l["url"] for l in cfg.get("links", [])]}
    if url:
        person["url"] = url
    ld = json.dumps(person, ensure_ascii=False).replace("</", "<\\/")

    og = ""
    if url:
        og += f'<link rel="canonical" href="{esc(url)}/">'
        og += f'<meta property="og:url" content="{esc(url)}/">'
    if cfg.get("og_image") and url:
        og += f'<meta property="og:image" content="{esc(url)}/{esc(cfg["og_image"])}"><meta name="twitter:card" content="summary_large_image">'
    else:
        og += '<meta name="twitter:card" content="summary">'

    pieces_js = json.dumps(PIECES)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
{og}
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<meta name="color-scheme" content="dark light">
<script>try{{var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t}}catch(e){{}}document.documentElement.classList.add('js')</script>
<link rel="stylesheet" href="assets/style.css">
<script type="application/ld+json">{ld}</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
<div class="wrap header-in">
<a class="brand" href="#top" aria-label="{esc(name)}, home">{pixel(piece, "sm")}<span>{esc(name)}</span></a>
<button class="nav-toggle" type="button" aria-expanded="false" aria-controls="nav">Menu</button>
<nav id="nav" class="nav" aria-label="Primary">{nav}</nav>
<button class="theme" type="button" data-theme-toggle aria-label="Switch light or dark theme"><span aria-hidden="true"></span></button>
</div>
<div class="checker" aria-hidden="true"></div>
</header>
<main id="main">
<span id="top"></span>
{hero}
{"".join(body)}
{contact}
</main>
<footer class="site-footer"><div class="wrap"><p>&copy; {year} {esc(name)}. Plain HTML, CSS and one Python script. No trackers, no cookies.</p></div><div class="checker" aria-hidden="true"></div></footer>
<script>window.PIECES={pieces_js};</script>
<script src="assets/site.js" defer></script>
</body>
</html>
"""


def build_404(cfg):
    name = esc(cfg.get("name", cfg["github"]))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Illegal move | {name}</title>
<script>try{{var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
<link rel="stylesheet" href="/assets/style.css"></head>
<body><main class="notfound"><div class="wrap"><p class="eyebrow">404</p><h1>Illegal move.</h1>
<p class="lead">That page is not on the board.</p><p class="cta"><a class="btn primary" href="/">Back to the start</a></p></div></main></body></html>
"""


def build_favicon():
    ring, body = piece_paths("knight")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-3 -3 15 15" shape-rendering="crispEdges">'
            f'<rect x="-3" y="-3" width="15" height="15" fill="#b58863"/>'
            f'<path d="{ring}" fill="#1c1a17"/><path d="{body}" fill="#fffaf0"/></svg>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(ROOT, "site.json"))
    args = ap.parse_args()
    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)
    piece = cfg.get("piece", "knight")

    def write(rel, text):
        path = os.path.join(ROOT, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    write("index.html", build_html(cfg))
    write("404.html", build_404(cfg))
    fav = build_favicon()
    if piece in PIECES and piece != "knight":
        ring, body = piece_paths(piece)
        fav = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-3 -3 15 15" shape-rendering="crispEdges">'
               f'<rect x="-3" y="-3" width="15" height="15" fill="#b58863"/>'
               f'<path d="{ring}" fill="#1c1a17"/><path d="{body}" fill="#fffaf0"/></svg>')
    write("assets/favicon.svg", fav)
    write(".nojekyll", "")
    url = cfg.get("site_url", "").rstrip("/")
    if url:
        today = datetime.date.today().isoformat()
        write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                             f'  <url><loc>{esc(url)}/</loc><lastmod>{today}</lastmod></url>\n</urlset>\n')
        write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {url}/sitemap.xml\n")
    else:
        write("robots.txt", "User-agent: *\nAllow: /\n")
    print("Built index.html, 404.html, favicon, robots.txt" + (", sitemap.xml" if url else ""))
    if not url:
        print("Tip: set site_url in site.json (for example https://your-username.github.io) for canonical links and a sitemap.")


if __name__ == "__main__":
    main()
