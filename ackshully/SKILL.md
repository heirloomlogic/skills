---
name: ackshully
description: >-
  Use when someone wants something explained so they actually understand it —
  "explain this PR", "what does this branch do", "what's going on in King Lear",
  "explain chapter 5 of Gravity's Rainbow", "summarise this repo", "what is this
  document", "walk me through this diff", or a bare PR number, URL, branch name,
  book title, or subject. Use with no argument to explain whatever the current
  directory, branch, or working document is about. Also use right after an agent
  opens a pull request, so the PR arrives explained. NOT for: writing the PR
  title or description itself, code review verdicts and approvals (use
  /code-review), security review, HTML or slide output, or answering a narrow
  factual question that needs one sentence.
metadata:
  version: "2.0.0"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Write
  - WebFetch
  - WebSearch
  - Skill
  - AskUserQuestion
---

# Ackshully

Explain one thing at three depths, in one markdown file, so the reader can stop at any depth and still be better off.

**The reader has two minutes and four interruptions.** They read the opener. If the opener earns it, they read the summary. If the summary earns it, they read the detail. Write for a reader who quits after each section.

**The reader is not an expert in this thing.** That is why they are reading. The title, the opener and the summary are written for someone who does not know the subject; the vocabulary of the subject starts at Level 3.

A long explanation of a small thing is a failure, not a bonus.

## 1. Resolve the target

**With an argument, the argument is the context.** "ackshully king lear" means explain King Lear. "ackshully gravity's rainbow chapter 5" means explain that chapter. It can also be a PR number, a PR URL, a branch, a repository, a file path, a Wikipedia URL, or a bare subject. Take it at face value and go.

**With no argument, read the environment.** Stop at the first one that fits:

1. A git branch with commits its base branch does not have → explain the change. Check for an open PR first with `gh pr view --json number`.
2. A git repository with no branch work → explain the repository.
3. A directory whose weight is one long markdown or text file → explain that document.
4. A file open in the conversation → explain that file.

Nothing fits? Ask, with the two candidates you found. Never guess between two equally likely targets. An argument in the request is never ambiguous.

## 2. Read past the surface

Before you write one word, do the reading the reader will not do. What that means depends on the target:

| Target | Read |
|---|---|
| Pull request or branch | The diff, then each touched file whole, the callers of every changed function, the tests that cover it, the PR body, the linked issue |
| Repository | The README, the entry points, the module layout, the test suite, the last twenty commits |
| Document or file | The whole thing, plus anything it links or cites that you can reach |
| Book, chapter, play, film, historical event, subject | What the text itself says, then the surrounding facts — dates, names, what came before and after. Fetch what you are not certain of |

State facts you verified. Where you could not verify something, either leave it out or mark it as unverified in one clause. Never invent a date, a name, a line number, or a quotation.

None of this reading goes in the document. It is what makes each sentence correct instead of a restatement of the thing above it.

## 3. Write the file

Write the same document to two places. The first is the archive. The second is a dated scratch copy that sorts by day and disappears on reboot.

```sh
~/.ackshully/<context>/<slug>.md
/tmp/$(date +%Y-%m-%d)-ackshully-<context>-<slug>.md
```

- `<context>` is the repository name from `gh repo view --json name` for code, keeping its capitalisation. For everything else it is a kebab-case slug of the subject: `king-lear`, `gravitys-rainbow`, `treaty-of-westphalia`. Lower-case it in the `/tmp` name.
- `<slug>` is `<number>-<3-to-6-kebab-words>` for a PR, `branch-<branch-name>` for a branch with no PR, `chapter-05` or `act-1` for a numbered part, and 3 to 6 kebab-case words from your title for everything else.

```sh
~/.ackshully/HeirloomKit/66-elevation-fill-picks-its-hue.md
~/.ackshully/king-lear/act-1.md
```

Create the directory first with `mkdir -p`. Never write inside the repository. Never open the file in a browser or a viewer.

Print the `~/.ackshully` path as the last line of your chat reply. Put two or three bullets above it. Do not paste the document into the chat.

## 4. Structure

Progressive disclosure. Each level is complete on its own and assumes the reader stopped at the one above.

### Title

One `#` heading, one sentence on what the thing is. Nothing else. No subtitle, no citation line, no summary paragraph under it.

Write it in ordinary words. No framework nouns, no API names, no term a reader outside the project would have to look up. The title is the one line everybody reads.

### Level 1 — the opener, 2 to 3 sentences, no heading

**The opener is the first prose in the document.** It sits immediately under the `#` heading, with nothing between them. If anything at all separates the heading from the opener, move that thing below the opener.

Say the largest true thing about the subject, in two or three sentences. Three only if the thing repairs or reverses something, because then one sentence has to say what it repairs.

Open on the subject itself. No catchphrase, no throat-clearing, no "This PR", no "This document". Nothing here or below it is arch, knowing, or pleased with itself — the document exists to be understood.

### The citation line

One line under the opener: the PR link and diff size, the author and edition, the URL, the repository and its default branch — whatever locates the thing. It goes here and not under the title, because the title's job is to hand the reader straight to the opener.

### Level 2 — `## The longer version`

The summary the reader gets if they have five minutes instead of one. Prose, 150 to 300 words. When they finish it they should understand the thing well enough to talk about it.

Cover the shape of the whole: what it does or what happens, why it is the way it is, and what it connects to. Do not restate the opener. Do not tease the sections below.

### Level 3 — detail sections, `##` each

Zero to five sections, each with a real heading naming what it covers. Add one only when the reader who already read Level 2 would still be missing something they need. What "need" means depends on the target:

| Target | A Level 3 section covers |
|---|---|
| Pull request or branch | One thing a reviewer must understand to approve it: a focused code block, cited `path.swift:42`, and one or two sentences on what it does and why |
| Repository | One flow end to end: how a request, a build, or a piece of data travels through the modules |
| Chapter of a novel or a play | Who is who, what changed for them, what recurs — the things a test on this chapter would ask |
| Chapter of a history book | The people, the dates, the causes, and how they connect to each other and to events the chapter does not mention |
| Subject or page | The claims that carry the weight, the numbers, and the parts that are genuinely disputed |

Order by what matters most, not by file path, page order, or diff order. Stop when the thing is covered. Four sections that carry it beat eight that inventory it.

### Optional last section — only if the reader must act or must not trust

Include a final section only when you found something that should make the reader stop: data loss, a silent failure, a breaking change, a security hole, or a claim in your own document that rests on a source you could not check. Name it for what it holds — `## Risks`, `## What is disputed`.

Nothing that severe? Omit it. Do not write "no risks identified". Do not list nits, style, or missing tests. Most documents end at Level 3.

## 5. Plain language in the opener and the summary

This section governs the title, the opener and `## The longer version`. Below those three, the vocabulary of the subject is fair game.

**Write for a smart friend who does not work on this project.** They have not read the diff, they do not know the framework, and they do not work in this field. They are not slow and you do not talk down to them. They just do not have the words yet, so you hand them the words. Simple is not vague: if the plain word would be wrong, use the real one and say what it means in the same breath. Never buy readability with an inaccuracy.

- No undefined domain term in the title or the opener. A sentence that needs one is the wrong sentence — say what the thing does instead of what it is called.
- In the summary, define each domain term in ordinary words the first time it appears, in the same sentence: "an anchor — the fixed point a view is pinned to". A term nobody defined is a term nobody read.
- Say what a thing is for before you say what it is called.
- 20 words per sentence here, against 25 for the rest of the document. One idea each.
- Take the common word over the specialist word when both are true. Expand every acronym on first use. Never use a verb that only this codebase uses.
- Paths, symbol names and quoted text stay exact wherever they appear, but they rarely belong this high up.
- Once the summary has introduced a term, the detail sections use it freely. That is what the detail sections are for.

## 6. Budget

Prose is every word outside a code block, a table, and a diagram.

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
| Last section | 0–3 bullets |

Over budget means cut a section, not compress every sentence into a fragment.

## 7. Code, tables, diagrams

- Show the changed or relevant lines, plus just enough context to read them. Cut function bodies, imports, and boilerplate, and mark the cut with `…`.
- Where a shape changed, use one block with `// before` and `// after` comments rather than two blocks.
- Quote code and text as they are. Never rewrite them to read better. Cite the line: `path.swift:42`, `Act 1, sc. 1`.
- Fence every block and tag the language. Quoted verse, dialogue, or any text whose line breaks matter goes in a `text` block, because a markdown blockquote joins the lines.
- Copy literal characters. Never emit `&lt;`, `&gt;`, or `&amp;` — write `<`, `>`, and `&`.
- A table replaces a block when the point is a set of cases: the same input before and after, a sequence of states, a cast of characters, a run of dates.
- Use a mermaid `flowchart` only when a value or a line of causation crosses three or more parts. Most documents have no diagram. Never draw ASCII art or box drawings.

## 8. Voice

**If the `dehumanizer` skill is installed, the whole draft goes through it before you write the file.** Required, not suggested, and not skipped because the draft already reads well. Its pattern catalog is the standard this document is held to. Apply these directly only when that skill is not installed:

- Active voice, simple tenses. One idea per sentence, 25 words maximum.
- Plain words: "use" not "leverage", "before" not "prior to".
- The same word for the same thing every time. A "flag" stays a "flag". A character keeps one name.
- Cut hedges. Write the fact, or write that you do not know it.
- No teaser headings, no "let's dive in", no closing paragraph that restates the document.
- Technical names, paths, commands, API names, and quoted text are exempt. Keep them exact.
- One long line per paragraph and per list item. Never hard-wrap prose at a column width — the reader's viewer wraps it.

`references/example-pull-request.md` and `references/example-chapter.md` are real outputs of this skill. Read one when the shape is unclear.

## Common mistakes

| Mistake | Fix |
|---|---|
| The explanation stays in the chat | Write the file. The chat gets 2–3 bullets and the path |
| A summary or citation line between the title and the opener | The opener is the first prose under the `#`. The citation goes below it |
| An arch or knowing voice anywhere in the document | The document is service. Nothing in it is pleased with itself |
| The opener names something the reader has never heard of | Say what it does. The name can wait for a detail section |
| The summary uses a term it never defined | Define it in ordinary words on first use, in the same sentence |
| The title is written in the codebase's vocabulary | Retitle it in words a stranger would use |
| Level 2 restates Level 1 in more words | Level 2 covers the whole shape. Level 1 covers the point |
| A detail section for every file or every page | Only what a reader who finished Level 2 still needs |
| Sections ordered by file path or page number | Ordered by what matters most |
| Prose describing code the reader cannot see | Every claim about code sits next to that code |
| A caption that reads the code aloud | Say what it does and why. The reader can read `if` |
| A date or a name you did not check | Verify it, cut it, or mark it unverified in one clause |
| "No risks identified" | Omit the section |
| ASCII arrows and box drawings | Table, mermaid, or nothing |
| `&lt;appID&gt;` in a code block | Literal characters only |
