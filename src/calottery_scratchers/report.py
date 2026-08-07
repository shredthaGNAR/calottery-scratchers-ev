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


_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>CA Lottery Scratchers -- Expected Value Ranking</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; color: #1a1a1a; }}
  h1 {{ font-size: 1.4rem; }}
  .disclaimer {{ background: #fff8e1; border: 1px solid #e0c36b; padding: 0.75rem 1rem;
                 border-radius: 6px; font-size: 0.9rem; margin-bottom: 1.5rem; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.9rem; }}
  th, td {{ border: 1px solid #ddd; padding: 0.4rem 0.6rem; text-align: right; }}
  th {{ background: #f4f4f4; position: sticky; top: 0; }}
  td:nth-child(2), th:nth-child(2) {{ text-align: left; }}
  tr:nth-child(even) {{ background: #fafafa; }}
  .positive {{ color: #1a7a1a; }}
  .negative {{ color: #b02a2a; }}
  footer {{ margin-top: 1.5rem; font-size: 0.8rem; color: #666; }}
</style>
</head>
<body>
<h1>CA Lottery Scratchers -- Expected Value Ranking</h1>
<p class="disclaimer">
  Statistical estimates derived from the CA Lottery's public remaining-prize
  data, generated at {generated_at}. This ranks games by estimated expected
  return, not individual ticket outcomes -- it cannot predict which specific
  ticket wins. Remaining-tickets estimates assume even mixing across
  retailers, which is an approximation. Lottery play has negative expected
  value overall; please play responsibly.
</p>
<table>
<thead><tr>{header_cells}</tr></thead>
<tbody>
{body_rows}
</tbody>
</table>
<footer>Source: calottery.com public scratchers API.</footer>
</body>
</html>
"""


def to_html(stats: list[GameStats], generated_at: str) -> str:
    header_cells = "".join(f"<th>{html.escape(h)}</th>" for _, h in COLUMNS)
    body_rows = []
    for s in stats:
        cells = _row_values(s)
        edge_class = "positive" if s.edge_pct >= 0 else "negative"
        tds = "".join(
            f'<td class="{edge_class}">{html.escape(c)}</td>' if i == 5 else f"<td>{html.escape(c)}</td>"
            for i, c in enumerate(cells)
        )
        body_rows.append(f"<tr>{tds}</tr>")
    return _HTML_TEMPLATE.format(
        generated_at=html.escape(generated_at),
        header_cells=header_cells,
        body_rows="\n".join(body_rows),
    )


def write_html(stats: list[GameStats], path: Path, generated_at: str) -> None:
    path.write_text(to_html(stats, generated_at))
