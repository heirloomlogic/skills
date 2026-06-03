# Heirloom Logic — Agent Skills

Agent skills published by [Heirloom Logic LLC](https://heirloomlogic.com) for Claude Code, Codex, Cursor, Gemini CLI, and other agent runtimes.

## Skills

| Skill | What it does | Upstream |
|---|---|---|
| [`swidux-ref`](swidux-ref/SKILL.md) | Architecture rules and copy-pasteable code templates for [Swidux](https://github.com/heirloomlogic/Swidux), a Redux-style state-management library for SwiftUI. | [heirloomlogic/Swidux](https://github.com/heirloomlogic/Swidux) |
| [`tightlip-ref`](tightlip-ref/SKILL.md) | Setup and code patterns for [Tightlip](https://github.com/heirloomlogic/Tightlip), a SwiftPM build-tool plugin that generates a `Secrets` enum from environment variables at build time. | [heirloomlogic/Tightlip](https://github.com/heirloomlogic/Tightlip) |
| [`persnicket-ref`](persnicket-ref/SKILL.md) | Setup and CI wiring for [Persnicket](https://github.com/heirloomlogic/Persnicket), a lightweight `swift-format` wrapper for Swift packages. | [heirloomlogic/Persnicket](https://github.com/heirloomlogic/Persnicket) |
| [`dehumanizer`](dehumanizer/SKILL.md) | Strips AI-writing tells (slop, ChatGPT-isms, em-dash closers, sycophancy) and rewrites prose in a deadpan, economical voice. | — |

## Install

Requires `gh` ≥ v2.90.0 and an authenticated GitHub account with read access to this repo.

```bash
# Claude Code
gh skill install heirloomlogic/skills dehumanizer --agent claude-code --force --scope user
gh skill install heirloomlogic/skills persnicket-ref --agent claude-code --force --scope user
gh skill install heirloomlogic/skills swidux-ref --agent claude-code --force --scope user
gh skill install heirloomlogic/skills tightlip-ref --agent claude-code --force --scope user

# Codex
gh skill install heirloomlogic/skills dehumanizer --agent codex --force --scope user
gh skill install heirloomlogic/skills persnicket-ref --agent codex --force --scope user
gh skill install heirloomlogic/skills swidux-ref --agent codex --force --scope user
gh skill install heirloomlogic/skills tightlip-ref --agent codex --force --scope user
```

For more options please see the [gh skill install](https://cli.github.com/manual/gh_skill_install) documentation.

## Updating

Re-run the install command — it overwrites the skill in place.

## Versioning

Skills currently track `main` — there are no tagged releases yet. Versioned releases are planned; once we cut them, `gh skill install heirloomlogic/skills <skill>@<tag>` will resolve to a specific commit per skill.

## License

MIT. See [LICENSE](LICENSE).
