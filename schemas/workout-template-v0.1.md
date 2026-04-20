# Workout Template Spec v0.1

A template for fitness workouts that humans can write and LLMs can parse/generate consistently.

## Principles

1. **One model**: every workout is a header + ordered list of **blocks**; every block is a name + round count + list of **exercises**. Sequential and circuit workouts are the same shape — sets live on exercises, rounds live on blocks.
2. **Two surface formats**: YAML (canonical, structured) and Markdown (human-friendly). Both describe the same schema.
3. **Explicit quantities**: every exercise must state either reps, duration, or prose. No hidden defaults.
4. **Block-level defaults** cascade to exercises; exercise fields override.

The core formula for total work of any exercise:

```
total reps = block.rounds  ×  exercise.sets  ×  exercise.reps
```

`rounds` and `sets` are orthogonal: rounds counts cycles through the exercise list; sets counts consecutive repeats of a single exercise before moving on. Circuits use `rounds > 1, sets = 1`; sequential workouts use `rounds = 1, sets > 1`; hybrids use both.

---

## YAML schema

### Workout (root)

| Field | Req | Type | Notes |
|---|---|---|---|
| `id` | ✓ | string | e.g., `"SESSION 3"`, `"Day 1"`, `1` |
| `name` | – | string | optional display name |
| `objective` | ✓ | string | short phrase; what the workout is for |
| `blocks` | ✓ | list\<Block\> | ordered |
| `notes` | – | string | workout-level prose |

### Block

| Field | Req | Type | Notes |
|---|---|---|---|
| `name` | ✓ | string | `"Warmup"`, `"Round 1"`, `"(1)"`, `"Main"`, etc. |
| `theme` | – | string | e.g., `"Pull & Push"`, `"Core & Grip"` |
| `type` | – | `work` \| `rest` | default `work` |
| `rounds` | – | int \| `[min, max]` | default `1`; range means "do 2–3 based on feel" |
| `setup` | – | string | one-time instructions before the loop |
| `instructions` | – | string | execution guidance for the block |
| `references` | – | list\<url\> | |
| `defaults` | – | object | fields inherited by exercises (`tempo`, `rest_after`, `load`, `intensity`, etc.) |
| `rest_between_rounds` | – | Duration | rest between cycles |
| `rest_between_exercises` | – | Duration | for sequential-style blocks |
| `exercises` | ✓* | list\<Exercise\> | required unless `type: rest` |
| `notes` | – | string | |

If `type: rest`, the block takes `duration` + `unit` directly and omits `exercises`.

### Exercise

An exercise is **one of**: reps-based, duration-based, or prose-only.

| Field | Req | Type | Notes |
|---|---|---|---|
| `name` | ✓† | string | required unless `prose` |
| `prose` | ✓† | string | free-text exercise; mutually exclusive with name/reps/duration |
| `sets` | – | int | default `1`; "how many times to do this exercise consecutively" |
| `reps` | – | int \| `[min, max]` | reps per set |
| `duration` | – | number | time-based |
| `unit` | – | `s` \| `min` | required when `duration` present |
| `positions` | – | int | multi-pose holds (Founder, bird-dog, etc.); duration applies per position |
| `per_side` | – | bool | asymmetric moves; equivalent to `positions: 2` |
| `load` | – | Load | held/lifted weight |
| `worn_load` | – | WornLoad | pack, vest, belt, etc. |
| `equipment` | – | string | box height, band tension, free-text spec |
| `tempo` | – | string \| object | `"1 rep / 1–2 s"` or `{eccentric, pause, concentric, unit}` |
| `intensity` | – | string | `"easy"`, `"rep-max"`, `"RPE 8"`, `"Zone 2"` |
| `modifier` | – | string | `"for time"`, `"AMRAP"`, `"EMOM"` |
| `protocol` | – | string | `"10s on / 50s off"` |
| `references` | – | list\<url\> | |
| `rest_after` | – | Duration | |
| `notes` | – | string | coach's notes |

### Shared types

```yaml
Duration: { duration: <number>, unit: s | min }
Load:     { value: <number>, unit: lbs | kg }
WornLoad: { value: <number>, unit: lbs | kg, type: pack | vest | belt }
```

### Validation rules

- Workout: `id` and `objective` required.
- Block: `name` required; `exercises` required unless `type: rest`.
- Exercise: must specify a quantity — `reps`, `duration`, or `prose`.
- `unit` required when `duration` is set.
- `per_side` and `positions` are aliases; use whichever reads better — `per_side` for bilateral strength, `positions` for multi-pose holds.

---

## Markdown format (human-writable equivalent)

```markdown
# <id>[: <name>] — <objective>

## <block name>[ — <theme>] (×<rounds>)
<optional setup / instructions prose>

- <exercise line>
- <exercise line>
```

**Exercise line grammar** (all fields optional except name + quantity):

```
- <name> — <quantity>[ @ <load>][ <modifiers>][; <notes>]
```

Where `<quantity>` is one of:

- `<sets>×<reps>` → `Bench Press — 4×5`
- `<reps>` (sets inferred from block rounds, default 1) → `Pull ups — 5`
- `<duration><unit>` → `Side Plank — 20s`
- `<sets>×<duration><unit>` → `Hangs — 3×10s`

Modifiers: `each side`, `×N positions`, `for time`, tempo in parens, etc.

Rest blocks: `## Rest — 5 min` (no exercises).

---

## Worked examples

### Example 1 — Sequential (Upper A)

```yaml
id: "Day 1"
name: "Upper A"
objective: "Strength Emphasis"
blocks:
  - name: "Main"
    exercises:
      - { name: "Bench Press",    sets: 4, reps: 5 }
      - { name: "Barbell Row",    sets: 4, reps: 6 }
      - { name: "Overhead Press", sets: 3, reps: 6 }
      - { name: "Lat Pulldown",   sets: 3, reps: 8 }
      - { name: "Skull Crushers", sets: 3, reps: 10 }
      - { name: "Dumbbell Curl",  sets: 3, reps: 10 }
```

### Example 2 — Circuit (Climbing Conditioning)

```yaml
id: 1
name: "Climbing Conditioning"
objective: "Pull/Push + Core"
blocks:
  - name: "Warmup"
    exercises:
      - { name: "Hangboard protocol", reps: 10, protocol: "10s on / 50s off" }
      - { name: "Foot protocol", prose: "Steps, ankle mobility" }

  - name: "Round 2"
    theme: "Pull & Push"
    rounds: 3
    exercises:
      - { name: "Pull ups",    reps: 5 }
      - { name: "Squat press", reps: 8, load: { value: 25, unit: lbs } }
      - { name: "Hangs",       duration: 10, unit: s }

  - name: "Round 4"
    theme: "Core & Grip Stability"
    rounds: [2, 3]
    exercises:
      - { name: "Side Plank",   duration: 20, unit: s }
      - { name: "Farmer Carry", duration: 30, unit: s, load: { value: 50, unit: lbs } }
      - { name: "Rest",         duration: 30, unit: s }
```

### Example 3 — Mixed (SESSION 3, climbing stamina)

```yaml
id: "SESSION 3"
objective: "Strength / Climb Stamina"
blocks:
  - name: "(1)"
    rounds: 6
    setup: "Pick 4 routes 3 V-levels below your ability. Record your routes."
    exercises:
      - { name: "Quadzilla Complex",         reps: 3, load: { value: 25, unit: lbs } }
      - { name: "2-Leg Poor Man's Leg Curl", reps: 15 }

  - name: "(2)"
    rounds: 4
    rest_between_rounds: { duration: 1, unit: min }
    exercises:
      - { prose: "Climb each route back-to-back with no rest" }

  - { name: "(3)", type: rest, duration: 5, unit: min }
  # (4)–(8) repeat the (2)/(3) pattern
```

### Example 4 — Sequential with defaults + references

```yaml
id: "SESSION 5"
objective: "Leg Strength"
blocks:
  - name: "Warmup"
    exercises:
      - { name: "Dynamic stretch routine", duration: 5, unit: min,
          references: ["https://youtu.be/lbozu0DPcYI"] }
      - { name: "Air Squat",      reps: 20 }
      - { name: "Turkish Get Up", reps: 10 }
      - { name: "Burpee",         reps: 10 }

  - name: "Main"
    instructions: "Complete all sets of each exercise before moving on."
    defaults:
      tempo: "1 rep / 1–2 s"
      rest_after: { duration: 2, unit: min }
    exercises:
      - { name: "Split Jump Squat (Basic)", sets: 6, reps: 10, per_side: true,
          references: ["https://youtu.be/72xY37N_Sww"],
          notes: "Start 30cm split; work deeper as you gain strength." }
      - { name: "Squat Jumps",              sets: 6, reps: 10,
          references: ["https://youtu.be/SDJIQq-BrCc"] }
      - { name: "Box Step-ups",             sets: 6, reps: 10, per_side: true,
          equipment: "Box 75% of knee-cap height",
          references: ["https://youtu.be/l4AA5d5mInQ"],
          notes: "Minimal rear-leg assist." }
      - { name: "Front Lunge (Basic)",      sets: 6, reps: 10, per_side: true,
          references: ["https://youtu.be/QOVaHwm-Q6U"] }

  - name: "Cooldown"
    exercises:
      - { name: "Easy aerobic", duration: 10, unit: min, intensity: easy }
```

### Example 5 — Solo "for time" effort + multi-position holds

```yaml
id: "SESSION 4"
objective: "Step-ups"
blocks:
  - name: "(1)"
    exercises:
      - name: "Step-ups"
        reps: 550
        modifier: "for time"
        worn_load: { value: 30, unit: lbs, type: pack }

  - name: "(2)"
    rounds: 4
    exercises:
      - { name: "Standing Founder", duration: 15, unit: s, positions: 2 }
      - { name: "Kneeling Founder", duration: 15, unit: s, positions: 2 }
      - { name: "Low Back Lunge",   duration: 15, unit: s, positions: 2 }
      - { name: "Face Down Back Extension", reps: 10 }

  - name: "(3)"
    rounds: 6
    exercises:
      - { name: "Curl to Press",    reps: 5,  load: { value: 25, unit: lbs } }
      - { name: "1-leg Calf Raise", reps: 10, load: { value: 25, unit: lbs }, per_side: true }
      - { name: "Pull-ups",         reps: 5 }
      - { name: "Dumbbell Hinge",   reps: 10, load: { value: 25, unit: lbs } }

  - name: "(4)"
    rounds: 3
    exercises:
      - { name: "Lat + Pec Stretch", duration: 30, unit: s }
      - { name: "Instep Stretch",    duration: 30, unit: s }
```

---

## Authoring conventions

- Prefer numeric values with explicit units (`lbs`, `kg`, `s`, `min`).
- Avoid descriptive loads ("heavy"); use a number or a range.
- Split alternate prescriptions (male/female) at authoring time — pick one for the template.
- Use `prose` exercises sparingly; prefer structured reps/duration when possible.
- Progressions across sessions live at the **program** level (future spec); a workout names one concrete exercise for that day.

---

## Open items (intentionally deferred)

- **Program spec** — multi-workout container with longitudinal progressions, schedules, substitutions.
- **Structured tempo object** — e.g., `{eccentric: 2, pause: 0, concentric: 1}` if free-text strings become limiting.
- **Exercise library / IDs** — stable identifiers so a workout can reference a canonical exercise instead of restating name/form.
