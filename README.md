# calottery-scratchers-ev

**Live report:** https://shredthagnar.github.io/calottery-scratchers-ev/
— regenerated daily by [GitHub Actions](.github/workflows/daily-report.yml).

Statistical expected-value analysis of California Lottery Scratchers,
built entirely from data the CA Lottery itself publishes for
transparency: per game, per prize tier, how many prizes were printed
and how many have already been claimed.

## What this actually does (and doesn't do)

This tool **ranks scratcher games** by their estimated statistical
expected return, using the same public "prizes remaining" data CA
Lottery shows on its own website. It does **not** and **cannot**
predict the outcome of any individual physical ticket — each ticket's
outcome is fixed at printing time and independent of this analysis.
What *does* vary game-to-game is the mix of big and small prizes still
unclaimed, which is public information you can use to compare games
before you buy — the same idea behind well-known published scratcher
overall-odds/EV analyses.

Read [`src/calottery_scratchers/analysis.py`](src/calottery_scratchers/analysis.py)
for the full methodology and its assumptions/limitations. Short version:

- **Original EV** — the expected return per ticket a game had at launch,
  computed from its full original prize pool.
- **Remaining EV** — the same calculation using only prizes not yet
  claimed, i.e. the statistical return of a ticket bought right now,
  *assuming* remaining tickets are evenly mixed across retailers (an
  approximation, not a guarantee).
- **Edge** — remaining EV minus original EV, in percentage points:
  positive means the remaining pool is currently richer than the
  game's lifetime average; negative means it's been picked over.

This is informational only. Lottery games have negative expected value
overall by design — the games with the "best" remaining EV in this
tool are still, in expectation, a loss. Please play responsibly; if
gambling is a problem for you, call 1-800-GAMBLER.

## Data source

`GET https://www.calottery.com/api/games/scratchers` — the same public
JSON endpoint that powers the "Top Prizes Remaining" table on
[calottery.com/scratchers](https://www.calottery.com/en/scratchers).
No authentication, scraping of private data, or bypassing of any
access control is involved.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Usage

```bash
# 1. Download the latest public dataset (writes to ./data)
python -m calottery_scratchers --data-dir data fetch

# 2. Print a ranked table (top 25 by default, all price points)
python -m calottery_scratchers --data-dir data analyze

# Filter to $10+ games, show all of them, as CSV
python -m calottery_scratchers --data-dir data analyze --min-price 10 --top 0 --format csv

# 3. Generate a standalone HTML report
python -m calottery_scratchers --data-dir data report --out report.html
```

Add `src` to `PYTHONPATH` (or run from the repo root with `PYTHONPATH=src`)
if you haven't installed the package:

```bash
PYTHONPATH=src python -m calottery_scratchers fetch
```

## Tests

```bash
pip install -r requirements-dev.txt
PYTHONPATH=src pytest
```

Tests run against a small synthetic fixture, not the live API.

## Automated daily report

[`.github/workflows/daily-report.yml`](.github/workflows/daily-report.yml)
runs once a day (and on-demand via the Actions tab): it fetches the
latest public dataset, regenerates the HTML report, and publishes it to
GitHub Pages. No secrets are required since the data source is public.

## Project layout

```
src/calottery_scratchers/
  fetch.py      # downloads + caches the public dataset
  models.py     # Game / PrizeTier data classes
  analysis.py   # expected-value math + methodology docs
  report.py     # text table / CSV / HTML rendering
  cli.py        # fetch / analyze / report subcommands
tests/
  test_analysis.py
data/           # cached JSON snapshots (gitignored)
```

## License

MIT — see [LICENSE](LICENSE).
