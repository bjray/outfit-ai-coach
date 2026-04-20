# Programming Guidelines

Canonical targets for **weekly training volume**, **per-session exercise count**, and **time estimation**. Read by `strength-trainer`, `sport-trainer`, and `program-builder` to size sessions coherently with the athlete's profile.

The ranges here are evidence-based (hypertrophy literature — Schoenfeld et al.; strength — Helms et al.; endurance — Seiler, Uphill Athlete). They are **defaults**, not dogma: a protocol, a stated preference, or a PT clearance can override any of these.

---

## 1. Weekly set volume per muscle group

Sets per muscle group per week, counting direct work only. A compound lift (bench press) counts as a full set for its primary mover (chest) and a half set for its secondary movers (triceps, front delt).

| Muscle group      | Beginner (wk 0–12 mo) | Intermediate (1–4 yr) | Advanced (4+ yr) |
|-------------------|-----------------------|-----------------------|------------------|
| Chest             | 8–12                  | 12–16                 | 16–22            |
| Back              | 10–14                 | 14–18                 | 18–24            |
| Quads             | 8–12                  | 12–16                 | 16–22            |
| Hamstrings        | 6–10                  | 10–14                 | 14–20            |
| Glutes            | 6–10                  | 10–14                 | 14–20            |
| Shoulders         | 6–10                  | 10–14                 | 14–20            |
| Biceps            | 4–8                   | 8–12                  | 10–16            |
| Triceps           | 4–8                   | 8–12                  | 10–16            |
| Calves            | 4–8                   | 6–12                  | 10–16            |
| Core              | 6–12                  | 10–16                 | 14–20            |

### How to use these ranges

- **Volume tolerance** (from profile) picks within the range:
  - `low` → lower third of the range
  - `moderate` → middle third
  - `high` → upper third
- **Goal** shifts the range:
  - `hypertrophy` → upper end (volume drives growth)
  - `strength` → lower end (intensity matters more; rest is longer)
  - `weight-loss` → middle, with shorter rests and circuit bias
  - `endurance` / `sport-performance` → lower end for non-specific lifts
- **Body-part emphasis** (from profile) shifts a muscle up one experience tier (e.g., intermediate athlete with `body_part_emphasis: [chest]` → program chest at the advanced range).
- **Body-part maintenance** (from profile) shifts a muscle down: use the lower third of the beginner range.
- **Active injury** affecting a muscle → zero direct work until cleared, no matter the range.

---

## 2. Exercises per muscle per session

How many distinct exercises to program for a muscle in a single session.

| Role                                    | Beginner | Intermediate | Advanced |
|-----------------------------------------|----------|--------------|----------|
| Primary muscle on its focus day         | 1–2      | 2–3          | 3–4      |
| Secondary muscle (incidental volume)    | 0–1      | 1–2          | 2        |
| Maintenance muscle                      | 0–1      | 0–1          | 0–1      |

"Primary muscle on its focus day" means e.g., chest on a push day or upper day. If an intermediate athlete is doing a 60-min upper day, plan **2–3 chest exercises**, not 1.

### Typical sets per exercise

- Primary compound (e.g., bench press): 3–5 sets
- Secondary compound (e.g., incline DB press): 3–4 sets
- Isolation accessory (e.g., cable fly): 2–3 sets

---

## 3. Per-block time estimation

Use these to sanity-check the session budget **before** finalizing the workout.

### Per-set work time

| Exercise type                    | Work time per set | Rest           |
|----------------------------------|-------------------|----------------|
| Heavy compound (1–5 reps)        | 20–40s            | 2.5–5 min      |
| Moderate compound (6–12 reps)    | 25–45s            | 90s–3 min      |
| Accessory (12–20 reps)           | 30–60s            | 45–90s         |
| Duration hold (plank, etc.)      | 20–60s            | 30–60s         |
| Circuit exercise (sets=1)        | 15–30s            | minimal intra  |

### Block-level budget formula

For a straight-sets block (rounds=1):

```
block_time ≈ sum over exercises of (sets × (work + rest))
```

For a superset block (rounds>1, sets=1 on exercises):

```
round_time ≈ sum(exercise works) + sum(rest_between_exercises) + rest_between_rounds
block_time ≈ rounds × round_time
```

Add **30–60s transition overhead** between exercises (tool swap, walk to station, re-position).

### Session-level overhead

- **General warm-up**: 5–10 min
- **Warm-up sets on the primary lift**: 3–5 min (2–4 ramp sets, short rest)
- **Cool-down / stretch**: 3–5 min
- **Transition between blocks** (not within): +2–3 min per block transition

### Typical session budgets at a glance

| Session length | Warm-up | Main blocks | Accessories | Core | Cool-down |
|----------------|---------|-------------|-------------|------|-----------|
| 45 min         | 6       | 18–22       | 10–14       | 4–6  | 3         |
| 60 min         | 8       | 22–28       | 14–18       | 6–8  | 4         |
| 75 min         | 10      | 28–34       | 18–24       | 8    | 5         |
| 90 min         | 10      | 34–42       | 24–30       | 8    | 6         |

The **hard_cap_minutes** from the profile is absolute. If the computed block budget exceeds it, cut accessories first (not the primary block), then drop a set per exercise before cutting exercises entirely.

---

## 4. Rest and density

- **Compound strength (<6 reps):** 2.5–5 min rest.
- **Moderate rep hypertrophy (6–12):** 90s–3 min. Longer for compounds, shorter for isolation.
- **High rep / metabolic (15+):** 30–90s.
- **Supersets:** 30–45s between exercises in the pair, 60–90s after the pair.
- **Circuits:** as short as feasible to maintain quality; rest *between rounds*, minimal between stations.

Shorter rest means more metabolic stress but less work volume — don't drop rest below the ranges above to save time if the goal is hypertrophy or strength. Save time by dropping a set or an exercise instead.

---

## 5. Goal-specific scaling

| Goal                 | Rep range (primary) | Intensity         | Rest           | Volume (vs range) |
|----------------------|---------------------|-------------------|----------------|-------------------|
| Hypertrophy          | 6–12                | RPE 7–9, 65–80%   | 90s–3 min      | Upper end         |
| Strength             | 1–5                 | RPE 8–10, 80–95%  | 2.5–5 min      | Lower end         |
| Endurance (muscular) | 15–25+              | RPE 6–8, 40–60%   | 30–60s         | Middle            |
| Weight-loss          | 8–15                | RPE 7–8           | 30–90s         | Middle, circuits  |
| Rehab                | variable            | RPE 5–7           | 60–120s        | Lower (ramp)      |

---

## 6. Deload rules

Every 4th week by default, or when the athlete flags fatigue. Apply one of:

- **Volume cut:** same load, ~50% of working sets (round down). Same exercises.
- **Load cut:** ~80% of working loads, same sets, add slow eccentric tempo (3s down).

Drop advanced structures (supersets, AMRAP, tempo extremes) for the deload week — straight sets only, conservative rest. Warm-up and mobility stay the same or increase.

Recovery-quality-poor athletes should deload every 3rd week; recovery-quality-good athletes can push to every 5th.

---

## 7. Worked example: 60-min intermediate hypertrophy upper day

Inputs: `experience_level: intermediate`, `goal: hypertrophy`, `typical_duration_minutes: 60`, `body_part_emphasis: [chest, back]`, `volume_tolerance: moderate`.

**Weekly target volume** (upper-body, 2 upper days/week):
- Chest: emphasized → advanced range upper end → 18–20 sets/week → **9–10 sets per upper day**
- Back: emphasized → 18–20 sets/week → **9–10 sets per upper day**
- Shoulders: 10–14 sets/week → **5–7 sets per upper day**
- Biceps: 8–12 sets/week → **4–6 sets per upper day**
- Triceps: 8–12 sets/week → **4–6 sets per upper day**

**Session exercise plan** (intermediate primary: 2–3 exercises per primary muscle):
- Warm-up: 8 min
- Main block — flat bench press: 4 × 6–8 (chest primary), ~9 min incl. warm-up ramps
- Main block — chest-supported row: 4 × 8–10 (back primary), ~7 min
- Accessory pair — incline DB press + lat pulldown: 3 × 10 each, superset, ~8 min
- Accessory pair — cable fly + cable row: 3 × 12 each, superset, ~7 min
- Accessory — DB lateral raise: 3 × 12–15, ~5 min
- Arms pair — EZ curl + cable pressdown: 3 × 10 each, superset, ~6 min
- Core: 2 movements, ~5 min
- Cool-down: 4 min

**Volume count:** chest 4+3+3 = 10 sets ✓, back 4+3+3 = 10 ✓, shoulders 3+ some from pressing = ~5 ✓, biceps 3 + pulling = ~4–5 ✓, triceps 3 + pressing = ~4–5 ✓.

**Time check:** 8+9+7+8+7+5+6+5+4 = **59 min** ✓.

This is the shape of a well-scoped intermediate hypertrophy upper day: **3 chest-hitting exercises**, **3 back-hitting exercises**, direct work for shoulders/biceps/triceps, core block, fits in the hard cap.

---

## 8. Fallback defaults (no profile)

If no profile is loaded, skills assume: `experience_level: intermediate`, `goal: general-fitness`, `typical_duration_minutes: 60`, `volume_tolerance: moderate`, `recovery_quality: average`. Note the fallback in the output so the user knows what to change if it's wrong.
