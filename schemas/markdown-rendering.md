# Markdown Rendering Convention

How to render a Workout Template v0.1 workout (YAML) into a clean human-readable markdown view. YAML remains canonical; this file defines the **view**.

The goal is readability without losing detail. Keep the exercise line short; push detail to a nested `Notes:` sub-bullet.

## Exercise line

```
- **<Name>** — <qty>[ @ <intensity>]
    - Notes: <equipment, cues, rest, safety, etc. — one concise line, sentences run together>
```

Rules:

1. **Bold the exercise name.** Use the clean `exercise.name` field — no parentheticals inline.
2. **Quantity + intensity on the main line.** Examples: `3×10 @ RPE 7-8`, `10 @ RPE 6-7`, `30s`, `5 rounds of 10s on / 50s off`.
3. **Push detail to `Notes:`** — equipment, setup, tempo, coaching cues, per-exercise rest (when not a superset), safety callouts. One concise sub-bullet. Use full sentences. If there are multiple independent cues, one sentence per cue, run together — don't create multiple Notes sub-bullets.
4. **No parenthetical equipment in the name.** If the YAML `name` is `"Seated machine chest press (neutral grip if available)"`, lift the parenthetical into the YAML `equipment` field and out of the display name. The markdown Notes then reads "Neutral grip if available."

### Example

YAML:
```yaml
- { name: "Seated machine chest press", equipment: "neutral grip if available",
    sets: 1, reps: 10, intensity: "RPE 6-7",
    notes: "Stop short of full lockout to protect left shoulder" }
```

Markdown:
```
- **Seated machine chest press** — 10 @ RPE 6-7
    - Notes: Neutral grip if available. Stop short of full lockout to protect left shoulder.
```

## Superset blocks

For a block with `rounds > 1` modeling a superset, end the exercise list with a trailing `- Rest — <interval>` bullet. This represents the inter-round rest. Do **not** prepend an italic `*Execute: ...*` preamble — the block heading already communicates the superset.

```
### Main — Upper Superset A (push/pull) (×3, superset)

- **Seated machine chest press** — 10 @ RPE 6-7
    - Notes: Neutral grip if available. Stop short of full lockout to protect left shoulder.
- **Chest-supported DB row** — 10 @ RPE 6-7
    - Notes: Prone on incline bench. Pulls scaps back; balances the press; no spinal load.
- Rest — 30-45s between exercises, 60-90s after the pair, 3 rounds
```

Derive the Rest bullet from the block's `rest_between_exercises` + `rest_between_rounds` + `rounds`.

## Straight-sets blocks

For a block with `rounds: 1` and exercises carrying `sets > 1`, rest is per-exercise. Put the rest interval **inline in the Notes sub-bullet** for each exercise. Drop any `*Straight sets (not supersetted).*` preamble — the heading says "straight sets".

```
### Right-Leg Posterior — straight sets

- **Right-leg seated hamstring curl (unilateral)** — 3×10 @ RPE 6-7
    - Notes: Rest 90s. Right leg only; left leg off the pad/supported. Stop immediately if knee feels off.
- **Supine single-leg hip thrust** — 3×10
    - Notes: Rest 60s. Bench-supported, bodyweight, right leg only. Left leg rests fully extended/supported on a chair or floor — do NOT use it to push.
```

## Duration-based exercises

```
- **Side plank** — 3×25s per side
    - Notes: Rest 30s. From forearm and right knee; left leg stacked, unloaded.
```

For zone/endurance work:

```
- **Steady run** — 90 min @ Zone 2
    - Notes: Conversational pace; stay under aerobic threshold.
```

## Prose-only exercises

For exercises that are pure prose (no structured reps/duration), print the prose directly after the em dash — no Notes sub-bullet needed.

```
- **Bench ramp** — Empty bar ×10, 40% ×5, 50% ×5, 60% ×3
```

## Safety-critical callouts

Safety language ("DO NOT perform on left leg", "stop at sharp pain") stays in the Notes sub-bullet — still one line, but uppercase the verb for emphasis. Never rely on an italic preamble above the block for safety; preambles get skimmed.

```
- **Right-leg seated leg extension** — 3×10 @ RPE 6-7
    - Notes: Rest 90s. ROM 90°→45° only. DO NOT perform on left leg. First true quad load — very conservative on weight.
```

## Block heading

```
### <Block name>[ — <theme>][ (×<rounds>[, <mode>])]
```

- `<mode>` is `superset`, `circuit`, or omitted. Use `superset` when the block has rounds > 1 **and** the intent is superset rather than circuit — make the intent explicit in YAML `instructions` too.
- For rest blocks (`type: rest`), use `### Rest — <duration> <unit>`.

## Block-level instructions

If the block has `instructions`, render them as a single italic line immediately under the heading **only if** the instructions are not already implied by the heading or captured in per-exercise Notes. Default: **skip** block instructions in the markdown view. They live in the YAML.

## When in doubt

Prefer fewer words. The person executing the workout is looking at their phone between sets — the markdown should read like a coaching card, not a protocol document. Detail that belongs in an audit trail stays in the YAML.
