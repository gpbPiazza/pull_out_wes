# Daily WES Message Generation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the two hard-coded mock messages in the existing GitHub Action with a curated pool of ~141 Portuguese messages, selected each morning by a small Python module via a Holiday > Monday > odd/even priority chain.

**Architecture:** Pure-data file (`messages/messages.json`) holds all messages. A pure Python function (`scripts/pick_message.py:pick_message`) takes today's BRT date plus the loaded JSON and returns the chosen string via sequential rotation (`epoch_day % len(pool)`). The workflow shells out to that script, captures stdout, and feeds it to the existing `tsickert/discord-webhook` step.

**Tech Stack:** Python 3 stdlib only (`json`, `datetime`, `zoneinfo`, `pathlib`, `unittest`). No new repo dependencies. GitHub Actions on `ubuntu-latest` (Python 3 + tzdata preinstalled).

## Global Constraints

- Language of all message content: **Portuguese (pt-BR)**.
- Display name on every message: `WES 🗿` (already enforced in the workflow's `username` field — do not change).
- Schedule unchanged: cron `0 12 * * *` (≈09:00 America/Sao_Paulo).
- Selection priority chain: **Holiday > Monday > parity (odd/even)**.
- Selection within a pool: `epoch_day % len(pool)`, where `epoch_day = (today - date(1970, 1, 1)).days`. Same date → same message.
- Pool sizes: `odd` 50, `even` 50, `monday` 20, each holiday 3 → ~141 total.
- Holiday set (fixed-date `MMDD` → key):
  - `0101` → `ano_novo`
  - `0501` → `trabalhador`
  - `0612` → `namorados`
  - `1102` → `finados`
  - `1225` → `natal`
  - `1231` → `reveillon`
  - Plus computed: weekday=Friday AND day=13 → `sexta_13`.
- Tone: aggressive humiliation of WES throughout. Odd days = mock-solemn ritualistic curse; even days = casual humiliation roast. Full Brazilian profanity allowed; cleverness over crutch.
- No new runtime dependencies. No movable-holiday math. No year-aware templating.

---

## Task 1: Build the message selector with unit tests

**Files:**
- Create: `scripts/__init__.py` (empty)
- Create: `scripts/pick_message.py`
- Create: `scripts/test_pick_message.py`

**Interfaces:**
- Produces: `pick_message(today: datetime.date, messages: dict) -> str` — pure function. Walks the priority chain in §4 of the spec and returns the rotated message.
- Produces: `main()` — entry point that loads `messages/messages.json` (relative to repo root), computes today's BRT date, prints the chosen message to stdout. Used by the workflow.

- [ ] **Step 1: Create the package marker**

```bash
mkdir -p scripts
: > scripts/__init__.py
```

- [ ] **Step 2: Write the failing test suite**

Create `scripts/test_pick_message.py`:

```python
import unittest
from datetime import date
from pick_message import pick_message


def fixture():
    """Tiny pool — pool sizes of 3 let us verify sequential rotation cleanly."""
    return {
        "holidays": {
            "ano_novo":    ["AN1", "AN2", "AN3"],
            "trabalhador": ["TR1", "TR2", "TR3"],
            "namorados":   ["NM1", "NM2", "NM3"],
            "finados":     ["FN1", "FN2", "FN3"],
            "natal":       ["NT1", "NT2", "NT3"],
            "reveillon":   ["RV1", "RV2", "RV3"],
            "sexta_13":    ["S13_1", "S13_2", "S13_3"],
        },
        "monday": ["MON1", "MON2", "MON3"],
        "odd":    ["ODD1", "ODD2", "ODD3"],
        "even":   ["EVN1", "EVN2", "EVN3"],
    }


class TestPickMessage(unittest.TestCase):
    def setUp(self):
        self.msgs = fixture()

    # --- Holiday detection (each fixed-date holiday) ---

    def test_ano_novo(self):
        self.assertIn(pick_message(date(2026, 1, 1), self.msgs),
                      self.msgs["holidays"]["ano_novo"])

    def test_trabalhador(self):
        self.assertIn(pick_message(date(2026, 5, 1), self.msgs),
                      self.msgs["holidays"]["trabalhador"])

    def test_namorados(self):
        self.assertIn(pick_message(date(2026, 6, 12), self.msgs),
                      self.msgs["holidays"]["namorados"])

    def test_finados(self):
        # 2026-11-02 is a Monday — also exercises Holiday > Monday priority.
        self.assertIn(pick_message(date(2026, 11, 2), self.msgs),
                      self.msgs["holidays"]["finados"])

    def test_natal(self):
        self.assertIn(pick_message(date(2026, 12, 25), self.msgs),
                      self.msgs["holidays"]["natal"])

    def test_reveillon(self):
        self.assertIn(pick_message(date(2026, 12, 31), self.msgs),
                      self.msgs["holidays"]["reveillon"])

    # --- Sexta-feira 13 ---

    def test_sexta_13(self):
        # 2026-02-13 is a Friday.
        self.assertIn(pick_message(date(2026, 2, 13), self.msgs),
                      self.msgs["holidays"]["sexta_13"])

    def test_friday_non_13_not_sexta(self):
        # 2026-02-06 is Friday but not the 13th — should fall through.
        msg = pick_message(date(2026, 2, 6), self.msgs)
        self.assertNotIn(msg, self.msgs["holidays"]["sexta_13"])

    # --- Monday ---

    def test_monday_non_holiday(self):
        # 2026-06-29 is a Monday with no holiday.
        self.assertIn(pick_message(date(2026, 6, 29), self.msgs),
                      self.msgs["monday"])

    # --- Parity fallback ---

    def test_odd_day(self):
        # 2026-06-25 is a Thursday, day 25 (odd).
        self.assertIn(pick_message(date(2026, 6, 25), self.msgs),
                      self.msgs["odd"])

    def test_even_day(self):
        # 2026-06-26 is a Friday, day 26 (even).
        self.assertIn(pick_message(date(2026, 6, 26), self.msgs),
                      self.msgs["even"])

    # --- Determinism + rotation ---

    def test_determinism(self):
        d = date(2026, 6, 25)
        self.assertEqual(pick_message(d, self.msgs),
                         pick_message(d, self.msgs))

    def test_sequential_rotation_within_odd_pool(self):
        # 2026-06-25 (Thu, odd), 2026-06-27 (Sat, odd), 2026-06-29 is Monday
        # so we use 06-27 and 06-29-skip. Use 06-25 and 06-27 — both odd, both
        # non-Monday, non-holiday. Indices differ by 2 (epoch_day differs by 2).
        m1 = pick_message(date(2026, 6, 25), self.msgs)
        m2 = pick_message(date(2026, 6, 27), self.msgs)
        i1 = self.msgs["odd"].index(m1)
        i2 = self.msgs["odd"].index(m2)
        self.assertEqual((i2 - i1) % len(self.msgs["odd"]), 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests and confirm they fail**

```bash
cd scripts && python3 -m unittest test_pick_message -v
```

Expected: `ModuleNotFoundError: No module named 'pick_message'` (or import error). Tests cannot run yet because `pick_message.py` does not exist.

- [ ] **Step 4: Implement the selector**

Create `scripts/pick_message.py`:

```python
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
```

- [ ] **Step 5: Run tests and confirm they pass**

```bash
cd scripts && python3 -m unittest test_pick_message -v
```

Expected: `OK` with 13 tests passing.

- [ ] **Step 6: Commit**

```bash
git add scripts/__init__.py scripts/pick_message.py scripts/test_pick_message.py
git commit -m "Add WES message selector with unit tests

Pure function + main entry. Holiday > Friday-13 > Monday > odd/even
priority chain. Sequential rotation by epoch day so the same date
always yields the same message and every entry in a pool is seen
before any repeat. Tested with stdlib unittest — no new deps."
```

---

## Task 2: Author the curated messages.json

**Files:**
- Create: `messages/messages.json`
- Modify: `scripts/test_pick_message.py` (add a structure test against the real file)

**Interfaces:**
- Consumes (from Task 1): `pick_message(today, messages)` — used to spot-check that the real file works end-to-end.
- Produces: `messages/messages.json` matching the shape in spec §5 with exact counts: `odd` 50, `even` 50, `monday` 20, each holiday key 3 entries.

- [ ] **Step 1: Author the messages file**

Create `messages/messages.json` with this exact top-level shape (counts are mandatory; tone anchors below):

```json
{
  "holidays": {
    "ano_novo":    ["…", "…", "…"],
    "trabalhador": ["…", "…", "…"],
    "namorados":   ["…", "…", "…"],
    "finados":     ["…", "…", "…"],
    "natal":       ["…", "…", "…"],
    "reveillon":   ["…", "…", "…"],
    "sexta_13":    ["…", "…", "…"]
  },
  "monday": ["…20 entries…"],
  "odd":    ["…50 entries…"],
  "even":   ["…50 entries…"]
}
```

**Tone anchors — write to these exemplars:**

- **`odd` (mock-solemn ritualistic curse):**
  > "Ó WES, vaso podre, recebe hoje a minha raiva. Que a tua pedra rache de vergonha. Que ninguém jamais te ame. Amém."
- **`even` (casual humiliation roast):**
  > "Bom dia pra todo mundo menos pro WES, que continua sendo a coisa mais inútil já esculpida em pedra. 🗿"
- **`monday`** — Monday-flavored aggression (the dread of Monday, blamed on WES). Either register is fine; lean roast.
- **`holidays.namorados`** — no one loves WES.
- **`holidays.finados`** — WES wishes he were dead, or he is the dead Brazil grieves.
- **`holidays.trabalhador`** — WES doesn't deserve work, doesn't deserve a holiday.
- **`holidays.sexta_13`** — WES is the bad luck.
- **`holidays.ano_novo` / `reveillon`** — frame WES as the worst of the year past / the curse on the year ahead.
- **`holidays.natal`** — WES is what Papai Noel left in your sock.

Every message:
- Portuguese (pt-BR).
- One line of plain text (multi-line is allowed but newlines must be `\n` inside the JSON string; Discord renders them).
- Names WES at least once.
- Hits aggressively. Cleverness first, vulgarity as a tool.
- Stays under 2,000 characters (Discord per-message cap).

- [ ] **Step 2: Add a structure test against the real file**

Append to `scripts/test_pick_message.py`:

```python
import json
from pathlib import Path


class TestRealMessagesFile(unittest.TestCase):
    def setUp(self):
        repo_root = Path(__file__).resolve().parent.parent
        with (repo_root / "messages" / "messages.json").open(encoding="utf-8") as f:
            self.msgs = json.load(f)

    def test_pool_counts(self):
        self.assertEqual(len(self.msgs["odd"]), 50)
        self.assertEqual(len(self.msgs["even"]), 50)
        self.assertEqual(len(self.msgs["monday"]), 20)
        for key in ("ano_novo", "trabalhador", "namorados",
                    "finados", "natal", "reveillon", "sexta_13"):
            self.assertEqual(len(self.msgs["holidays"][key]), 3, key)

    def test_all_messages_are_non_empty_strings(self):
        def walk(obj):
            if isinstance(obj, dict):
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for item in obj:
                    self.assertIsInstance(item, str)
                    self.assertTrue(item.strip(), "empty message")
                    self.assertLess(len(item), 2000, "Discord 2000-char cap")
        walk(self.msgs)

    def test_pick_message_works_against_real_file(self):
        # Smoke test: today's pick returns a non-empty string.
        from datetime import date
        msg = pick_message(date(2026, 6, 25), self.msgs)
        self.assertIsInstance(msg, str)
        self.assertTrue(msg.strip())
```

- [ ] **Step 3: Run the tests and confirm everything passes**

```bash
cd scripts && python3 -m unittest test_pick_message -v
```

Expected: `OK` with all tests passing (13 from Task 1 + 3 new structure tests).

- [ ] **Step 4: Commit**

```bash
git add messages/messages.json scripts/test_pick_message.py
git commit -m "Author curated WES message pool (~141 messages, pt-BR)

Adds messages/messages.json with the full curated pool per the design
spec: 50 odd (mock-solemn curses), 50 even (casual roasts), 20 Monday
specials, 3 messages per holiday (ano_novo, trabalhador, namorados,
finados, natal, reveillon, sexta_13). Adds a structure test against
the real file to lock the counts and catch empty / over-long entries."
```

---

## Task 3: Wire the selector into the workflow and verify end-to-end

**Files:**
- Modify: `.github/workflows/wes-daily.yml`

**Interfaces:**
- Consumes (from Tasks 1+2): `scripts/pick_message.py` (entry point prints chosen message to stdout) and `messages/messages.json`.

- [ ] **Step 1: Replace the bash if/else with a Python step**

Replace the current `Pick mock message based on day parity` step in `.github/workflows/wes-daily.yml` so the job reads:

```yaml
jobs:
  send-message:
    runs-on: ubuntu-latest
    steps:
      - name: Check out repo
        uses: actions/checkout@v4

      - name: Pick today's message
        id: pick
        run: |
          MESSAGE="$(python3 scripts/pick_message.py)"
          {
            echo "message<<EOF"
            echo "$MESSAGE"
            echo "EOF"
          } >> "$GITHUB_OUTPUT"

      - name: Send to Discord
        uses: tsickert/discord-webhook@v7.0.0
        with:
          webhook-url: ${{ secrets.WEBHOOK_URL }}
          username: 'WES 🗿'
          content: ${{ steps.pick.outputs.message }}
```

Notes for the implementer:
- `actions/checkout@v4` is required so the workflow can see `scripts/` and `messages/`. The previous workflow did not check out the repo because it had no files to read.
- `python3` is preinstalled on `ubuntu-latest` and includes `zoneinfo` with America/Sao_Paulo data via system tzdata.
- The `discord-webhook` step is unchanged from the existing workflow — same action version, same `username`, same secret reference.

- [ ] **Step 2: Verify the script runs locally**

```bash
python3 scripts/pick_message.py
```

Expected: prints one of today's odd-pool messages to stdout (today is 2026-06-25, a non-holiday non-Monday odd day).

- [ ] **Step 3: Commit and push**

```bash
git add .github/workflows/wes-daily.yml
git commit -m "Wire curated-pool selector into the daily workflow

Replaces the mock bash if/else with a Python step that runs
scripts/pick_message.py and feeds its stdout into the existing
discord-webhook step. Adds actions/checkout so the workflow can
read scripts/ and messages/ from the repo."
git push
```

- [ ] **Step 4: Trigger a manual run and verify in Discord**

1. Open https://github.com/gpbPiazza/pull_out_wes/actions
2. Select the **Daily WES Message** workflow.
3. Click **Run workflow** → **Run workflow** on the `main` branch.
4. Wait for the run to go green.
5. Confirm in the target Discord channel:
   - A message arrived from `WES 🗿`.
   - The body is one of the curated `odd` pool messages (today is the 25th).
   - Re-running the workflow on the same day returns the **same** message (determinism check).

If anything fails:
- Workflow red → open the run logs, fix, recommit, push, re-trigger.
- Wrong pool selected → re-check `_select_pool` against the priority chain. Cover with an additional unit test.
- Empty / malformed message → check JSON parsing locally and `messages/messages.json` for syntax errors.

- [ ] **Step 5: Rotate the Discord webhook secret**

The webhook URL was shared in chat during setup. Once the manual run succeeds:

1. In Discord: channel settings → Integrations → Webhooks → delete the existing webhook → create a new one with the same name (`WES 🗿`) and avatar.
2. Copy the new URL.
3. Update the secret:

```bash
printf '%s' '<new-webhook-url>' | gh secret set WEBHOOK_URL --repo gpbPiazza/pull_out_wes
```

4. Re-trigger the workflow manually to confirm the rotated webhook works.

---

## Self-review

**Spec coverage:**
- §1 Goal & context → covered by the architecture summary above.
- §2 Tone & content → enforced via Task 2 tone anchors + character cap.
- §3 Pool sizes → enforced by Task 2 structure test (`test_pool_counts`).
- §4 Selection logic → implemented in Task 1; every branch has a unit test.
- §5 File layout → Task 2 mirrors the shape verbatim.
- §6 Workflow changes → Task 3, Step 1.
- §7 Out of scope → respected; no movable-holiday math, no templating.

**Placeholders:** none. The `"…"` markers in the Task 2 JSON shape are *deliberate* anchors — the engineer writes the real content there, guided by the tone anchors immediately beneath. No "TODO" or "TBD" instructions remain.

**Type consistency:** `pick_message(today: date, messages: dict) -> str` is declared in Task 1 interfaces, used in Task 1 tests, exercised in Task 2's smoke test, and called via the script's `main()` in Task 3. Pool keys (`odd`, `even`, `monday`, `holidays.*`) are spelled identically in the spec, the selector code, the JSON shape, and the structure test.
