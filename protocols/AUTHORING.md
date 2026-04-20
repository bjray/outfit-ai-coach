# Authoring Protocols

How to add a new training protocol or update an existing one. Protocol files in `protocols/*.md` are read at runtime by the `protocol-engine` skill; they must be faithful to the methodology they represent.

## What belongs in `protocols/`

A protocol is a **named methodology with opinionated, load-bearing rules** — specific progression math, heart-rate formulas, volume-distribution rules, phase structures. Examples: Uphill Athlete, 5/3/1, Starting Strength, Tactical Barbell, MAF, GZCL, Juggernaut.

**Not** protocols: push/pull splits, upper/lower splits, PPL, full-body, bro split, generic HIIT/Tabata session shapes. These are session architectures — the `strength-trainer` skill handles them from the athlete's profile (`days_per_week`, `goals`, `volume_tolerance`). Adding them as protocol files adds noise without adding methodology.

**Quick test:** if describing the approach requires a formula, a table, or a phase diagram that a skilled coach couldn't reconstruct from "it's a push/pull split," it's a protocol. Otherwise, it's a session shape and belongs in the skills, not here.

## Source material

Fidelity to the source is the point. Protocols authored from general training knowledge (instead of the actual book, article, or coach's written methodology) drift silently. If you have source material, use it.

Drop source material in `inbox/<protocol-name>/` as markdown, PDFs, or links before asking for the protocol to be authored. One folder per protocol keeps things clean. If no source is available, we can still author from general knowledge — but the protocol's frontmatter must flag `source: "general training knowledge"` so downstream users know the fidelity is approximate.

## Workflow — new protocol

1. **Scope**
   - Confirm the methodology passes the quick test above (it's a protocol, not a session shape).
   - Name it (kebab-case filename: `uphill-athlete.md`, `531.md`, `tactical-barbell.md`).
2. **Collect sources**
   - Drop source material into `inbox/<name>/`.
   - Note what's canonical (the book) vs. supplementary (interviews, blog posts). Book > article > interview > forum for fidelity.
3. **Synthesize into the template**
   - Use the frontmatter + section structure described in `README.md` "Adding a Protocol" and modeled by `protocols/uphill-athlete.md`.
   - For every load-bearing rule (rep schemes, %1RM formulas, HR zones, cycle lengths), cite the source inline — e.g., `> (Training for the New Alpinism, ch. 7)`. If a detail is filled in from general knowledge, mark it `> (inferred — not in source)`.
   - Do not round or simplify formulas. If the source says "training max = 90% of 1RM" and "first cycle uses 85% of training max," keep both numbers and the chain.
4. **Smoke-test**
   - Invoke `/protocol-engine <name>` against the default athlete profile. The skill should produce a concrete v0.1 workout that reflects the protocol's structure.
   - Invoke it against a profile edge case (beginner, or a profile the protocol excludes). Confirm the skill either adapts per the protocol's variations or flags a contraindication.
5. **Hand off for review**
   - The user reviews; iterate until the protocol reads the way the source describes it.

## Workflow — updating an existing protocol

1. Bump the `version` field in the frontmatter (add it if missing — `version: 1.1`).
2. Append a `## Changelog` section at the bottom (create if missing):
   ```
   ## Changelog
   - 2026-05-01 (v1.1): corrected training-max percentages per 5/3/1 Forever ch. 2; added joker sets variation.
   - 2026-04-18 (v1.0): initial protocol, authored from general knowledge.
   ```
3. If the update changes load-bearing rules (progression math, HR formulas, phase lengths), call it out in the changelog — future runs of the protocol-engine will produce different workouts.
4. Smoke-test the updated protocol the same way.

## Template structure (reference)

Required frontmatter fields (see `README.md` for the full shape):

- `name`, `author`, `type`, `goal[]`, `experience_level[]`, `required_equipment[]`, `cycle_length_weeks`
- Recommended: `version`, `source` (canonical-book | article | general-training-knowledge), `optional_equipment[]`

Required sections:

- **Overview** — what the protocol is, who it's for, book/article references
- **Core Principles** — the 4-8 load-bearing rules
- **Structure** — weekly template, phase structure, set/rep/zone schemes with numbers
- **Progression Rules** — how to advance between cycles; cite the source
- **Variations** — named variations the user might request
- **Contraindications** — when NOT to use this protocol

Optional sections:

- **Tests / benchmarks** — e.g., Aerobic Deficiency Syndrome test for Uphill Athlete, 1RM test for 5/3/1
- **Example weekly layout** — prose or YAML showing a concrete week
- **Glossary** — terms the source uses (e.g., "AeT", "TM", "AMRAP")

## Authoring checklist

Before declaring a protocol done:

- [ ] Frontmatter complete and accurate (including `version` and `source`)
- [ ] Every load-bearing number (percentage, zone, duration) has an inline source citation or an `(inferred)` marker
- [ ] Core Principles section covers the methodology's non-negotiables
- [ ] Progression Rules are concrete enough to execute from the text alone
- [ ] Contraindications list is explicit (experience floor, equipment requirements, medical/injury contraindications)
- [ ] Smoke-tested via `/protocol-engine <name>` against a realistic profile
- [ ] Changelog updated (if updating an existing protocol)
- [ ] Source material filed in `inbox/<name>/` or removed if no longer needed

## When a protocol overlaps with skills

Some methodologies prescribe volume in ways that conflict with `schemas/programming-guidelines.md` (e.g., 5/3/1 main-work volume is intentionally low). **The protocol wins.** The `protocol-engine` skill is documented to override guidelines when the protocol is opinionated. Do not mutate the protocol to match the guidelines — mutate the output to match the protocol.

Where the protocol is silent (e.g., what accessories to pick, how many core sets), fall back to guidelines + profile.
