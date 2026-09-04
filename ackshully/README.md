# Ackshully

A skill that explains one thing at three depths, in one markdown file, so the reader can stop at any depth and still be better off.

Give it an argument and the argument is the context. `ackshully king lear`. `ackshully gravity's rainbow chapter 5`. A PR number, a PR URL, a branch, a repository, a file path, a Wikipedia page, or a bare subject — it works out what kind of thing it has and reads accordingly.

Give it nothing and it reads its environment: a branch with commits its base does not have, otherwise the repository, otherwise the long markdown file the directory is built around, otherwise the file already open in the conversation. If two candidates are equally likely it asks rather than guessing.

Every report is archived by context, with a dated scratch copy alongside it:

```
~/.ackshully/HeirloomKit/66-elevation-fill-picks-its-hue.md
~/.ackshully/king-lear/act-1.md
/tmp/2026-09-04-ackshully-king-lear-act-1.md
```

## Progressive disclosure

Three levels. Each one is complete on its own and assumes the reader stopped at the level above.

**Level 1 — the opener.** The first prose in the document, sitting immediately under the `#` title with nothing between them — no subtitle, no summary line, no citation. Two or three sentences, no heading of its own, beginning with "Well actually,", "Ackshully," or "Actually factually," picked at random. That is the whole of the joke. Everything after the comma is the largest true statement about the thing, and nothing further down the document is arch about it.

**Level 2 — the longer version.** One section, 150 to 300 words. When the reader finishes it they understand the thing well enough to talk about it.

**Level 3 — the detail sections.** Zero to five, each added only when a reader who already read Level 2 would still be missing something they need. What that means depends on the target: for a pull request it is the code a reviewer has to see, cited by file and line; for a chapter of a novel it is who is who and what recurs; for a chapter of a history book it is the people, the dates and how they connect to events the chapter never mentions; for a subject it is the claims carrying the weight and the parts genuinely disputed.

A last section appears only when the reader must act or must not trust — data loss, a breaking change, a security hole, a claim resting on a source that could not be checked. Most documents do not have one, and none of them say "no risks identified".

## What it is NOT

It does not review code. There is no verdict, no approval, and no punch list of nits — use `/code-review` for that. It does not write the PR title or description. It does not produce HTML or slides. It is not the right tool for a question that wants one sentence back.

## Budget

Brevity is enforced, not encouraged. Prose is every word outside a code block, a table, and a diagram.

| Item | Limit |
|---|---|
| Opener | 3 sentences |
| The longer version | 300 prose words |
| Detail sections | 0–5 |
| Prose per detail section | 250 words |
| Prose, whole document | 1000 words |
| Code blocks | 1 per detail section |
| Lines per code block | 12 |
| Sentences beside a code block | 2 |

Over budget means cut a section, not compress every sentence into a fragment.

## Voice

The draft goes through the [`dehumanizer`](../dehumanizer/SKILL.md) skill before it is written to disk. Active voice, one idea per sentence, plain words, no hedging, the same word for the same thing every time, and no teaser headings.

Facts get verified or marked unverified. It does not invent a date, a name, a line number, or a quotation. The King Lear example cites by scene rather than by line, because line numbers do not agree across editions.

Tables replace code when the point is a set of cases. Mermaid appears only when a value or a line of causation crosses three or more parts. Most documents have no diagram. ASCII art never appears.

## Examples

- [`references/example-pull-request.md`](references/example-pull-request.md) — a 305-line Swift change, four detail sections, code blocks cited by file and line.
- [`references/example-chapter.md`](references/example-chapter.md) — Act 1 of *King Lear*, a cast table, quoted verse, and a short note on what the text does not settle.

## Installation

```bash
gh skill install heirloomlogic/skills ackshully --agent claude-code --force --scope user
```
