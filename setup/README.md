# Setup — Garmin Connect MCP Extensions

> **Note:** After editing your `garmin_mcp.py`, restart the MCP server so the running process picks up the new tools (kill it via your client, or relaunch `uv run python garmin_mcp.py`).

This folder holds **reference code that gets installed into a different project** — the user's `garmin-connect-mcp` server. It's not executed by `outfit-ai-coach` directly; the `garmin-training` skill calls the MCP server, which calls these tools.

| File | Goes to | Purpose |
|------|---------|---------|
| `garmin-mcp-extensions.py` | `garmin-connect-mcp/garmin_mcp.py` | Adds five Garmin tools (training status, VO2 max, training readiness, HRV, sleep) the base server doesn't expose |
| `README.md` | (stays here) | Install instructions and project-side context |

## Why this exists

The base `garmin-connect-mcp` server exposes daily summaries, activities, body comp, and weigh-ins. The `garmin-training` skill in this project needs five additional tools — training status, VO2 max, training readiness, HRV, sleep. Rather than fork the server, paste these tool definitions into your local copy.

Without these extensions the skill still works in a degraded mode: Snapshot writes daily summary + weigh-in and notes which fields were missing. With them, the skill writes the full `health-snapshot.md` and `performance-stats.csv` rows.

## Prerequisites

You need a `garmin-connect-mcp` server already set up and registered with this Claude project. If you don't have it yet, follow that project's own README first (`uv sync`, `.env` credentials, client registration via `claude mcp add`). If Garmin already works in another Claude workspace of yours, the same server will work here.

## Install

1. **Bump the library** if it's pinned to an older version:
   ```bash
   cd <path-to>/garmin-connect-mcp
   uv add 'garminconnect>=0.2.20'
   ```

2. **Open `garmin_mcp.py`** in that project.

3. **Paste Section A** (input model classes) immediately after the existing `BodyCompInput` class. Strip the `# noqa: F821` markers — they're there because the helpers live in the host file, not the standalone extension file.

4. **Paste Section B** (the `@mcp.tool` functions and their `_parse_*` helpers) immediately before the `if __name__ == "__main__":` block at the bottom of the file. Strip the `# noqa: F821` markers here too.

   The new tools reuse the existing `_get_client()`, `_handle_error()`, `_validate_iso_date()`, `_format_seconds()`, `ResponseFormat`, and `_StrictModel` helpers — no new imports needed beyond what `garmin_mcp.py` already pulls in.

5. **Restart the MCP server** (kill it via your client, or `uv run python garmin_mcp.py` from a terminal for testing).

You should see five new tools listed by the client:
- `garmin_get_training_status`
- `garmin_get_max_metrics`
- `garmin_get_training_readiness`
- `garmin_get_hrv`
- `garmin_get_sleep`

## Smoke test

```bash
cd <path-to>/garmin-connect-mcp
uv run python -c "
import asyncio
from garmin_mcp import garmin_get_training_status, TrainingStatusInput
print(asyncio.run(garmin_get_training_status(TrainingStatusInput(target_date='2026-05-31', response_format='markdown'))))
"
```

Expect a "Training Status" block. If you see `AttributeError`, the `garminconnect` library version is too old — re-run the `uv add` in step 1.

## Verify from this project

In this project's Claude client:

> "training status"

Expected behavior (per `.claude/skills/garmin-training/SKILL.md`):
- Skill creates `fitness-data/` and `fitness-data/imports/` if missing.
- Pulls training status / VO2 max / readiness / daily summary / latest weigh-in.
- Writes `fitness-data/health-snapshot.md` and upserts today's row into `fitness-data/performance-stats.csv`.
- Returns a 2-line confirmation.

If the five new tools aren't registered yet, the skill falls back to daily summary + weigh-in only and notes the missing tools in `health-snapshot.md`.

## Related

- `.claude/skills/garmin-training/SKILL.md` — the in-project consumer of these tools.
- `.claude/agents/training-context/AGENT.md` — reads the CSVs that the skill writes.
- `schemas/training-context.yaml` — the structured output downstream skills consume.
