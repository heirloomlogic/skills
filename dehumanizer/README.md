# Dehumanizer

A writing skill that removes signs of AI-generated writing without making the
output sound like an encyclopedia entry or a sales pitch.

Forked from [humanizer](https://github.com/blader/humanizer). Same detection
foundation, different voice: deadpan, economical, recalibrated to flag overuse
rather than carpet-bomb every dash and triple.

## What it is

A reading-quality tool. Point it at AI-flavored prose — a README, changelog,
doc, presentation, blog draft — and it rewrites the parts that read like a
machine while keeping the meaning and matching the register of the input.

## What it is NOT

This is not a tool for hiding that AI wrote something, and not a way to beat AI
detectors — the job is the writing, not the provenance. The same tics show up
in plenty of human writing, and it fixes those too. If the text is clearer and
less annoying afterward, the skill worked, regardless of who or what produced
the draft.

## How it differs from the humanizer

| | Humanizer | Dehumanizer |
|---|---|---|
| **Detection** | Wikipedia "Signs of AI writing" catalog | Same foundation, kept current |
| **Aggression** | Strips aggressively — kills em dashes, hedging, rule of three | Recalibrated — flags overuse, leaves appropriate use alone |
| **Voice** | "Add soul": first person, mixed feelings, performative | Deadpan, economical, dry |
| **Output** | Tends toward soul-injection | Matches the register of the input |

## Pattern groups

The full catalog lives in [`references/patterns.md`](references/patterns.md),
grouped by type. Read that file for examples — it is the source of truth, not
this list:

- **Content** — significance inflation, notability name-dropping, fake -ing
  analysis, promotional tone, vague attribution, formulaic "challenges" sections
- **Language and grammar** — AI vocabulary, copula avoidance, negative
  parallelism and tailing negation, rule of three, synonym cycling, false
  ranges, passive/subjectless fragments, persuasive-authority tropes
- **Style** — em dashes (incl. the sales-pitch closer), boldface, inline-header
  lists, title case, emojis, curly quotes, hyphen-pair consistency, AI markup
  and citation artifacts, fragmented headers
- **Communication** — chatbot artifacts, knowledge-cutoff disclaimers, sycophancy
- **Filler and hedging** — filler phrases, excessive hedging, generic positive
  conclusions, signposting and announcements

The catalog also has a short "No longer reliable tells" section — patterns that
have aged out as models changed.

## Installation

Copy the skill into your agent skills directory:

```bash
cp -r dehumanizer/ .agent/skills/dehumanizer/
```

## Upgrading

AI writing tells move. Models change their habits, new artifacts appear, and old
tells age out. Re-check the catalog against the source roughly every 3–6 months:

1. **Pull the source.** Read the current
   [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
   (maintained by WikiProject AI Cleanup). Optionally diff against the upstream
   [humanizer](https://github.com/blader/humanizer) for newly added patterns.
2. **Diff against `references/patterns.md`.** Note new categories, new flagged
   phrases, and any tells the source now calls outdated.
3. **Apply the recalibration philosophy.** This skill flags *overuse*, it
   doesn't carpet-bomb. When importing a pattern, keep the "acceptable use"
   half. Reject upstream fixes that trade an AI tell for bad grammar (e.g.
   blanket-stripping hyphens). Generalize any voice guidance — no dated slang or
   brand callouts as the point.
4. **Insert into the right group and renumber.** Pattern numbers are reference
   handles only; keep them sequential within their group and update the table of
   contents. `SKILL.md` deliberately does not hardcode counts or numeric ranges,
   so adding a pattern only touches `patterns.md`.
5. **Record what aged out.** Move newly-unreliable tells to the "No longer
   reliable tells" section rather than deleting them — the history is useful.
6. **Bump the version** in `SKILL.md` and add a line to the history below.

## Version history

- **1.2.0** — Added passive/subjectless fragments, persuasive-authority tropes,
  hyphen-pair consistency (reframed: no blanket de-hyphenation), AI markup &
  citation artifacts, fragmented headers, and signposting; folded tailing
  negation into negative parallelism. Removed hardcoded pattern count and
  numeric group ranges from `SKILL.md` (the source of the three-file drift).
  Generalized the voice guidance away from dated, performative framing. Added a
  scope note and this upgrading methodology. Added a "No longer reliable tells"
  section.
- **1.1.0** — Restructured: moved patterns to reference file, removed
  generational labels, trimmed SKILL.md from 537 to 172 lines.
- **1.0.0** — Initial release. Forked from humanizer 2.1.1 with voice
  recalibration.
