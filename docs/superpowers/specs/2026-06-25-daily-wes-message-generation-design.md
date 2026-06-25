# Daily WES Message Generation — Design

**Date:** 2026-06-25
**Status:** Approved (pending spec review)
**Replaces:** the two mock messages currently hard-coded in `.github/workflows/wes-daily.yml`.

## 1. Goal & context

The repo posts a daily message to a Discord channel via webhook (already working — see `README.md` and the existing GitHub Action). This spec defines how the *content* of those messages is generated from a curated pool.

**Theological frame (load-bearing for tone):** WES is the vessel that absorbs everything that is worst. The messages are *aggression dumped onto WES* — insults, humiliations, mock-curses. By having all the negativity directed at him, he absorbs it and the rest of us are blessed. WES is the punching bag of the ritual.

## 2. Tone & content

- **Language:** Portuguese (pt-BR).
- **Direction:** Always aggressive toward WES. He is everything worst. Messages humiliate, insult, mock.
- **Content limits:** None — full Brazilian profanity is allowed (porra, caralho, merda, cu, etc.). Slurs and any other content are not restricted by policy.
- **Craft rule:** Lean on cleverness. Vulgarity is a tool, not a crutch. The best messages are sharp first and crude second.
- **Two registers, alternating by day-of-month parity:**
  - **Odd day → mock-solemn ritualistic curse.** Formal, prayer-shaped, but every line invokes WES's worthlessness, stench, failure. Humor comes from how seriously it takes itself.
    > *Example:* "Ó WES, vaso podre, recebe hoje a minha raiva. Que a tua pedra rache de vergonha. Que ninguém jamais te ame. Amém."
  - **Even day → casual humiliation roast.** Boteco-style direct insults, conversational, more obviously jokey.
    > *Example:* "Bom dia pra todo mundo menos pro WES, que continua sendo a coisa mais inútil já esculpida em pedra. 🗿"

## 3. Message categories & pool sizes

| Category       | Size | Notes |
|----------------|-----:|-------|
| `odd`          |  50  | Mock-solemn ritualistic curses (used on odd days when no higher-priority signal fires). |
| `even`         |  50  | Casual humiliation roasts (used on even days when no higher-priority signal fires). |
| `monday`       |  20  | Aggressive Monday-morning specials. Tone can lean either register. |
| `holidays.ano_novo`     | 3 | 1 Jan |
| `holidays.trabalhador`  | 3 | 1 May |
| `holidays.namorados`    | 3 | 12 Jun — comedic gold (no one loves WES) |
| `holidays.finados`      | 3 | 2 Nov — WES wishes he were dead |
| `holidays.natal`        | 3 | 25 Dec |
| `holidays.reveillon`    | 3 | 31 Dec |
| `holidays.sexta_13`     | 3 | weekday=Friday AND day=13 |
| **Total**      | **~141** | |

Pool sizes were chosen so that, given typical category frequency, a given message reappears no sooner than roughly every 3.5 months for the daily parity pools and roughly every 5 months for Mondays.

## 4. Selection logic

Runs inside the workflow once per scheduled fire. Pseudocode:

```
today = current date in America/Sao_Paulo
mmdd  = today.strftime("%m%d")
weekday = today.weekday()  # 0=Mon … 6=Sun
day = today.day

# Priority chain: Holiday > Monday > parity
if mmdd in FIXED_HOLIDAY_MAP:
    pool = holidays[FIXED_HOLIDAY_MAP[mmdd]]
elif day == 13 and weekday == 4:  # Friday the 13th
    pool = holidays["sexta_13"]
elif weekday == 0:  # Monday
    pool = monday
elif day % 2 == 1:
    pool = odd
else:
    pool = even

# Within pool: sequential rotation by epoch day.
epoch_day = (today - date(1970, 1, 1)).days
message = pool[epoch_day % len(pool)]
```

`FIXED_HOLIDAY_MAP`:
- `0101` → `ano_novo`
- `0501` → `trabalhador`
- `0612` → `namorados`
- `1102` → `finados`
- `1225` → `natal`
- `1231` → `reveillon`

**Why sequential rotation by epoch day** (rather than random or hashed): predictable (same date → same message → testable), and guarantees every message in a pool is seen before any of them repeats. Adding new messages shifts the rotation, which is acceptable — variety improves.

## 5. File layout

A single data file at `messages/messages.json`. Pure data, no logic. Shape:

```json
{
  "holidays": {
    "ano_novo":    ["...", "...", "..."],
    "trabalhador": ["...", "...", "..."],
    "namorados":   ["...", "...", "..."],
    "finados":     ["...", "...", "..."],
    "natal":       ["...", "...", "..."],
    "reveillon":   ["...", "...", "..."],
    "sexta_13":    ["...", "...", "..."]
  },
  "monday": ["...", "..."],
  "odd":    ["...", "..."],
  "even":   ["...", "..."]
}
```

Splitting into per-category files is rejected: at ~141 messages the single file stays readable, and per-file splitting adds workflow complexity (multiple reads + concatenation) without paying back in maintenance.

## 6. Workflow changes

The existing `.github/workflows/wes-daily.yml` keeps:
- the `schedule` trigger (cron `0 12 * * *`),
- the `workflow_dispatch` trigger,
- the `tsickert/discord-webhook` step with `username: 'WES 🗿'`.

The current bash if/else step (`Pick mock message based on day parity`) is **replaced** with a single Python step that:
1. Reads `messages/messages.json`.
2. Computes today's date in `America/Sao_Paulo`.
3. Walks the priority chain in §4 to pick a pool.
4. Indexes by `epoch_day % len(pool)`.
5. Emits the chosen string as a step output via `GITHUB_OUTPUT`.

Python rationale (over shell + `jq`): JSON parsing, timezone-aware date math, and the priority chain read cleanly in stdlib Python (`json`, `datetime`, `zoneinfo`). The shell version would need `jq` plus careful escaping and is harder to verify by reading.

The `discord-webhook` step is unchanged — it consumes `steps.pick.outputs.message` exactly as today.

## 7. Out of scope (v1)

- **Movable holidays** (Carnaval, Sexta-feira Santa, Corpus Christi). Adding any of these requires an Easter computation; defer to a follow-up.
- **Year-aware variants** (messages that name the current year, e.g. "boas-vindas a 2027"). Possible but introduces templating; defer.
- **Per-message metadata** (author, theme tags, weight). YAGNI.
- **Admin tooling for editing messages.** Direct file edits + PR are sufficient.
- **Telemetry / delivery success tracking.** GitHub Actions UI is enough.

## 8. Open questions

None at design freeze. Spec is approved; implementation plan is the next step.
