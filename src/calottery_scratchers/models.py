"""Data structures for CA Lottery Scratchers games and prize tiers."""

from __future__ import annotations

import html
from dataclasses import dataclass, field


@dataclass
class PrizeTier:
    """A single prize level within a scratcher game.

    Fields map directly onto the CA Lottery public API response for
    ``GET /api/games/scratchers``.
    """

    level: str
    value: float
    odds: float  # "1 in N" chance of this tier at the start of the game
    total_prizes: int
    prizes_cashed: int
    prizes_pending: int  # prizes not yet claimed -- i.e. still "in the wild"
    prize_type: str = "Cash Prize"

    @property
    def prizes_remaining(self) -> int:
        return self.prizes_pending

    @classmethod
    def from_api(cls, raw: dict) -> "PrizeTier":
        return cls(
            level=raw.get("level") or "",
            value=float(raw["value"]),
            odds=float(raw["odds"]),
            total_prizes=int(raw["totalNumberOfPrizes"]),
            prizes_cashed=int(raw["numberOfPrizesCashed"]),
            prizes_pending=int(raw["numberOfPrizesPending"]),
            prize_type=raw.get("type") or "Cash Prize",
        )


@dataclass
class Game:
    """A single scratcher game and its full prize structure."""

    game_number: int
    name: str
    price: float
    game_type: str = ""
    product_page: str = ""
    tiers: list[PrizeTier] = field(default_factory=list)

    @classmethod
    def from_api(cls, raw: dict) -> "Game":
        tiers = [PrizeTier.from_api(t) for t in raw.get("prizeTiers", [])]
        return cls(
            game_number=int(raw["gameNumber"]),
            # The API sends names HTML-escaped ("LOTERIA&trade;"); decode once
            # here so every output carries the real characters and the HTML
            # report re-escapes them itself.
            name=html.unescape(
                raw.get("name") or raw.get("marketingTitle") or f"Game {raw.get('gameNumber')}"
            ),
            price=float(raw["price"]),
            game_type=raw.get("gameType") or "",
            product_page=raw.get("productPage") or "",
            tiers=tiers,
        )
