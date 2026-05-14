# Heirloom Logic — Agent Skills

Agent skills published by [Heirloom Logic LLC](https://heirloomlogic.com) for Claude Code, Codex, Cursor, Gemini CLI, and other agent runtimes.

## Skills

| Skill | What it does | Upstream |
|---|---|---|
| [`swidux-ref`](swidux-ref/SKILL.md) | Architecture rules and copy-pasteable code templates for [Swidux](https://github.com/heirloomlogic/Swidux), a Redux-style state-management library for SwiftUI. | [heirloomlogic/Swidux](https://github.com/heirloomlogic/Swidux) |
| [`tightlip-ref`](tightlip-ref/SKILL.md) | Setup and code patterns for [Tightlip](https://github.com/heirloomlogic/Tightlip), a SwiftPM build-tool plugin that generates a `Secrets` enum from environment variables at build time. | [heirloomlogic/Tightlip](https://github.com/heirloomlogic/Tightlip) |
| [`persnicket-ref`](persnicket-ref/SKILL.md) | Setup and CI wiring for [Persnicket](https://github.com/heirloomlogic/Persnicket), a lightweight `swift-format` wrapper for Swift packages. | [heirloomlogic/Persnicket](https://github.com/heirloomlogic/Persnicket) |

## Install

**GitHub CLI** (recommended — multi-agent, requires `gh` ≥ v2.90.0):

```bash
gh skill install heirloomlogic/skills swidux-ref --agent claude-code --scope user
```

- `--scope user` installs to `~/.claude/skills/swidux-ref/`.
- `--scope project` installs to `<cwd>/.claude/skills/swidux-ref/` so a team can commit it.
- Other agents: `--agent codex`, `--agent cursor`, `--agent gemini-cli`, etc. `gh skill install --help` shows the full list.

**skills.sh:**

```bash
npx skillsadd heirloomlogic/skills
```

Indexes this repo. Each skill folder becomes individually addressable on [skills.sh](https://skills.sh).

## Updating

Re-run whichever install command you used originally.

## Versioning

Skills currently track `main` — there are no tagged releases yet. Versioned releases are planned; once we cut them, `gh skill install heirloomlogic/skills <skill>@<tag>` will resolve to a specific commit per skill.

## License

MIT. See [LICENSE](LICENSE).
