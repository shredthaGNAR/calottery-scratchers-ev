"""Render GameStats rankings as a table, CSV, or standalone HTML page."""

from __future__ import annotations

import csv
import html
import io
from pathlib import Path

from .analysis import GameStats

COLUMNS = [
    ("game_number", "Game #"),
    ("name", "Name"),
    ("price", "Price"),
    ("remaining_return_pct", "Remaining EV %"),
    ("original_return_pct", "Original EV %"),
    ("edge_pct", "Edge (pp)"),
    ("remaining_fraction_est", "Est. % tickets left"),
    ("top_prize_remaining", "Top prizes left"),
    ("top_prize_total", "Top prizes total"),
]


def _row_values(s: GameStats) -> list[str]:
    return [
        str(s.game_number),
        s.name,
        f"${s.price:.0f}",
        f"{s.remaining_return_pct:.1f}%",
        f"{s.original_return_pct:.1f}%",
        f"{s.edge_pct:+.1f}",
        f"{s.remaining_fraction_est * 100:.1f}%",
        str(s.top_prize_remaining),
        str(s.top_prize_total),
    ]


def to_text_table(stats: list[GameStats]) -> str:
    headers = [h for _, h in COLUMNS]
    rows = [_row_values(s) for s in stats]
    widths = [max(len(h), *(len(r[i]) for r in rows)) if rows else len(h)
              for i, h in enumerate(headers)]

    def fmt_row(cells: list[str]) -> str:
        return "  ".join(c.ljust(w) for c, w in zip(cells, widths))

    lines = [fmt_row(headers), fmt_row(["-" * w for w in widths])]
    lines.extend(fmt_row(r) for r in rows)
    return "\n".join(lines)


def to_csv(stats: list[GameStats]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([h for _, h in COLUMNS])
    for s in stats:
        writer.writerow(_row_values(s))
    return buf.getvalue()


STYLES_DIR = Path(__file__).parent / "styles"
# Design-system stylesheets, in load order: tokens (CSS variables per theme),
# then the .sev-* component classes that read them.
STYLESHEETS = ("tokens.css", "bundle.css")


def _inline_styles() -> str:
    return "\n".join((STYLES_DIR / name).read_text() for name in STYLESHEETS)


_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="color-scheme" content="light dark">
<title>CA Lottery Scratchers -- Expected Value Ranking</title>
<style>
{styles}
</style>
</head>
<body class="sev-report">
<h1 class="sev-title">CA Lottery Scratchers -- Expected Value Ranking</h1>
<p class="sev-disclaimer">
  Statistical estimates derived from the CA Lottery's public remaining-prize
  data, generated at {generated_at}. This ranks games by estimated expected
  return, not individual ticket outcomes -- it cannot predict which specific
  ticket wins. Remaining-tickets estimates assume even mixing across
  retailers, which is an approximation. Lottery play has negative expected
  value overall; please play responsibly.
</p>
<table class="sev-table">
<thead><tr>{header_cells}</tr></thead>
<tbody>
{body_rows}
</tbody>
</table>
<footer class="sev-footer">Source: calottery.com public scratchers API.</footer>
</body>
</html>
"""


def to_html(stats: list[GameStats], generated_at: str) -> str:
    header_cells = "".join(f"<th>{html.escape(h)}</th>" for _, h in COLUMNS)
    body_rows = []
    for s in stats:
        cells = _row_values(s)
        edge_class = "sev-positive" if s.edge_pct >= 0 else "sev-negative"
        tds = "".join(
            f'<td class="{edge_class}">{html.escape(c)}</td>' if i == 5 else f"<td>{html.escape(c)}</td>"
            for i, c in enumerate(cells)
        )
        body_rows.append(f"<tr>{tds}</tr>")
    return _HTML_TEMPLATE.format(
        styles=_inline_styles(),
        generated_at=html.escape(generated_at),
        header_cells=header_cells,
        body_rows="\n".join(body_rows),
    )


def write_html(stats: list[GameStats], path: Path, generated_at: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_html(stats, generated_at))
