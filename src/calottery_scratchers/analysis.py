"""Expected-value analysis of scratcher games from published prize data.

Methodology
-----------
For each game, the lottery publishes, per prize tier, the total number of
prizes printed and how many have already been claimed. From this we derive
two numbers per game:

1. ``original_return_pct`` -- the expected return (as a fraction of ticket
   price) a ticket had on the game's launch day, computed from the full
   original prize pool.

2. ``remaining_return_pct`` -- the same calculation using only prizes that
   have *not yet* been claimed, i.e. the statistical return of a ticket
   bought *right now*, assuming remaining tickets are well-mixed across
   retailers (see Limitations below).

``edge_pct = remaining_return_pct - original_return_pct`` tells you whether
a game's remaining pool is currently better or worse than its lifetime
average -- e.g. because a disproportionate share of top prizes have already
been claimed, or the reverse.

We can't observe how many *tickets* (winning or losing) remain in
circulation directly, so we estimate it from the tier with the largest
prize count (almost always the lowest-value tier, which is the least noisy
signal): ``remaining_fraction ~= pending / total`` for that tier, applied to
the total-tickets estimate from the same tier (``total ~= tier.total_prizes
* tier.odds``).

Limitations (read before use)
------------------------------
* This ranks *games*, not tickets. It cannot tell you which specific
  physical ticket on a shelf will win -- outcomes on an individual ticket
  are still random and this tool does not and cannot change that.
* The remaining-fraction estimate assumes unsold tickets are randomly
  distributed across retailers, which is an approximation, not a fact.
* Ticket price is a poor proxy for variance/risk; a higher expected return
  does not mean a safer or "smarter" bet in the personal-finance sense.
* This is for informational/statistical purposes only. Lottery play is a
  form of gambling with negative expected value overall; please play
  responsibly.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import Game, PrizeTier


@dataclass
class GameStats:
    game_number: int
    name: str
    price: float
    game_type: str
    product_page: str

    total_tickets_est: float
    remaining_fraction_est: float

    original_ev: float
    original_return_pct: float

    remaining_ev: float
    remaining_return_pct: float

    top_prize_value: float
    top_prize_total: int
    top_prize_remaining: int

    @property
    def edge_pct(self) -> float:
        return self.remaining_return_pct - self.original_return_pct


def _anchor_tier(tiers: list[PrizeTier]) -> PrizeTier:
    """Pick the tier with the most prizes printed as the sampling anchor.

    This is (almost always) the lowest cash tier, which gives the most
    statistically stable estimate of how many tickets have moved through
    the system so far.
    """
    return max(tiers, key=lambda t: t.total_prizes)


def analyze_game(game: Game) -> GameStats | None:
    if not game.tiers:
        return None

    anchor = _anchor_tier(game.tiers)
    if anchor.odds <= 0 or anchor.total_prizes <= 0:
        return None

    total_tickets_est = anchor.total_prizes * anchor.odds
    remaining_fraction_est = anchor.prizes_pending / anchor.total_prizes
    remaining_tickets_est = total_tickets_est * remaining_fraction_est

    original_ev = sum(t.value * t.total_prizes for t in game.tiers) / total_tickets_est
    if remaining_tickets_est > 0:
        remaining_ev = sum(t.value * t.prizes_pending for t in game.tiers) / remaining_tickets_est
    else:
        remaining_ev = 0.0

    top_tier = max(game.tiers, key=lambda t: t.value)

    return GameStats(
        game_number=game.game_number,
        name=game.name,
        price=game.price,
        game_type=game.game_type,
        product_page=game.product_page,
        total_tickets_est=total_tickets_est,
        remaining_fraction_est=remaining_fraction_est,
        original_ev=original_ev,
        original_return_pct=original_ev / game.price * 100,
        remaining_ev=remaining_ev,
        remaining_return_pct=remaining_ev / game.price * 100,
        top_prize_value=top_tier.value,
        top_prize_total=top_tier.total_prizes,
        top_prize_remaining=top_tier.prizes_pending,
    )


def analyze_games(games: list[Game]) -> list[GameStats]:
    results = [analyze_game(g) for g in games]
    return [r for r in results if r is not None]


def rank_by_remaining_return(stats: list[GameStats], min_price: float | None = None,
                              max_price: float | None = None) -> list[GameStats]:
    filtered = stats
    if min_price is not None:
        filtered = [s for s in filtered if s.price >= min_price]
    if max_price is not None:
        filtered = [s for s in filtered if s.price <= max_price]
    return sorted(filtered, key=lambda s: s.remaining_return_pct, reverse=True)
