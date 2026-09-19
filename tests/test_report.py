import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from calottery_scratchers.analysis import analyze_game
from calottery_scratchers.models import Game, PrizeTier
from calottery_scratchers.report import to_html


def make_game() -> Game:
    tiers = [
        PrizeTier(level="H", value=100.0, odds=100000.0, total_prizes=10,
                   prizes_cashed=0, prizes_pending=10),
        PrizeTier(level="L", value=1.0, odds=2.0, total_prizes=500000,
                   prizes_cashed=250000, prizes_pending=250000),
    ]
    return Game(game_number=1, name="Test <Game>", price=1.0, tiers=tiers)


def test_html_inlines_design_system_styles():
    page = to_html([analyze_game(make_game())], generated_at="2026-01-01T00:00:00Z")
    assert "--surface: #ffffff;" in page
    assert "@media (prefers-color-scheme: dark)" in page
    assert ".sev-table th" in page
    assert '<body class="sev-report">' in page
    assert '<table class="sev-table">' in page


def test_html_marks_edge_cell_and_escapes_names():
    page = to_html([analyze_game(make_game())], generated_at="2026-01-01T00:00:00Z")
    assert 'class="sev-positive"' in page or 'class="sev-negative"' in page
    assert "Test &lt;Game&gt;" in page
