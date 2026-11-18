# Chess portfolio: project notes for Claude Code

A static personal portfolio for a machine learning student, hosted on GitHub Pages. It matches the
owner's GitHub profile README (same chess theme, same piece).

## How it works
- `site.json` is the single source of content. `build_site.py` turns it into `index.html`, `404.html`,
  `assets/favicon.svg`, `robots.txt` and (if `site_url` is set) `sitemap.xml`.
- `assets/style.css` and `assets/site.js` are hand-written. They are not generated.
- Python standard library only. No frameworks, no npm, no build step beyond `python build_site.py`.

## Commands
- Build: `python build_site.py`
- Preview: `python -m http.server 8000`, then open http://localhost:8000

## Rules
1. Edit `site.json`, never `index.html` directly (it is overwritten on every build).
2. Never invent facts. Do not make up metrics, results, dates, employers, skills or links.
   If a value is missing, leave a visible TODO and ask the owner.
3. Keep it static and private: no analytics, no trackers, no cookies, no third-party scripts or fonts,
   no network requests.
4. Keep accessibility intact: one `h1`, ordered headings, visible focus styles, keyboard-operable
   board and skill graph, `prefers-reduced-motion` respected, text contrast of at least 4.5:1 in both themes.
5. Keep the page working without JavaScript (content visible, static board piece).
6. To add a section, add its data to `site.json`, a function in `build_site.py`, and styles in `style.css`.

## Before publishing
Run this and fix anything it finds (it should print nothing):

    grep -rniE "your-username|example\.com|Your Name|City, Country|replace with|your university" site.json index.html

Then check: all links work, `resume` points at a real file, `site_url` is set, the site looks right
on a phone-width window, and every number on the page is one the owner can defend in an interview.
