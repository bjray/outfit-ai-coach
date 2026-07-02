---
name: garmin-training
description: >
  Use this skill when the user says "garmin training status", "training stats",
  "performance stats", "VO2 max", "training effect", "training readiness",
  "fitness check", "pull my training data", "sync training data",
  "import garmin year", "import training csv", "pre-workout context", or
  "training context for today". Pulls Garmin Connect training/health data
  into the project's `fitness-data/` folder using a hybrid strategy: live
  MCP for recent state, CSV imports for historical aggregates (to avoid
  API throttling). This is the ingestion layer — the `training-context`
  agent reads the CSVs this skill writes.
argument-hint: [mode]
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Garmin Training — Ingestion & Persistence Layer

This skill is the **only** entry point for pulling Garmin Connect data into the project. It writes CSVs to `fitness-data/` that other parts of the system read.

- **`training-context` agent** reads these CSVs to assemble the workout-skill input. It does NOT call Garmin MCP directly anymore.
- **`workout-coach`** and individual workout skills consume `training_context`, not these CSVs directly.

The skill surfaces three classes of Garmin data:

1. **Key health stats** — daily summary (steps, RHR, intensity minutes, active kcal), body composition, HRV, sleep.
2. **Performance stats** — training status (productive / maintaining / detraining / peaking / etc.), per-activity training effect (aerobic + anaerobic), VO2 max, training readiness.
3. **Report data** — aggregate totals across a year or period: activity count, total distance, total activity time, total ascent, total calories, average HR / cadence / speed.

The first two come from live MCP. The third comes from user-exported CSV reports (Garmin Connect → Reports → Activities → Export CSV) — importing them dodges the API throttling you hit when trying to assemble multi-year history from per-activity calls.

---

## Arguments / Trigger words

The user's wording picks the mode:

| User says | Mode | What gets pulled |
|-----------|------|------------------|
| "training status", "fitness check", "what's my VO2 max" | **Snapshot** | Latest training status + VO2 max + readiness + today's daily summary + latest weigh-in |
| "sync training data", "pull last 14 days", "sync training" | **Rolling sync** | 14-day activities + daily summaries + performance snapshots, written to CSVs |
| "import garmin year", "import training csv", "import year.csv" | **CSV import** | Reads user-exported CSV from `fitness-data/imports/`, normalizes, upserts into `period-summary.csv` |
| "pre-workout context", "training context for today" | **Pre-workout** | Tight 5-line summary for downstream workout agents |
| Ambiguous trigger | Defaults to **Snapshot** | — |

Slash form: `/garmin-training [snapshot|sync|import|pre-workout]` if the user prefers explicit invocation.

---

## Refresh policy

**This skill never auto-fires.** Live MCP calls happen only when:

1. The user explicitly triggers one of the modes above.
2. `/profile-builder` runs the optional initial snapshot during fresh setup, after the user opts into Garmin.

Other consumers (`training-context`, `workout-coach`) read whatever CSVs already exist. If the data is stale, they note staleness in their output but do **not** call the skill on the user's behalf. Append-only on disk; minimize API traffic.

---

## Prerequisites

This skill depends on the Garmin Connect MCP server with **five extension tools** added. The extension file lives at `setup/garmin-mcp-extensions.py` with install instructions at `setup/README.md`.

Required tools (existing five from the base server):
- `garmin_get_daily_summary`
- `garmin_get_body_comp`
- `garmin_get_latest_weigh_in`
- `garmin_list_activities`
- `garmin_get_activity`

Required tools (the five added by `setup/garmin-mcp-extensions.py`):
- `garmin_get_training_status`
- `garmin_get_max_metrics`
- `garmin_get_training_readiness`
- `garmin_get_hrv`
- `garmin_get_sleep`

If the extension tools aren't installed, the skill degrades gracefully — Snapshot mode writes daily summary + weigh-in and notes which fields were unavailable. Pre-Workout mode falls back to RHR + activity load only.

Always request `response_format="json"` from MCP calls — the markdown variant is for human display, not parsing.

---

## Data Sources

| What you need | Source | Tool / file |
|---------------|--------|-------------|
| Steps, RHR, intensity min, active kcal (per day) | MCP | `garmin_get_daily_summary` |
| Body composition (range) | MCP | `garmin_get_body_comp` |
| Latest weigh-in | MCP | `garmin_get_latest_weigh_in` |
| Activity list (incl. per-activity training effect: `aerobic_te`, `anaerobic_te`) | MCP | `garmin_list_activities` |
| Activity detail | MCP | `garmin_get_activity` |
| Training status (rolling classification) | MCP (extension) | `garmin_get_training_status` |
| VO2 max (running + cycling) | MCP (extension) | `garmin_get_max_metrics` |
| Training readiness | MCP (extension) | `garmin_get_training_readiness` |
| HRV trend (optional) | MCP (extension) | `garmin_get_hrv` |
| Sleep stages (optional) | MCP (extension) | `garmin_get_sleep` |
| Aggregate yearly / period totals | **CSV import** | `fitness-data/imports/*.csv` → `fitness-data/period-summary.csv` |

---

## Storage

The skill creates and maintains the following layout under `garmin_data_path`:

```
fitness-data/
├── health-snapshot.md          ← latest Snapshot run (overwritten each time)
├── performance-stats.csv       ← rolling training status / VO2 / readiness time series
├── activity-effect.csv         ← per-activity training effect (last 30 days, upsert by activity_id)
├── period-summary.csv          ← imported yearly/period aggregate reports
├── daily-summary.csv           ← daily health stats (steps, RHR, kcal, intensity)
└── imports/                    ← drop user-exported Garmin Connect CSVs here
    ├── year.csv                ← example: yearly aggregate from Reports view
    └── archived/               ← processed imports preserved as audit trail
```

The folder is gitignored. Create it on first run if missing.

### Upsert rules (source of truth)

- `performance-stats.csv`, `daily-summary.csv`: keyed by `date`. Upsert; never duplicate a row.
- `activity-effect.csv`: keyed by `activity_id`. Upsert; preserve any manually-written `notes` column.
- `period-summary.csv`: keyed by `period` (`"2024"`, `"2025"`, `"lifetime"`, etc.). Last import wins for that period.
- All writes are **append-only** semantically — never delete rows Garmin no longer returns. Flag drift for the user instead.

---

## Configuration

Default: `<project-root>/fitness-data/`.

Override: add a `garmin_data_path` line to project CLAUDE.md or to the active profile (`profiles/<name>.yaml` → `garmin_data_path`). Useful if the user already collects Garmin data in another project (e.g., a nutrition workspace) and wants both contexts to share storage.

When this skill resolves the path:
1. Check the active profile for `garmin_data_path`.
2. Else check project CLAUDE.md for `garmin_data_path:`.
3. Else default to `./fitness-data/`.

---

## Schemas

### `daily-summary.csv`
```
date,day,steps,resting_hr,intensity_min_mod,intensity_min_vig,active_kcal,bmr_kcal,sleep_total_min,sleep_deep_min,sleep_light_min,sleep_rem_min,sleep_awake_min,sleep_score,sleep_quality,sleep_score_feedback,last_synced
```
- Sleep columns come from `garmin_get_sleep`. `sleep_quality` is Garmin's `EXCELLENT|GOOD|FAIR|POOR` qualifier. `sleep_score_feedback` is Garmin's coaching slug, e.g. `POSITIVE_LONG_AND_CALM`.

### `performance-stats.csv`
```
date,training_status,training_status_detail,vo2_max_running,vo2_max_cycling,fitness_age,training_readiness,readiness_level,acute_training_load,chronic_training_load,acute_load_optimal_min,acute_load_optimal_max,acwr,acwr_status,load_focus_low_aerobic,load_focus_high_aerobic,load_focus_anaerobic,load_focus_feedback,hrv_last_night_avg,hrv_weekly_avg,hrv_status,hrv_feedback_phrase,last_synced
```
- `training_status` is the top-level Garmin classification (`PRODUCTIVE`, `MAINTAINING`, `DETRAINING`, `RECOVERY`, `UNPRODUCTIVE`, `PEAKING`, `OVERREACHING`). Derived from `trainingStatusFeedbackPhrase` (more reliable than the numeric code, which has drifted across firmware versions).
- `training_status_detail` is the full Garmin phrase slug (e.g. `PRODUCTIVE_1`).
- `acute_training_load` / `chronic_training_load` are Garmin's 7-day and 28-day rolling loads — the values that drive the "Acute Training Load" chart in Garmin Connect's UI.
- `acute_load_optimal_min` / `acute_load_optimal_max` bound Garmin's "optimal range" band for today's chronic load. Acute load inside this band = sustainable; outside = under- or over-loading.
- `acwr` / `acwr_status` come from Garmin's `dailyAcuteChronicWorkloadRatio` and `acwrStatus` (`OPTIMAL`, `LOW`, `HIGH`, etc.). Garmin computes these — do **not** recompute locally.
- `load_focus_low_aerobic` / `_high_aerobic` / `_anaerobic` are the last-4-weeks monthly loads by intensity (drives the "Exercise Load" stacked-bar chart). `load_focus_feedback` is Garmin's coaching slug (e.g. `AEROBIC_HIGH_SHORTAGE`).
- `hrv_last_night_avg` is the overnight mean; `hrv_weekly_avg` is the 7-day mean. `hrv_status` is `BALANCED|UNBALANCED|LOW|POOR`. `hrv_feedback_phrase` is Garmin's slug (e.g. `HRV_BALANCED_2`).

### `activity-effect.csv`
```
activity_id,date,start_time_local,activity_type,activity_name,duration_min,distance_m,aerobic_te,anaerobic_te,training_effect_label,primary_benefit,recovery_time_hr,last_synced,notes
```

### `period-summary.csv`
```
period,activities,total_distance_mi,total_time_h,total_routes,total_calories,total_ascent_ft,avg_speed_mph,avg_hr_bpm,avg_run_cadence_spm,avg_bike_cadence_rpm,source_file,imported_at
```

These schemas are the contract `training-context` reads against. See `schemas/training-context.yaml` for how these fields map into the structured `training_context` object that downstream skills consume.

---

# Workflow A — Snapshot

Trigger words: "training status", "fitness check", "VO2 max", etc.

## Step A1 — Determine target date

Default: today (local time).

## Step A2 — Pull from MCP

Run these calls in order. If any single one errors with 429 or an authentication error, **stop the snapshot, surface the error, and offer CSV-import fallback** instead of partial-writing.

```
garmin_get_training_status(target_date=today, response_format="json")
garmin_get_max_metrics(target_date=today, response_format="json")
garmin_get_training_readiness(target_date=today, response_format="json")
garmin_get_daily_summary(target_date=today, response_format="json")
garmin_get_latest_weigh_in(lookback_days=14, response_format="json")
```

Optional (only on explicit request):
```
garmin_get_hrv(target_date=today, response_format="json")
garmin_get_sleep(target_date=today, response_format="json")
```

## Step A3 — Write `health-snapshot.md`

Overwrite the file. Schema:

```markdown
# Health Snapshot — YYYY-MM-DD HH:MM (local)

## Performance
- **Training status**: PRODUCTIVE (`PRODUCTIVE_1`)
- **VO2 max (running)**: 47 · **VO2 max (cycling)**: 51
- **Training readiness**: 78 / 100 — *Moderate*
- **Fitness age**: 38

## Load
- **Acute load (7d)**: 462 (optimal 267–501)
- **Chronic load (28d)**: 334
- **ACWR**: 1.3 — *OPTIMAL*
- **Load focus (last 4 weeks)**: low-aerobic 1226 / high-aerobic 110 / anaerobic 0 — `AEROBIC_HIGH_SHORTAGE`

## Recovery
- **HRV last night**: 47 ms (balanced band 40–51) — BALANCED (`HRV_BALANCED_2`)
- **HRV 7-day avg**: 48 ms
- **Sleep last night**: 7h 53m — score 73 *FAIR* (`POSITIVE_LONG_AND_CALM`)
  - Deep 57m (12%) · Light 5h 39m (72%) · REM 1h 17m (16%) · Awake 40m (3 awakenings)
- **Resting HR (today)**: 51 bpm

## Body
- **Weight** (Garmin, YYYY-MM-DD): 178.6 lbs · BF 24.0%

## Activity (today so far)
- **Steps**: 6,420 · **Active kcal**: 312 · **Intensity min**: 12 mod / 4 vig
```

Skip lines whose source returned null. Don't fabricate `"unknown"` — just omit the row.

## Step A4 — Upsert `performance-stats.csv`

Add (or replace) today's row from the fetched data.

## Step A5 — Confirm

Show a 2-line summary in chat:
> *Snapshot saved to `fitness-data/health-snapshot.md`. Training status: PRODUCTIVE · Readiness 78 · VO2max 47R/51C. Anything missing was unavailable from Garmin at fetch time.*

---

# Workflow B — Rolling Sync (14 days)

Trigger words: "sync training data", "pull last 14 days", "sync training".

## Step B1 — Pull activities

```
garmin_list_activities(start=0, limit=50, response_format="json")
```
Filter to activities with `startTimeLocal` in the last 14 days. Paginate (`start=50, limit=50`, etc.) if exactly 50 are returned.

## Step B2 — Upsert `activity-effect.csv`

Same upsert-by-`activity_id` pattern. Fields per activity:
- `activity_id`, `date`, `start_time_local`, `activity_type`, `activity_name`
- `duration_min` (from `duration` seconds / 60, 1 decimal)
- `distance_m` (as-is)
- `aerobic_te`, `anaerobic_te` (Garmin's per-activity training effect, 1 decimal)
- `training_effect_label`, `primary_benefit` (Garmin's text labels: "Tempo", "Recovery", "Threshold", "VO2Max", etc.)
- `recovery_time_hr` if Garmin returns it
- `last_synced` (ISO timestamp)
- `notes` preserved

## Step B3 — Pull daily summaries for affected dates

For each unique date in the 14-day window:
```
garmin_get_daily_summary(target_date=<date>, response_format="json")
```
Upsert into `daily-summary.csv`.

**Throttle guard:** sleep 1 second between summary calls. If a 429 fires mid-loop, write what's been collected so far, surface the error with the last-synced date, and stop. Do not retry within the same skill run.

## Step B4 — Pull performance snapshots (yesterday + today)

Two rows: yesterday and today. Training status changes slowly and these endpoints are expensive. If the user explicitly asks for "full performance backfill", expand to all 14 dates with extra throttle spacing (3 sec).

## Step B5 — (deprecated) Local ACWR computation

Removed. Garmin returns ACWR directly via `acuteTrainingLoadDTO.dailyAcuteChronicWorkloadRatio` in the `garmin_get_training_status` payload, along with a categorical `acwrStatus` (`OPTIMAL` / `LOW` / `HIGH`). Both land in `performance-stats.csv` during Step B4. Do **not** recompute from `activity-effect.csv` — Garmin's value uses a fuller training-load model that accounts for intensity bands the per-activity training effect doesn't capture.

## Step B6 — Confirm

```
Rolling sync complete.
- Activities: 7 new, 1 refreshed, 0 deleted
- Daily summaries: 14 dates upserted
- Performance: 2 dates upserted (today, yesterday)
- ACWR (Garmin): 1.3 — OPTIMAL
- Load focus (4w): low-aerobic 1226 / high-aerobic 110 / anaerobic 0 — AEROBIC_HIGH_SHORTAGE
```

---

# Workflow C — CSV Import (historical aggregates)

Trigger words: "import garmin year", "import training csv", "import year.csv", "import garmin export".

This path exists because Garmin Connect's Reports view exports clean historical roll-ups directly. Importing them avoids API throttling and gives downstream agents multi-year context the live API would take hundreds of calls (and many rate-limit pauses) to assemble.

## Step C1 — Discover import file(s)

List `fitness-data/imports/*.csv`. If empty:

> *Drop a Garmin Connect Reports export (e.g., `year.csv`) into `fitness-data/imports/` and re-run. Garmin Connect → Reports → Activities → Export CSV is the standard path.*

If multiple files are present, ask which to import (or import all if the user said "import all").

## Step C2 — Detect schema

Garmin Connect Reports CSVs use this header (subject to mild variation by locale / units):

```
"Time Period","Activities","Total Distance","Total Activity Time",
"Total Routes","Activity Calories","Total Ascent","Average Speed",
"Average Heart Rate","Average Run Cadence","Average Bike Cadence"
```

If the actual header doesn't match, surface a parse error showing the found vs. expected header. **Don't guess.**

## Step C3 — Normalize rows

For each row (skip blanks; capture the `"Summary"` row into a `period="lifetime"` row):

| Source column | Stored column | Transform |
|---------------|---------------|-----------|
| Time Period | `period` | strip quotes; keep as `"2024"`, `"2025"`, `"lifetime"` |
| Activities | `activities` | int |
| Total Distance | `total_distance_mi` | strip ` mi`; float (`--` → null) |
| Total Activity Time | `total_time_h` | parse `HH:MM:SS` → hours float (1 decimal); else null |
| Total Routes | `total_routes` | int; `--` → null |
| Activity Calories | `total_calories` | strip commas; int |
| Total Ascent | `total_ascent_ft` | strip ` ft` and commas; int; `--` → null |
| Average Speed | `avg_speed_mph` | strip ` mph`; float; `--` → null |
| Average Heart Rate | `avg_hr_bpm` | strip ` bpm`; int; `--` → null |
| Average Run Cadence | `avg_run_cadence_spm` | strip ` spm`; int; `--` → null |
| Average Bike Cadence | `avg_bike_cadence_rpm` | strip ` rpm`; int; `--` → null |

Add columns:
- `source_file` = the relative filename (e.g., `imports/year.csv`)
- `imported_at` = ISO timestamp

Default to imperial. If the user prefers metric, ask once and convert before writing.

## Step C4 — Upsert into `period-summary.csv`

Key by `period`. If a row exists for the same period, replace it and announce the swap:

> *Replaced existing row for `2025` (last imported YYYY-MM-DD). Old: activities=312, distance=389.10 mi. New: activities=312, distance=389.10 mi.*

This lets the user re-import after Garmin reclassifies past activities without creating duplicates.

## Step C5 — Move imported file

Move processed CSVs from `fitness-data/imports/` to `fitness-data/imports/archived/YYYY-MM-DD-<original-name>.csv`. Don't delete — the original file is the only ground-truth audit trail.

## Step C6 — Confirm

```
CSV import complete.
- Source: fitness-data/imports/year.csv
- 17 period rows imported (2008 — 2026 + lifetime)
- Lifetime totals: 2,112 activities · 12,635.6 mi · 1,283,262 kcal · 811,098 ft ascent
- File archived to imports/archived/2026-05-31-year.csv
```

---

# Workflow D — Pre-Workout Context

Trigger words: "pre-workout context", "training context for today", "readiness check before workout".

This is the **agent-to-agent integration point**. Goal: a 5–8 line block downstream agents can parse in one chunk. (The full structured `training_context` object — produced by the `training-context` agent — is a different, richer contract.)

## Step D1 — Read fresh from snapshot if available

If `fitness-data/health-snapshot.md` is < 8 hours old, read it directly. Otherwise tell the user the snapshot is stale and suggest running "training status" — **do not auto-fetch**. Append-only policy: live calls are user-triggered.

## Step D2 — Read recent activity load

From `activity-effect.csv`, pull the last 3 sessions (by date desc). For each, capture:
- date
- `activity_type`
- `aerobic_te` + `anaerobic_te`
- `recovery_time_hr` (if Garmin returned it)

## Step D3 — Compute simple flags

- **High load yesterday?** `aerobic_te + anaerobic_te ≥ 4.0` on yesterday's session.
- **Insufficient recovery?** sum of `recovery_time_hr` from sessions in the last 48h > 48.
- **RHR creep?** today's RHR > 4 bpm above the 28-day avg.
- **Low readiness?** `training_readiness < 50`.

## Step D4 — Output

Hand back this exact-shape block:

```markdown
**Training context — YYYY-MM-DD**
- Status: PRODUCTIVE · Readiness 78/100 · VO2max 47R
- RHR: 51 bpm (28d avg 52) · Weight: 178.6 lbs
- Last 3: 2026-05-30 cycling TE 3.2/0.5 · 2026-05-29 strength TE 1.8/2.4 · 2026-05-28 walking TE 1.5/0.0
- Flags: none
- Recommended emphasis: maintain — green across recovery indicators
```

If flags fire:
```
- Flags: high_load_yesterday, low_readiness
- Recommended emphasis: recovery / aerobic Z2 only — readiness 38 + yesterday's TE 4.2
```

**This block is the contract.** Keep the shape stable — downstream agents parse it as-is.

---

# Error Handling

| Failure | Behavior |
|---------|----------|
| MCP tool returns 429 (rate limit) | Stop the workflow. Surface the error. Suggest CSV import fallback for the affected window. Don't auto-retry. |
| MCP tool returns null for a metric | Omit the metric from `health-snapshot.md`; leave the CSV cell blank. Don't write `"unknown"`. |
| `imports/` is empty when Workflow C runs | Tell the user where to drop the file. Stop. |
| CSV import header doesn't match expected schema | Surface found vs. expected header. Do not partial-import. |
| `fitness-data/` does not exist | Create it (and `imports/`) on first run. Tell the user the folder was created. |
| Extension tools not registered (e.g., `garmin_get_training_status`) | Snapshot mode degrades: write what's available, add a footer line in `health-snapshot.md` noting *"training status / VO2 / readiness unavailable — install extensions per `setup/garmin-mcp-extensions.py`."* Pre-workout context falls back to RHR + activity load. |

---

# What This Skill Does NOT Do

- Doesn't prescribe workouts. That's the workout-building skills' job. This skill only ingests context.
- Doesn't push data back to Garmin.
- Doesn't get called automatically by other agents. User-triggered only (plus the one-time profile-builder setup hook).
- Doesn't auto-delete rows from local CSVs when Garmin no longer returns them. Flag for user review; default-keep.
- Doesn't refresh more than once per hour on the same Snapshot run unless the user passes `force_refresh=true`.

---

# Related

- `setup/garmin-mcp-extensions.py` — Python tools to add to the Garmin Connect MCP server before this skill can run with full data.
- `setup/README.md` — install steps for those extensions.
- `.claude/agents/training-context/AGENT.md` — the downstream analysis agent that reads the CSVs this skill writes.
- `schemas/training-context.yaml` — the structured output `training-context` produces from these CSVs.
- `.claude/skills/profile-builder/SKILL.md` — handles the optional initial snapshot during fresh profile setup.
