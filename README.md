# Heirloom Logic — Agent Skills

Agent skills published by [Heirloom Logic LLC](https://heirloomlogic.com) for Claude Code, Codex, Cursor, Gemini CLI, and other agent runtimes.

## Skills

| Skill | What it does | Upstream |
|---|---|---|
| [`ackshully`](ackshully/SKILL.md) | Explains one thing — a pull request, a branch, a repository, a document, a book chapter, a subject — at three depths: a two-sentence opener, a longer summary, then detail sections for whatever the reader still needs. The opener and the summary are written for someone who does not already know the subject; the detail sections are where the jargon starts. Archives each report under `~/.ackshully/<context>/`. | — |
| [`dehumanizer`](dehumanizer/SKILL.md) | Strips AI-writing tells (slop, ChatGPT-isms, em-dash closers, teaser headings, sycophancy) and rewrites prose in a concise, economical voice. | — |
| [`persnicket-ref`](persnicket-ref/SKILL.md) | Setup and CI wiring for [Persnicket](https://github.com/heirloomlogic/Persnicket), a lightweight `swift-format` wrapper for Swift packages. | [heirloomlogic/Persnicket](https://github.com/heirloomlogic/Persnicket) |
| [`swidux-ref`](swidux-ref/SKILL.md) | Architecture rules and copy-pasteable code templates for [Swidux](https://github.com/heirloomlogic/Swidux), a Redux-style state-management library for SwiftUI. | [heirloomlogic/Swidux](https://github.com/heirloomlogic/Swidux) |
| [`tightlip-ref`](tightlip-ref/SKILL.md) | Setup and code patterns for [Tightlip](https://github.com/heirloomlogic/Tightlip), a SwiftPM build-tool plugin that generates a `Secrets` enum from environment variables at build time. | [heirloomlogic/Tightlip](https://github.com/heirloomlogic/Tightlip) |
| [`tightwad`](tightwad/SKILL.md) | Audits one repo's GitHub Actions workflows, measures what CI costs in billed minutes from real job durations, tightens it, brings actions current and pinned, hardens permissions, and opens a PR that leads with the number. Its `ramen` mode parks every runner above 1x for accounts that cannot pay 10x at all. | — |

## Install

Requires `gh` ≥ v2.90.0 and an authenticated GitHub account with read access to this repo.

```bash
# Claude Code
gh skill install heirloomlogic/skills ackshully --agent claude-code --force --scope user --upstream
gh skill install heirloomlogic/skills dehumanizer --agent claude-code --force --scope user --upstream
gh skill install heirloomlogic/skills persnicket-ref --agent claude-code --force --scope user --upstream
gh skill install heirloomlogic/skills swidux-ref --agent claude-code --force --scope user --upstream
gh skill install heirloomlogic/skills tightlip-ref --agent claude-code --force --scope user --upstream
gh skill install heirloomlogic/skills tightwad --agent claude-code --force --scope user --upstream

# Codex
gh skill install heirloomlogic/skills ackshully --agent codex --force --scope user --upstream
gh skill install heirloomlogic/skills dehumanizer --agent codex --force --scope user --upstream
gh skill install heirloomlogic/skills persnicket-ref --agent codex --force --scope user --upstream
gh skill install heirloomlogic/skills swidux-ref --agent codex --force --scope user --upstream
gh skill install heirloomlogic/skills tightlip-ref --agent codex --force --scope user --upstream
gh skill install heirloomlogic/skills tightwad --agent codex --force --scope user --upstream
```

For more options please see the [gh skill install](https://cli.github.com/manual/gh_skill_install) documentation.

## Updating

Re-run the install command — it overwrites the skill in place.

## Versioning

Skills currently track `main` — there are no tagged releases yet. Versioned releases are planned; once we cut them, `gh skill install heirloomlogic/skills <skill>@<tag>` will resolve to a specific commit per skill.

## License

MIT. See [LICENSE](LICENSE).
