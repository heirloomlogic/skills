# Robosplainer

A skill that explains one pull request to a reader who has two minutes and four interruptions. It writes a short markdown file built around code blocks, not a wall of chat text.

Point it at a PR number, a PR URL, a branch, or nothing at all. It reads the diff, the whole files the diff touches, the callers, and the tests. Then it writes the explanation and prints the path.

Every report is archived by repository and PR number, with a dated scratch copy alongside it:

```
~/.robosplainer/HeirloomKit/66-elevation-fill-picks-its-hue.md
/tmp/2026-08-17-robosplainer-heirloomkit-66.md
```

## What it is for

Two cases, one skill:

- A pull request someone else opened, which you now have to review.
- A pull request your own agent just opened, which you have not read yet. Run the skill as the last step of the workflow and the PR arrives explained.

## What it is NOT

It does not review the code. There is no verdict, no approval, and no punch list of nits — use `/code-review` for that. It also does not write the PR title or description, and it never produces HTML.

## The document

**Title.** One sentence on what changed, plus the PR link and the diff size.

**The opener.** Two or three sentences: what this part of the system does, and why the change was made. That is the whole of the background. There is no TL;DR section, no background section, and no intuition section, because nobody reads them.

**The walkthrough.** The body, and the reason the document exists. A bold lead-in, a code block, one or two sentences on what it does and why. Repeated three to six times, ordered by what matters, not by file path.

**Risks.** Present only when the reader should stop and open a ticket — data loss, silent failure, a breaking change, a security hole. Most documents have no such section, and none of them say "no risks identified".

## Budget

Brevity is enforced, not encouraged.

| Item | Limit |
|---|---|
| Opener | 3 sentences |
| Walkthrough units | 3–6 |
| Lines per code block | 12 |
| Sentences per caption | 2 |
| Prose, whole document | 350 words |
| Risks | 0–2 bullets |

Code does not count against the prose budget. The code is the point.

## Voice

Plain, in the discipline of [ASD-STE100](https://en.wikipedia.org/wiki/Simplified_Technical_English): active voice, one idea per sentence, plain words, no hedging, and the same word for the same thing every time.

Tables replace code when the point is a set of cases. Mermaid appears only when a value crosses three or more components. Most documents have no diagram. ASCII art never appears.

## Installation

```bash
gh skill install heirloomlogic/skills robosplainer --agent claude-code --force --scope user
```
