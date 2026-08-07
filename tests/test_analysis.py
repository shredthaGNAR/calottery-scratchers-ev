import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from calottery_scratchers.analysis import analyze_game, rank_by_remaining_return
from calottery_scratchers.models import Game, PrizeTier


def make_simple_game() -> Game:
    # A toy $1 game: 1,000,000 tickets, one $100 top prize, and low tiers.
    # Anchor tier (most prizes) is the $1 tier: total=500,000, odds=2 -> 1,000,000 tickets.
    tiers = [
        PrizeTier(level="H", value=100.0, odds=100000.0, total_prizes=10,
                   prizes_cashed=0, prizes_pending=10),
        PrizeTier(level="L", value=1.0, odds=2.0, total_prizes=500000,
                   prizes_cashed=250000, prizes_pending=250000),
    ]
    return Game(game_number=1, name="Test Game", price=1.0, tiers=tiers)


def test_analyze_game_original_ev():
    game = make_simple_game()
    stats = analyze_game(game)
    assert stats is not None
    # total tickets estimated from anchor tier: 500,000 * 2 = 1,000,000
    assert stats.total_tickets_est == 1_000_000
    # original EV = (100*10 + 1*500000) / 1,000,000 = 500010 / 1e6
    assert abs(stats.original_ev - (100 * 10 + 1 * 500000) / 1_000_000) < 1e-9


def test_analyze_game_remaining_ev_reflects_depleted_top_prizes():
    game = make_simple_game()
    # Deplete all top prizes but leave low tier untouched -> remaining EV should drop
    game.tiers[0].prizes_pending = 0
    game.tiers[0].prizes_cashed = 10
    stats = analyze_game(game)
    assert stats is not None
    assert stats.remaining_ev < stats.original_ev
    assert stats.edge_pct < 0


def test_rank_by_remaining_return_orders_descending():
    good = make_simple_game()
    good.game_number = 1

    bad = make_simple_game()
    bad.game_number = 2
    bad.tiers[0].prizes_pending = 0  # top prize gone -> worse remaining EV

    stats = [analyze_game(good), analyze_game(bad)]
    ranked = rank_by_remaining_return(stats)
    assert ranked[0].game_number == 1
    assert ranked[1].game_number == 2


def test_rank_by_remaining_return_price_filter():
    g1 = make_simple_game()
    g1.game_number = 1
    g1.price = 1.0

    g2 = make_simple_game()
    g2.game_number = 2
    g2.price = 5.0

    stats = [analyze_game(g1), analyze_game(g2)]
    ranked = rank_by_remaining_return(stats, min_price=2.0)
    assert [s.game_number for s in ranked] == [2]


def test_analyze_game_returns_none_for_empty_tiers():
    game = Game(game_number=99, name="Empty", price=1.0, tiers=[])
    assert analyze_game(game) is None
