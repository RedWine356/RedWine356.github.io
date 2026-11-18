# Setup (about 15 minutes)

## 1. Fill in your content
Open `site.json` and replace every placeholder. The `skill_layers`, `projects` (name, repo, desc, result,
status, difficulty, tags) and `piece` fields use the same shape as your GitHub profile kit's `profile.json`,
so you can copy them across. Extra fields for the site:

| Field | What it does |
|-------|--------------|
| `highlights` | Three headline numbers under your name. Use real, checkable results |
| `about.paragraphs` / `facts` | Your story and quick facts |
| `model_card` | A small "model card" about you: intended use, limitations, evaluation |
| `projects[].category` | Creates the filter buttons (NLP, Vision, ...) |
| `projects[].role` | Say exactly what you did on team projects |
| `projects[].case_study` | Optional expandable write-up: problem, approach, outcome, learned |
| `projects[].links` | `demo` and `writeup` URLs. The Code link comes from `repo` |
| `timeline` | Your journey, shown as a numbered move list |
| `writing` | Optional posts, papers or talks |

Put your resume at `assets/resume.pdf` (or change `resume`).

## 2. Build and preview
    python build_site.py
    python -m http.server 8000
Open http://localhost:8000. Try the board: click the piece, then a marked square.

## 3. Publish on GitHub Pages
1. Create a public repo named exactly `your-username.github.io`.
2. Set `site_url` in `site.json` to `https://your-username.github.io`, then run `python build_site.py` again.
3. Push everything in this folder to the `main` branch.
4. On GitHub: Settings, then Pages, then "Deploy from a branch", branch `main`, folder `/ (root)`.
5. After a minute or two your site is live at `https://your-username.github.io`.

Note: `404.html` uses absolute paths, so it expects the site at the root of a domain
(`your-username.github.io` or a custom domain), not a project subpath.

## 4. Connect it to everything else
- GitHub profile: add the site URL in Edit profile, Website.
- Profile README kit: set the portfolio link in its `profile.json` and rebuild.
- LinkedIn and your resume: use the same URL.
- Optional social preview: add a 1200x630 PNG at `assets/og.png`, set `"og_image": "assets/og.png"`, rebuild.
- Optional custom domain: add it under Settings, Pages, and create a `CNAME` file with the domain.

## 5. Final checks
- Run the placeholder search in `CLAUDE.md` and fix anything it finds.
- Open it on your phone. Tab through it with the keyboard. Switch the light and dark theme.
- Click every link.
