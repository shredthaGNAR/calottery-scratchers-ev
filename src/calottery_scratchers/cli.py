"""Command-line interface: fetch data, analyze it, or emit a report."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import fetch, report
from .analysis import analyze_games, rank_by_remaining_return
from .models import Game


def _load_games(data_dir: Path) -> list[Game]:
    payload = fetch.load_latest(data_dir=data_dir)
    raw_games = payload["data"]["games"]
    return [Game.from_api(g) for g in raw_games]


def cmd_fetch(args: argparse.Namespace) -> int:
    path = fetch.fetch_and_save(data_dir=args.data_dir)
    print(f"Saved snapshot to {path}")
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    games = _load_games(args.data_dir)
    stats = analyze_games(games)
    ranked = rank_by_remaining_return(stats, min_price=args.min_price, max_price=args.max_price)
    if args.top:
        ranked = ranked[: args.top]

    if args.format == "csv":
        print(report.to_csv(ranked))
    else:
        print(report.to_text_table(ranked))
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    games = _load_games(args.data_dir)
    stats = analyze_games(games)
    ranked = rank_by_remaining_return(stats, min_price=args.min_price, max_price=args.max_price)
    generated_at = datetime.now(timezone.utc).isoformat()
    report.write_html(ranked, args.out, generated_at=generated_at)
    print(f"Wrote {args.out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calottery-scratchers",
        description="Expected-value analysis of CA Lottery Scratchers from public data.",
    )
    parser.add_argument(
        "--data-dir", type=Path, default=fetch.DEFAULT_DATA_DIR,
        help="Directory to read/write cached snapshots (default: ./data)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_fetch = sub.add_parser("fetch", help="Download the latest public dataset")
    p_fetch.set_defaults(func=cmd_fetch)

    p_analyze = sub.add_parser("analyze", help="Print a ranked table of games by expected value")
    p_analyze.add_argument("--top", type=int, default=25, help="Show only the top N games (0 = all)")
    p_analyze.add_argument("--min-price", type=float, default=None)
    p_analyze.add_argument("--max-price", type=float, default=None)
    p_analyze.add_argument("--format", choices=["table", "csv"], default="table")
    p_analyze.set_defaults(func=cmd_analyze)

    p_report = sub.add_parser("report", help="Write a standalone HTML report")
    p_report.add_argument("--out", type=Path, default=Path("report.html"))
    p_report.add_argument("--min-price", type=float, default=None)
    p_report.add_argument("--max-price", type=float, default=None)
    p_report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "top", None) == 0:
        args.top = None
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
