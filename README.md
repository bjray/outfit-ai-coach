# Workout Coach

A Claude Code agent and skill system that designs tailored workouts and training programs. It combines specialized fitness skills with real training data to produce intelligent, context-aware programming.

## How It Works

The system has three layers:

1. **Orchestrator Agent** (`workout-coach`) — Interprets your request, gathers context, and delegates to the right skills
2. **Training Context Agent** (`training-context`) — Pulls your real training data from connected sources, analyzes load/fatigue/progression, and feeds it into the skills
3. **Skills** (6 specialized skills) — Each handles a specific aspect of workout design

```
You: "Build me a 12-week mountaineering plan"
 │
 ▼
┌────────────────────┐
│  workout-coach     │ ← interprets your goal, orchestrates the rest
│  (orchestrator)    │
└────────┬───────────┘
         │
         │  ── Inputs (gathered before skills run) ─────────────────
         ├──► profiles/default.yaml         (always) — long-lived
         │                                    preferences, goals, equipment,
         │                                    time budget, injuries
         │
         ├──► training-context agent        (optional) — Strava, Garmin,
         │       │                            TrainingPeaks, oneten
         │       ▼
         │   load / fatigue / gaps / trends
         │
         │  ── Skills (invoked as needed) ──────────────────────────
         ├──► strength-trainer   ┐
         ├──► sport-trainer      ├─► consult schemas/programming-guidelines.md
         ├──► program-builder    ┘    for volume, exercise counts, time budget
         ├──► protocol-engine         (protocols override guidelines)
         └──► injury-adapter          (reads profile.active_injuries)
                  │
                  │   All skills emit v0.1 workouts per
                  │   schemas/workout-template-v0.1.md and render the
                  │   human view per schemas/markdown-rendering.md
                  ▼
         Your workout program (canonical YAML + markdown view)
```

## Skills

### /strength-trainer

Generates strength and resistance training workouts.

**Goals:** hypertrophy, strength, endurance, weight loss

Handles exercise selection, set/rep schemes, rest periods, warm-up/cool-down, and weekly split design based on available days and equipment.

```
/strength-trainer hypertrophy
/strength-trainer strength beginner
```

### /sport-trainer

Generates sport-specific training for mountain and endurance sports.

**Sports:** climbing, trail running, hiking, mountaineering, cycling, skiing

Includes sport-relevant movement patterns, energy system training, mobility/prehab, and guidance on integrating with existing sport sessions.

```
/sport-trainer climbing
/sport-trainer trail-running peak-for-event
```

### /program-builder

Assembles individual workouts into multi-week periodized programs.

**Models:** linear, undulating (DUP), block, or auto-selected based on your goal and experience

Handles phase transitions, deload scheduling, progression rules, and volume/intensity management across weeks.

```
/program-builder 12
/program-builder 8 block
```

### /injury-adapter

Modifies workouts to accommodate injuries while maintaining training stimulus.

**Phases:** acute, early-rehab, late-rehab, return-to-sport

Includes exercise substitution logic for common injuries (ACL, rotator cuff, and combinations), rehab/prehab additions, and always includes a medical disclaimer.

```
/injury-adapter acl early-rehab
/injury-adapter rotator-cuff
```

### /protocol-engine

Reads named training protocol files and generates concrete workouts following the protocol's rules faithfully.

Looks up protocol files in the `protocols/` directory, validates user context against protocol requirements, and produces workouts that match the protocol's structure exactly.

```
/protocol-engine uphill-athlete
```

### /profile-builder

Interactive skill that walks you through creating your athlete profile. Asks a focused set of questions, explains the tradeoffs on each field, and writes a complete `profiles/<name>.yaml`. Use this the first time you set up the coach, or when creating an alternate profile (e.g., a rehab-mode profile alongside your normal one).

```
/profile-builder          # writes to profiles/default.yaml
/profile-builder alice    # writes to profiles/alice.yaml
/profile-builder rehab    # alternate profile for a rehab phase
```

Fresh-setup only — if you want to change a single field later, edit `profiles/<name>.yaml` directly, or re-run this skill to overwrite the whole file.

## Agents

### workout-coach

The main orchestrator. Use this when you have a complex request that spans multiple skills — for example, a periodized sport-specific program with injury accommodations using a named protocol.

The agent:
1. Gathers training context (if data sources are connected)
2. Interprets your goal and identifies which skills to use
3. Asks clarifying questions if needed
4. Invokes skills in the right order
5. Composes outputs into a cohesive plan

### training-context

Pulls and analyzes your real training data to inform workout generation. Connects to:

| Source | What it provides |
|--------|-----------------|
| Strava | Activities — runs, rides, hikes with HR, pace, distance, elevation |
| Garmin Connect | Activities, sleep, HRV, resting HR, training status, body battery |
| TrainingPeaks | Structured plans, TSS, CTL/ATL/TSB |
| oneten | Strength sessions — exercises, sets, reps, weights |
| Manual logs | Markdown/CSV training logs |

Produces:
- **Recent activity summary** — what you've done in the last 7-14 days
- **Training load** — acute/chronic load balance (ATL/CTL/TSB), fatigue status, readiness
- **Progression trends** — are your lifts/paces progressing, plateaued, or regressing?
- **Gap analysis** — undertrained movement patterns, neglected energy systems, overdue deloads

The training context is optional — skills work without it, but produce smarter output with it.

## Protocols

Protocol files live in the `protocols/` directory. Each is a markdown document with YAML frontmatter describing a training methodology.

### Available Protocols

| Protocol | Type | Sports |
|----------|------|--------|
| [Uphill Athlete](protocols/uphill-athlete.md) | Sport-specific | Mountaineering, trail running, ski-mo, alpine climbing |

### Adding a Protocol

Adding a protocol has its own workflow — source material goes in `inbox/<protocol-name>/`, and the protocol file follows the template described in [`protocols/AUTHORING.md`](protocols/AUTHORING.md). See that file for the full template, source-fidelity rules, and smoke-test checklist.

The protocol-engine skill reads these files at runtime — no code changes needed to add a new protocol.

## Workout Output Format

Every skill emits workouts conforming to the **Workout Template Spec v0.1** (`schemas/workout-template-v0.1.md`). The model:

- A **workout** is a header (`id`, `objective`) + an ordered list of **blocks**.
- A **block** has a `name`, optional `rounds`, and a list of **exercises**. Sets live on exercises, rounds live on blocks.
- An **exercise** specifies a quantity — `reps`, `duration`, or `prose` — plus optional `load`, `worn_load`, `tempo`, `intensity`, `protocol`, `modifier`, `per_side`, `references`, `notes`, `substitutions`.
- YAML is canonical; a human markdown view is equivalent.
- Multi-week **programs** (phases, weeks, progression) are project-specific and live in `schemas/workout-output.yaml` — the v0.1 spec defers a program container to a future version. Each day inside a program holds a full v0.1 workout.

Sequential strength work uses `rounds: 1` with `sets > 1` on exercises. Circuits use `rounds > 1` with `sets: 1`. Supersets are modeled as a block with `rounds = set_count` and an `instructions` field disambiguating the superset intent.

The human markdown view follows a dedicated convention in `schemas/markdown-rendering.md` — bold exercise names, notes in nested `- Notes:` sub-bullets, terminal `Rest — …` line on superset blocks. The YAML is canonical; the markdown is just a view.

See `programs/2026-04-18_4week_post-op-acl_rcuff/` for a worked example (one `PROGRAM.md` + one file per workout day).

## Inputs to the coach

Three inputs shape every session the coach produces. Only the profile is required; the other two enrich it when available.

| Input | Kind | File(s) | Required? |
|-------|------|---------|-----------|
| **Athlete profile** | Long-lived preferences (experience, goals, body-part emphasis, session-time budget, equipment, injuries) | `profiles/default.yaml` (+ alternates in `profiles/`) — created interactively via `/profile-builder` or edited directly | Yes (falls back to defaults if missing) |
| **Training context** | Per-session data snapshot (recent activity, load, fatigue, gaps) from Strava/Garmin/TrainingPeaks/etc. | Generated by the `training-context` agent | No |
| **Programming guidelines** | Evidence-based volume/exercise-count/time targets by experience × goal | `schemas/programming-guidelines.md` | Loaded automatically by skills |

The orchestrator reads the profile first, optionally layers training context, then each skill consults the guidelines to size the session. Edit `profiles/default.yaml` to change your defaults; override per session in the request if needed.

## Project Structure

```
workout-coach/
├── .claude/
│   ├── skills/
│   │   ├── strength-trainer/SKILL.md
│   │   ├── sport-trainer/SKILL.md
│   │   ├── program-builder/SKILL.md
│   │   ├── injury-adapter/SKILL.md
│   │   ├── protocol-engine/SKILL.md
│   │   └── profile-builder/SKILL.md
│   └── agents/
│       ├── workout-coach/AGENT.md
│       └── training-context/AGENT.md
├── inbox/                              # source material staging for new protocols
│   └── <protocol-name>/                # drop books/articles/notes here before authoring
├── profiles/
│   ├── default.yaml                    # long-lived athlete preferences
│   └── <name>.yaml                     # alternate profiles (e.g. rehab mode)
├── protocols/
│   ├── AUTHORING.md                    # how to add a new protocol
│   └── uphill-athlete.md
├── programs/                           # user-specific outputs (gitignored)
│   └── 2026-04-18_4week_post-op-acl_rcuff/
│       ├── PROGRAM.md                  # overview, constraints, progression
│       ├── w1-day-a.md                 # one v0.1 workout per file
│       ├── w1-day-b.md
│       └── w1-day-c.md
├── schemas/
│   ├── workout-template-v0.1.md        # canonical workout spec
│   ├── workout-output.yaml             # project extensions: program, metadata, injury_modifications
│   ├── markdown-rendering.md           # human view convention
│   ├── programming-guidelines.md       # volume/time/exercise-count targets
│   ├── athlete-profile.yaml            # profile schema
│   └── training-context.yaml
└── README.md
```

## Setup

### 1. Navigate to the project

```bash
cd workout-coach
```

Claude Code automatically discovers skills in `.claude/skills/` and agents in `.claude/agents/`.

### 2. Connect data sources (optional)

Configure MCP servers for your training data sources. The training-context agent will use whatever is available:

- **Strava** — via Strava MCP server
- **Garmin Connect** — via Garmin MCP server
- **TrainingPeaks** — via TrainingPeaks MCP server
- **oneten** — your local MCP server

If no MCP sources are configured, the system still works — it just won't have training history context.

### 3. Use it

**Quick workout:**
```
/strength-trainer hypertrophy
```

**Sport-specific:**
```
/sport-trainer mountaineering
```

**With a protocol:**
```
/protocol-engine uphill-athlete
```

**Complex request (use the orchestrator):**
```
@workout-coach Build me a 12-week trail running plan for a 50K using the
Uphill Athlete methodology. I have an ACL that's in late rehab and a
functional rotator cuff tear. I climb 2x/week and have access to a gym
with machines, dumbbells, and a treadmill.
```

## License

Licensed under the [MIT License](LICENSE). This covers the original code, skills, schemas, and prompts in this repository.

Protocol files in `protocols/` synthesize third-party training methodologies (e.g. Uphill Athlete) and cite their sources inline. The MIT License does **not** extend to those third-party works — copyright in the underlying books, articles, and methodologies remains with their original authors.

## Design Principles

- **Stateless per invocation.** No persistent user state. You provide context each time (or the training-context agent pulls it from your data sources).
- **Skills are independently useful.** Each skill works on its own for simple requests. The orchestrator adds value for complex, multi-skill compositions.
- **Protocols are data, not code.** Adding a new training methodology is just adding a markdown file.
- **Training context is optional but powerful.** Skills produce reasonable output without it, but produce smarter output when they know your recent training history, fatigue status, and progression trends.
- **Safety first.** Injury-adapted workouts always include medical disclaimers. The system always asks about injuries before generating workouts.
