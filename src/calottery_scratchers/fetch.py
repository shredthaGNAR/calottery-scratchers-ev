"""Fetch the public CA Lottery Scratchers dataset.

The California Lottery publishes live scratcher game data -- including,
per prize tier, the total number of prizes printed and how many have
already been cashed -- at a public JSON endpoint that backs the
"Top Prizes Remaining" table on calottery.com/scratchers. This module
just downloads and caches that JSON; no authentication or scraping of
non-public data is involved.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

API_URL = "https://www.calottery.com/api/games/scratchers"
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
LATEST_FILENAME = "latest.json"
USER_AGENT = (
    "calottery-scratchers-ev/0.1 "
    "(+https://github.com/; educational statistical analysis tool)"
)


class FetchError(RuntimeError):
    pass


def fetch_raw(timeout: float = 20.0, retries: int = 3, backoff: float = 1.5) -> dict[str, Any]:
    """Download the current scratchers dataset from the public API.

    Retries with exponential backoff on transient failures. Raises
    FetchError if the request ultimately fails or the response is not
    the JSON shape we expect.
    """
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    last_exc: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(API_URL, headers=headers, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            if "games" not in data:
                raise FetchError(f"Unexpected response shape: keys={list(data)[:10]}")
            return data
        except (requests.RequestException, ValueError, FetchError) as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(backoff ** attempt)

    raise FetchError(f"Failed to fetch scratchers data after {retries} attempts") from last_exc


def save_snapshot(data: dict[str, Any], data_dir: Path = DEFAULT_DATA_DIR) -> Path:
    """Persist a fetched snapshot to data/<timestamp>.json and refresh data/latest.json."""
    data_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_path = data_dir / f"scratchers_{stamp}.json"

    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": API_URL,
        "data": data,
    }

    snapshot_path.write_text(json.dumps(payload, indent=2))
    (data_dir / LATEST_FILENAME).write_text(json.dumps(payload, indent=2))
    return snapshot_path


def load_latest(data_dir: Path = DEFAULT_DATA_DIR) -> dict[str, Any]:
    latest_path = data_dir / LATEST_FILENAME
    if not latest_path.exists():
        raise FetchError(
            f"No cached data at {latest_path}. Run `calottery-scratchers fetch` first."
        )
    return json.loads(latest_path.read_text())


def fetch_and_save(data_dir: Path = DEFAULT_DATA_DIR) -> Path:
    data = fetch_raw()
    return save_snapshot(data, data_dir=data_dir)
