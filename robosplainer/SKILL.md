---
name: robosplainer
description: >-
  Use when someone wants a code change explained — "explain this PR", "what
  does PR #42 do", "walk me through this diff", "explain the change on this
  branch", "help me review this", or a bare PR number or URL. Also use right
  after an agent opens a pull request, so the PR arrives with a plain
  explanation of what landed. Works for pull requests written by other people
  and for pull requests written by agents. NOT for: writing the PR title or
  description itself, code review verdicts and approvals (use /code-review),
  security review, HTML or slide output, or summarizing a whole repository.
metadata:
  version: "2.0.0"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - AskUserQuestion
---

# Robosplainer

Explain one code change in the time it takes to drink a coffee. Write one markdown file. Show the code.

**The reader has two minutes and four interruptions.** They are not going to read your background section. They will scroll to the code. Give them the code, and put one sentence beside each block that says what it does.

A long explanation of a small change is a failure, not a bonus.

## 1. Resolve the target

Accept a PR number, a PR URL, a branch name, or nothing. With nothing, explain the current branch.

```sh
gh pr view <n> --json title,body,url,headRefName,baseRefName,author,additions,deletions,files
gh pr diff <n>
```

No PR exists yet? Use `git diff <base>...` against the target branch, and say in the file that the change is a branch, not a PR.

Ask the user only when two targets are equally likely. A PR number in the request is never ambiguous.

## 2. Read past the diff

A diff hunk shows what changed. It does not show why the change is correct. Before you write one word:

- Read each touched file whole, not just the hunks.
- Read the callers of every changed function or type.
- Read the tests that cover the changed code.
- Read the PR description and the linked issue, if there is one.

This reading does not go in the document. It is what makes each one-line caption correct instead of a restatement of the code above it.

## 3. Write the file

Write the same document to two places. The first is the archive. The second is a dated scratch copy that sorts by day and disappears on reboot.

Both names are built from the same three parts, so they always agree.

```sh
~/.robosplainer/<repo>/<number>-<slug>.md
/tmp/$(date +%Y-%m-%d)-robosplainer-<repo>-<number>.md
```

- `<repo>` is the repository name alone, from `gh repo view --json name`. Keep its capitalisation in the directory. Lower-case it in the `/tmp` name.
- `<number>` is the PR number by itself. No `#`, no `pr-` prefix.
- `<slug>` is 3 to 6 kebab-case words from the title of your document. It appears in the archive name only.
- No PR? Use `branch-<branch-name>` in place of `<number>`.

For PR #66 of `HeirloomKit`, that is:

```sh
~/.robosplainer/HeirloomKit/66-elevation-fill-picks-its-hue.md
/tmp/2026-08-17-robosplainer-heirloomkit-66.md
```

Create the directory first with `mkdir -p`. Never write inside the repository. Never open the file in a browser or a viewer.

Print the `~/.robosplainer` path as the last line of your chat reply. Put two or three bullets above it. Do not paste the document into the chat.

## 4. Structure

Three parts. The third one is usually absent.

### Title

One `#` heading, one sentence on what changed, then the PR link and the diff size.

### The opener — 2 to 3 sentences, no heading

Everything the reader needs before the code: what this part of the system does, and why the change was made. Two sentences. Three if the change repairs something, because then one sentence has to say what was broken.

There is no background section, no TL;DR, and no intuition section. The reader skips those. Fold what matters into these sentences and drop the rest.

### The walkthrough — the body of the document

Repeat this unit, 3 to 6 times, until the important parts of the change are covered:

1. A bold lead-in of 2 to 5 words. This is the skim anchor.
2. A code block, cited with `path.swift:42`.
3. One or two sentences on what it does and why. Never more.

Order the units by what matters most, not by file path and not by diff order. Stop when the change is covered. Four units that carry the change beat eight that inventory it.

### Risks — only if the reader must act today

Include this part only when you found something that should make the reader stop and open a ticket: data loss, a silent failure, a breaking change, a security hole.

Nothing that severe? Omit the section. Do not write "no risks identified". Do not list nits, style, or missing tests. Most documents end at the walkthrough.

## 5. Budget

| Item | Limit |
|---|---|
| Opener | 3 sentences |
| Walkthrough units | 3–6 |
| Lines per code block | 12 |
| Sentences per caption | 2 |
| Prose, whole document | 350 words |
| Risks | 0–2 bullets |

Code does not count against the 350 words. Prose does. Over budget means cut a unit, not compress every sentence into a fragment.

## 6. Code blocks

The code blocks carry the document, so choose them with care.

- Show the changed lines, plus just enough context to read them.
- Cut function bodies, imports, and boilerplate. Use `…` for what you removed.
- Where the shape changed, use one block with `// before` and `// after` comments rather than two separate blocks.
- Quote the code as it is. Never rewrite it to read better.
- Fence every block and tag the language.
- Copy code as literal characters. Never emit `&lt;`, `&gt;`, or `&amp;` — write `<`, `>`, and `&`.

A table replaces a code block when the point is a set of cases: the same input before and after, or a sequence of states. Use a mermaid `flowchart` only when a value crosses three or more components. Most documents have no diagram at all. Never draw ASCII art or box drawings.

## 7. Voice

Write plainly, in the discipline of ASD-STE100.

- Use active voice and simple tenses.
- One idea per sentence. 25 words maximum.
- Use plain words: "use" not "leverage", "before" not "prior to".
- Use the same word for the same thing every time. A "flag" stays a "flag".
- Cut hedges. Write the fact, or write that you do not know.
- Technical names, paths, commands, and API names are exempt. Keep them exact.
- Write one long line per paragraph and per list item. Never hard-wrap prose at a column width — the reader's viewer wraps it.

`references/example.md` is a real output of this skill. Read it when the shape is unclear.

## Common mistakes

| Mistake | Fix |
|---|---|
| The explanation stays in the chat | Write the file. The chat gets 2–3 bullets and the path |
| A background section before the code | Two sentences, then the first code block |
| 2000 words for a 90-line diff | Apply the budget |
| Prose describing code the reader cannot see | Every claim about code sits next to that code |
| A caption that reads the code aloud | Say what it does and why. The reader can read `if` |
| Eight units inventorying every file | 3–6 units, ordered by what matters |
| "No risks identified" | Omit the section |
| A nit list at the end | Only drop-everything items. Otherwise nothing |
| ASCII arrows and box drawings | Table, mermaid, or nothing |
| `&lt;appID&gt;` in a code block | Literal characters only |
