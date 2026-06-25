"""Pick the daily WES message based on date signals."""

import json
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo


FIXED_HOLIDAYS = {
    (1, 1):   "ano_novo",
    (5, 1):   "trabalhador",
    (6, 12):  "namorados",
    (11, 2):  "finados",
    (12, 25): "natal",
    (12, 31): "reveillon",
}

EPOCH = date(1970, 1, 1)


def pick_message(today: date, messages: dict) -> str:
    """Return today's WES message from the curated pool.

    Priority chain: fixed-date holiday > Friday-the-13th > Monday > odd/even.
    Within the chosen pool, the message is selected by sequential rotation
    keyed off the number of days since the Unix epoch, so the same date
    always yields the same message and every message in a pool is seen
    before any repeats.
    """
    pool = _select_pool(today, messages)
    idx = (today - EPOCH).days % len(pool)
    return pool[idx]


def _select_pool(today: date, messages: dict) -> list:
    holiday_key = FIXED_HOLIDAYS.get((today.month, today.day))
    if holiday_key is not None:
        return messages["holidays"][holiday_key]
    if today.weekday() == 4 and today.day == 13:  # Friday the 13th
        return messages["holidays"]["sexta_13"]
    if today.weekday() == 0:  # Monday
        return messages["monday"]
    if today.day % 2 == 1:
        return messages["odd"]
    return messages["even"]


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    with (repo_root / "messages" / "messages.json").open(encoding="utf-8") as f:
        messages = json.load(f)
    today = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    sys.stdout.write(pick_message(today, messages))


if __name__ == "__main__":
    main()
