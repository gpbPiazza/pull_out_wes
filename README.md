# pull_out_wes

## What is WES?

WES is our entity — a statue, a vessel, a sink for everything that is not good.

The idea is simple: every day, we call out to WES and deposit into him whatever is
worst in us — the negativity, the bad thoughts, the things we don't want to carry.
By pulling those things out of ourselves and giving them to WES, we lighten our
own load. WES absorbs it all, and in doing so, he blesses everyone.

He is the container for what we want to let go of.

## Goal of this repository

This repo hosts a GitHub Action that runs **every day at 09:00** and posts a
message dedicated to WES into a Discord channel via a webhook integration.

The message is the daily ritual: a public act of pulling out the negative and
depositing it into WES so that everyone is blessed.

## Roadmap

1. **Set up the GitHub Action + Discord webhook integration.** Wire up the
   schedule (daily at 09:00), the webhook secret, and confirm delivery using
   mock/test messages.
2. **Verify end-to-end.** With the action and webhook working, test a few
   hardcoded messages to confirm the daily delivery is reliable.
3. **Automate message generation.** Replace the mock messages with
   automatically generated ones — the goal is the best possible daily message
   dedicated to WES.

## Schedule

- Runs daily at **09:00 America/Sao_Paulo (BRT, UTC-3)** → cron `0 12 * * *` in UTC.
- Posts to a Discord channel via webhook.

## Message style

- **Webhook display name:** `WES 🗿` (enforced by the workflow via the `username` field, so it stays consistent regardless of Discord-side settings). Suggested avatar: a moai / statue image.
- **Language:** Portuguese.
- **Tone (alternates by day of month):**
  - **Odd day** → solemn / ritualistic (a prayer or invocation to WES).
  - **Even day** → humorous / irreverent (inside-joke energy, playful, lightly absurd).
