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

**GitHub CLI** (recommended; multi-agent, needs `gh` ≥ v2.90.0):

```bash
gh skill install heirloomlogic/skills swidux-ref --agent claude-code --scope user
```

- `--scope user` installs to `~/.claude/skills/swidux-ref/`.
- `--scope project` installs to `<cwd>/.claude/skills/swidux-ref/` so a team can commit it.
- Other agents: `--agent codex`, `--agent cursor`, `--agent gemini-cli`, etc. `gh skill install --help` shows the full list.

**All skills at once:** there is no single-command "install all". `gh skill install` takes one skill name per call, so loop over them:

```bash
for s in dehumanizer persnicket-ref swidux-ref tightlip-ref; do
  gh skill install heirloomlogic/skills "$s" --agent claude-code --scope user
  gh skill install heirloomlogic/skills "$s" --agent codex       --scope user
done
```

`--agent claude-code` installs to `~/.claude/skills/`. `--agent codex` installs to the shared `~/.agents/skills/` directory (Codex, Cursor, Gemini CLI, and other agents read from there). Run both lines to cover both locations.

## Updating

Re-run the install command — it overwrites the skill in place:

```bash
for s in dehumanizer persnicket-ref swidux-ref tightlip-ref; do
  gh skill install heirloomlogic/skills "$s" --agent claude-code --scope user
done
```

(`gh skill update --all` also works, but only for skills it installed itself —
it can't update skills added by `npx` or copied in manually.)

## Versioning

Skills currently track `main` — there are no tagged releases yet. Versioned releases are planned; once we cut them, `gh skill install heirloomlogic/skills <skill>@<tag>` will resolve to a specific commit per skill.

## License

MIT. See [LICENSE](LICENSE).
