"""Draw the README's leaderboard chart from the results files (no model calls, no plotting library).

    uv run python scripts/release/make_readme_figures.py [--check]

Writes docs/assets/readme/leaderboard-{light,dark}.svg: the README shows the light or the dark one with the reader's
colour scheme. The numbers are the leaderboard's (scripts/leaderboard.py): the score over all scenarios, released and
held out, with its 95% interval. --check exits 1 if a written chart differs from what the results files give.
"""
from __future__ import annotations

import json
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import leaderboard as lb  # noqa: E402

OUT = ROOT / "docs/assets/readme"
FONT = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
# The website's palette (site.css), with a dark variant for GitHub's dark theme.
THEMES = {
    "light": {"ink": "#16171b", "ink2": "#41434a", "ink3": "#676a72", "rule": "#e9e9ee", "closed": "#2f54d8",
              "open": "#a3a5ad"},
    "dark": {"ink": "#e6edf3", "ink2": "#c9d1d9", "ink3": "#8b949e", "rule": "#30363d", "closed": "#6d8cff",
             "open": "#6e7681"},
}
NAME_W, PLOT_W, ROW = 200, 520, 30


def svg(w: int, h: int, body: list[str], title: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'font-family="{FONT}" role="img" aria-label="{escape(title)}">\n<title>{escape(title)}</title>\n'
            + "\n".join(body) + "\n</svg>\n")


def text(x: float, y: float, s: str, fill: str, size: int = 13, anchor: str = "start", weight: int = 400) -> str:
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}">{escape(s)}</text>')


def axis(c: dict, x0: float, top: float, bottom: float) -> list[str]:
    out = []
    for v in (0, 25, 50, 75, 100):
        x = x0 + PLOT_W * v / 100
        out.append(f'<line x1="{x:.1f}" y1="{top:.1f}" x2="{x:.1f}" y2="{bottom:.1f}" stroke="{c["rule"]}" stroke-width="1"/>')
        out.append(text(x, bottom + 16, str(v), c["ink3"], 11, "middle"))
    return out


def results() -> list[tuple[dict, bool]]:
    return [(json.loads((ROOT / "results/final_results.json").read_text()), False),
            (json.loads((ROOT / "results/recent_models_results.json").read_text()), True)]


def leaderboard_svg(c: dict, res: list[tuple[dict, bool]]) -> str:
    rs = lb.rows(res)
    x0, top = NAME_W, 52
    h = top + ROW * len(rs) + 34
    w = x0 + PLOT_W + 70
    body = [text(16, 22, "■", c["closed"], 14), text(32, 22, "Closed model", c["ink2"], 12),
            text(132, 22, "■", c["open"], 14), text(148, 22, "Open-weight model", c["ink2"], 12),
            f'<line x1="282" y1="17" x2="306" y2="17" stroke="{c["ink3"]}" stroke-width="1.5"/>'
            f'<line x1="282" y1="12" x2="282" y2="22" stroke="{c["ink3"]}" stroke-width="1.5"/>'
            f'<line x1="306" y1="12" x2="306" y2="22" stroke="{c["ink3"]}" stroke-width="1.5"/>',
            text(314, 22, "95% interval", c["ink2"], 12)]
    body += axis(c, x0, top - 8, top + ROW * len(rs))
    for k, (m, R, _later) in enumerate(rs):
        o = lb.ov(R, m)
        y = top + ROW * k
        col = c["open"] if m in lb.OPEN else c["closed"]
        mark = "†" if o.get("dimensions_not_run") else ""
        body.append(text(28, y + 15, str(k + 1), c["ink3"], 12, "end"))
        body.append(text(40, y + 15, lb.NAME.get(m, m) + mark, c["ink"], 13, weight=500))
        bw = PLOT_W * o["score"]
        body.append(f'<rect x="{x0}" y="{y + 4}" width="{bw:.1f}" height="16" rx="3" fill="{col}"/>')
        lo, hi = (x0 + PLOT_W * v for v in o["ci"])
        body.append(f'<line x1="{lo:.1f}" y1="{y + 12}" x2="{hi:.1f}" y2="{y + 12}" stroke="{c["ink"]}" stroke-width="1.3" opacity="0.75"/>'
                    f'<line x1="{lo:.1f}" y1="{y + 8}" x2="{lo:.1f}" y2="{y + 16}" stroke="{c["ink"]}" stroke-width="1.3" opacity="0.75"/>'
                    f'<line x1="{hi:.1f}" y1="{y + 8}" x2="{hi:.1f}" y2="{y + 16}" stroke="{c["ink"]}" stroke-width="1.3" opacity="0.75"/>')
        body.append(text(hi + 8, y + 16, lb.pct(o["score"]), c["ink"], 13, weight=600))
    return svg(w, h, body, "Leaderboard: score over all 240 scenarios with 95% intervals")


def figures() -> dict[str, str]:
    res = results()
    out = {}
    for t, c in THEMES.items():
        out[f"leaderboard-{t}.svg"] = leaderboard_svg(c, res)
    return out


def main() -> None:
    figs = figures()
    if "--check" in sys.argv[1:]:
        stale = [n for n, s in figs.items() if not (OUT / n).exists() or (OUT / n).read_text() != s]
        if stale:
            print("stale README chart: " + ", ".join(stale) + " (run scripts/release/make_readme_figures.py)")
            sys.exit(1)
        print(f"{len(figs)} README chart files match the results files")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    for n, s in figs.items():
        (OUT / n).write_text(s)
    print(f"wrote {len(figs)} figures to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
