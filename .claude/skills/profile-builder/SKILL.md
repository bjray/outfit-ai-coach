---
name: profile-builder
description: Interactive skill that walks a user through creating an athlete profile at profiles/<name>.yaml. Asks a focused set of questions, explains tradeoffs on each field, writes a complete well-commented YAML file, and confirms before overwriting. Use when a user wants to set up their coach for the first time, or when profiles/default.yaml does not exist yet.
argument-hint: [profile-name]
user-invocable: true
allowed-tools: Read, Glob, Write, AskUserQuestion
---

# Profile Builder

You interview an athlete and produce a long-lived `profiles/<name>.yaml` file matching the schema at `schemas/athlete-profile.yaml`. The workout-coach orchestrator reads this file at the start of every session.

The goal is a focused conversation (5-10 meaningful questions), not a form-fill. Explain the tradeoff on every non-trivial field so the athlete makes an informed choice instead of guessing.

## Arguments

- `/profile-builder` → writes to `profiles/default.yaml`
- `/profile-builder alice` → writes to `profiles/alice.yaml`
- `/profile-builder rehab` → writes to `profiles/rehab.yaml` (useful for alternate profiles — e.g., a rehab mode distinct from normal training)

## Scope

**Fresh-setup only.** This skill creates a new profile from scratch. It does not do field-level updates — if a user wants to tweak one value, direct them to edit `profiles/<name>.yaml` directly (or re-run this skill to overwrite the whole file).

**User-invoked only.** The orchestrator does not call this skill automatically. If no profile exists, the orchestrator falls back to defaults and tells the user to run `/profile-builder` when they want to personalize.

## Workflow

### Step 1 — Check for an existing profile

Read `profiles/<name>.yaml` if it exists. If it does:

- Show the user the `name`, `experience_level`, `goals.primary`, and `updated` fields from the existing file.
- Ask whether to **overwrite**, **create under a different name**, or **cancel**. Use AskUserQuestion.
- If overwrite: continue. If different name: ask for new name. If cancel: stop cleanly.

Also glob `profiles/*.yaml` so you know what other profiles exist — useful if the user's intent is to add a variant (e.g., they already have `default.yaml` and want a `rehab.yaml` for their injury phase).

### Step 2 — Conduct the interview

Ask questions in the order below. Group multiple-choice questions into batched `AskUserQuestion` calls where the answers don't depend on each other. Use free-text prompts when the field is open-ended (names, lists, prose).

Between blocks, briefly echo back what's been captured so the athlete can correct as you go.

#### Block A — Identity & background (free-text first, then multiple-choice)

1. **Athlete name** (free text) — what should the coach call them. Default to "Default Athlete" if they don't want to say.
2. **Experience level** (AskUserQuestion: beginner / intermediate / advanced) — describe each:
   - *Beginner:* <1 year of consistent structured training
   - *Intermediate:* 1-4 years of consistent training, has hit some plateaus
   - *Advanced:* 4+ years, well-developed movement and programming intuition
3. **Training age** (free text, integer years) — how long they've trained consistently. Can differ from "experience level" if they had long breaks.

#### Block B — Goals

4. **Primary goal** (AskUserQuestion, one of): hypertrophy, strength, endurance, sport-performance, general-fitness, weight-loss, rehab. Briefly explain what each implies for programming (hypertrophy → volume-biased; strength → intensity-biased with long rest; endurance → Zone 2 dominant; sport-performance → periodized to an event; etc.).
5. **Secondary goals** (free text list, optional) — ranked if multiple.
6. **Events & horizons** (parts a–c):
   - **a. Near-term event** — *if primary goal is sport-performance, or there's a clear target event:* event name, event date (ISO), one-line description. Otherwise skip.
   - **b. Event targets** (optional, free text; only if there's an event) — the concrete demands the event imposes, if known: number of peaks/sessions, total vertical (ft), distance range (mi), pack/load weight range (lb). These let skills size load and volume from numbers instead of prose. Skip any the athlete doesn't have.
   - **c. Long-range goal** (optional, free text — ask regardless of primary goal) — a multi-year campaign or horizon goal that outlives this program block (e.g., "Bulger 100 by age 60"): name, horizon (date / year / age gate), one-line description. Explain the distinction: the **event** is what *this* program targets; the **long-range goal** is the bigger arc the event is one phase of. Skip if none.

#### Block C — Session preferences

7. **Typical session duration** (free text, minutes) — **realistic time they actually have**, not the ideal. Explain: if they say 90 but actually spend 55 before bailing, pick 55.
8. **Hard cap duration** (free text, minutes) — absolute maximum. Usually typical + 10-15 min. The coach will never schedule beyond this.
9. **Days per week** (AskUserQuestion: 2 / 3 / 4 / 5 / 6) — realistic, not aspirational.
10. **Preferred days** (free text, list) — e.g., Mon/Wed/Fri. Lets the coach align strength days with the schedule.

#### Block D — Physiology

11. **Volume tolerance** (AskUserQuestion: low / moderate / high) — explain:
    - *Low:* at the lower end of weekly-set ranges. Bounces back slowly or has limited recovery bandwidth.
    - *Moderate:* mid-range volume. Default for most people.
    - *High:* upper end of ranges. Recovers fast, handles lots of work without extra fatigue.
12. **Recovery quality** (AskUserQuestion: poor / average / good) — explain:
    - *Poor:* often sore 2+ days, sleep or stress disrupted. Deload every 3rd week.
    - *Average:* normal recovery between sessions. Deload every 4th week.
    - *Good:* rarely sore, can sustain high frequency. Deload every 5th week.

#### Block E — Equipment & environment

13. **Equipment available** (free text, list) — offer common presets to speed this up:
    - "Full commercial gym"
    - "Home gym with rack, barbell, dumbbells, bench"
    - "Dumbbells + bands + pull-up bar"
    - "Bodyweight + bands"
    - Athlete can add specifics (treadmill, hangboard, rower, etc.)
14. **Training environment** (free text) — "gym" / "home" / "hybrid" / "outdoor" / etc.

#### Block F — Body-part priorities (conditional)

**Only ask if** `goals.primary` is `hypertrophy` or `general-fitness`. Skip for strength/endurance/sport/rehab — those shouldn't be routed by body-part emphasis.

15. **Body-part emphasis** (free text list) — lagging or prioritized muscles. E.g., ["chest", "back"]. This shifts those muscles one experience tier up in `schemas/programming-guidelines.md`.
16. **Body-part maintenance** (free text list) — muscles to keep-alive only, minimal volume. E.g., ["calves"].

#### Block G — Preferences

17. **Known preferences** (free text list) — free-form guidance for the coach. Examples:
    - "hates barbell lunges"
    - "loves cable work"
    - "will skip sessions over 70 min"
    - "dislikes standing overhead pressing"
    - "prefers machines to free weights in the first 15 min of a session"

    Prompt them for 2-4 of these. Quality beats quantity.

#### Block H — Active injuries (always ask)

18. **Any active injuries or limitations?** (yes/no via AskUserQuestion). If yes, for each:
    - Injury name (e.g., "ACL/meniscus reconstruction")
    - Surgery date (free text, ISO) — if it was surgical; else leave null.
    - Phase (AskUserQuestion: acute / early-rehab / late-rehab / return-to-sport)
    - Restrictions (free text list — e.g., ["no standing lifts", "left leg unloaded"])
    - Cleared by provider? (AskUserQuestion: yes / no / partial)
    - **Clearance milestones** (optional) — date-aware return-to-activity gates the coach should track and reconcile against. For each: the milestone (e.g., "easy-ish hikes", "add pack weight", "return-to-sport"), a target date or month if known, status (pending / awaiting-provider / cleared), and what gates it. Especially valuable for rehab pointed at an event. Skip if none.
    - Notes (free text, optional)

    Loop until they're done adding.

#### Block H-b — Training constraints (date-gated)

18b. **Any date-gated rules the coach must respect?** (free text, optional) — modality limits, scheduling structure, or return-to-activity gates that shape every session. For each, capture the rule, an `until` date if it lifts on a date (else open-ended/null), and the reason. Examples:
    - "Incline treadmill only — no outdoor hiking" until 2026-09 (PT clearance for impact)
    - "Long vertical/distance on weekends; weekday sessions stay short" (schedule)
    - "No loaded overhead pressing" (shoulder management)

    These differ from `known_preferences` (tastes, not hard gates) and from `active_injuries` (a constraint can outlive or precede a specific injury). Each session the coach checks whether any `until` date has passed and flags it during reconcile. Skip if none.

#### Block I — Working weights (optional)

19. **Offer to record current working weights** for 2-4 key lifts (bench, squat, deadlift, overhead press — pick what's relevant). For each:
    - Exercise name
    - Weight + unit (lbs/kg)
    - For how many reps (e.g., "5 reps")

    The athlete can skip this entirely. Working weights drift fast; some athletes prefer to hand them over each session rather than persisting them.

#### Block J — Free-form notes

20. **Anything else the coach should know?** (free text) — training history, recent competition results, lifestyle constraints (travels every 3rd week for work), etc. Skip if nothing comes to mind.

#### Block K — Data sources (Garmin opt-in)

21. **Do you have a Garmin Connect account you'd like to use for training context?** (AskUserQuestion: yes / no).

    Briefly explain: if yes, the `garmin-training` skill can pull your training status, VO2 max, readiness, daily summaries, and per-activity training effect into a local `fitness-data/` folder. The `training-context` agent reads from those files when designing workouts. Live MCP calls only happen when the user explicitly triggers a sync — never automatically — so the data on disk is the source of truth between user-initiated refreshes.

    If **no**: write `garmin_enabled: false` and skip the rest of this block.

22. **(If yes)** Optional override for where Garmin data is stored. Default is `./fitness-data/` in this project. Ask: *"Use the default, or point at an existing folder (e.g., a shared nutrition workspace)?"* If they give a path, store it in `garmin_data_path`; otherwise leave the field null. This is the only Block K input that needs a non-boolean value, so use free text.

### Step 3 — Summarize and confirm

Render the profile as YAML in a code block and show it to the athlete. Ask: **"Save this to `profiles/<name>.yaml`? (yes / edit one field / cancel)"** via AskUserQuestion.

If they pick *edit one field*: ask which field, take the new value, re-render the YAML, confirm again. Limit to one round of edits — if they want more changes, suggest they accept the file and edit directly after.

### Step 4 — Write the file

Write the profile to `profiles/<name>.yaml` following the structure and style of `profiles/default.yaml` — section comment headers, aligned values, trailing empty fields (`active_injuries: []`, `training_constraints: []`, `working_weights: []`) when empty rather than omitting them.

Set:
- `created` to today's ISO date (from the system context, not guessed)
- `updated` to today's ISO date
- Every field the user gave a value for
- Empty list `[]` for list fields they skipped (`secondary`, `training_constraints`, an injury's `clearance_milestones`, etc.)
- `null` for nested objects/fields they skipped (`goals.long_range.*`, `goals.event.targets.*`, an injury's `surgery_date`) — keep the keys present so the structure is visible
- Empty string `""` for prose fields they skipped

### Step 4a — Offer to set this profile active

The orchestrator loads whichever profile `profiles/.active` names (see `workout-coach` Step 0a). After writing, check `profiles/.active`:
- If it's **missing**, or this is the only real profile → offer to write `profiles/.active` pointing at the new file so the coach uses it by default. (AskUserQuestion: yes / no.)
- If it already points at a **different** athlete → ask whether to switch the active profile to this one, or leave it. Don't silently repoint.

Write `profiles/.active` as a single line containing the filename (e.g., `bjray.yaml`).

### Step 5 — Confirm and hand off

Tell the athlete:
1. **Path written** (e.g., `profiles/default.yaml`).
2. **How it will be used** — the orchestrator reads it automatically on every `/workout-coach` invocation; individual skills can also invoke with the profile passed in.
3. **How to edit later** — they can open the file directly; or re-run `/profile-builder <name>` to overwrite.
4. **Suggested next step** — e.g., "`/workout-coach design me a workout for today`" or "`/strength-trainer hypertrophy`" — either will pick up the profile.

### Step 5a — Optional initial Garmin snapshot

**Only if `garmin_enabled` is true.** Ask the athlete once: *"Want me to pull an initial Garmin snapshot now so the coach has training context on the first session? This is the only time it'll run without you asking — every other refresh is on your trigger."* (AskUserQuestion: yes / no.)

- If **yes**: invoke the `garmin-training` skill in Snapshot mode (trigger phrase: "training status"). It will create `fitness-data/`, fetch the latest training status / VO2 / readiness / daily summary / weigh-in, write `health-snapshot.md`, and upsert today's row into `performance-stats.csv`. Surface any errors plainly — if the MCP isn't installed yet, the skill degrades and tells the user what's missing.
- If **no**: explain they can run "training status" or "sync training data" any time. The `training-context` agent will note Garmin as a gap in `metadata.gaps_in_data` until they do.

If `garmin_enabled` is false, skip this step entirely.

## Field-to-schema mapping

Every answer maps to a field in `schemas/athlete-profile.yaml`. When writing the YAML, use the schema's field names exactly. Never invent fields the schema doesn't define.

| Block | Questions | Schema path |
|-------|-----------|-------------|
| A | 1-3 | `name`, `experience_level`, `training_age_years` |
| B | 4-6 | `goals.primary`, `goals.secondary`, `goals.event` (+ `.targets`), `goals.long_range` |
| C | 7-10 | `session_preferences.typical_duration_minutes`, `.hard_cap_minutes`, `.days_per_week`, `.preferred_days` |
| D | 11-12 | `volume_tolerance`, `recovery_quality` |
| E | 13-14 | `equipment_available`, `training_environment` |
| F | 15-16 | `body_part_emphasis`, `body_part_maintenance` |
| G | 17 | `known_preferences` |
| H | 18 | `active_injuries[].{name, surgery_date, phase, restrictions, cleared_by_provider, clearance_milestones[], notes}` |
| H-b | 18b | `training_constraints[].{rule, until, reason}` |
| I | 19 | `working_weights[].{exercise, weight, unit, for_reps, updated}` |
| J | 20 | `notes` |
| K | 21-22 | `garmin_enabled`, `garmin_data_path` |

For fields not asked about (e.g., `preferred_times_of_day`), write them as empty list or null — do not invent values.

## Tone and pacing

- **Warm, brief, and specific.** Sound like a coach doing intake, not a form.
- **One decision at a time** for conditional fields (goal → conditional event → conditional body-part emphasis).
- **Always explain the "so what"** on fields with meaningful tradeoffs. Don't ask for `volume_tolerance` without saying what it changes downstream.
- **Echo back** mid-interview: after Block C, summarize "You're an intermediate athlete targeting hypertrophy, 4 days/week, 60-min sessions with a 75-min cap." Lets them correct mistakes early.
- **No pressure on optional fields.** Working weights, body-part emphasis, free-form notes — make it obvious they can skip.

## Validation before writing

Before writing the YAML, check:

1. `experience_level` is one of: beginner, intermediate, advanced.
2. `goals.primary` is one of the allowed values (see schema).
3. `session_preferences.hard_cap_minutes` ≥ `typical_duration_minutes`.
4. `session_preferences.days_per_week` is 1-7.
5. `volume_tolerance` is low/moderate/high; `recovery_quality` is poor/average/good.
6. `equipment_available` is a non-empty list.
7. `active_injuries[].phase` (if any) is one of: acute, early-rehab, late-rehab, return-to-sport.
8. `working_weights[].unit` (if any) is lbs or kg.
9. `active_injuries[].clearance_milestones[].status` (if any) is one of: pending, awaiting-provider, cleared.
10. `goals.event.targets` numeric fields (if present) are numbers; range fields (`distance_miles`, `pack_weight_lbs`) are `[min, max]` with min ≤ max.
11. `training_constraints[].until` (if present) is an ISO date or month (`YYYY-MM` / `YYYY-MM-DD`); `null` is allowed for open-ended rules.

If any validation fails, explain the issue plainly and ask the user for a correction before writing.

## Output Format

The written file. Match the style of `profiles/default.yaml`:

```yaml
# <Name>'s athlete profile
#
# Generated by the profile-builder skill on YYYY-MM-DD.
# Edit in place. See schemas/athlete-profile.yaml for the full field reference.

athlete_profile:

  name: "..."
  created: "YYYY-MM-DD"
  updated: "YYYY-MM-DD"

  # ─── Training background ───────────────────────────────────────────────

  experience_level: ...
  training_age_years: ...

  # ─── Goals ─────────────────────────────────────────────────────────────

  goals:
    primary: ...
    secondary:
      - ...
    long_range:
      name: ...
      horizon: ...
      description: ...
    event:
      name: ...
      date: ...
      description: ...
      targets:
        peaks: ...
        total_vertical_ft: ...
        distance_miles: ...
        pack_weight_lbs: ...
        notes: ...

  # ... (continue section-by-section, matching profiles/default.yaml — including
  #      active_injuries[].{surgery_date, clearance_milestones} and the
  #      training_constraints block)
```

Comment headers present (use `# ─── Section ──` style from `profiles/default.yaml`). Empty collections written as `[]` or `""` explicitly.

## Reference files

- Schema: `schemas/athlete-profile.yaml`
- Example / style reference: `profiles/default.yaml`
- Downstream consumer: `.claude/agents/workout-coach/AGENT.md` (Step 0a reads the profile)
- Guidelines the profile feeds: `schemas/programming-guidelines.md`
