# Heirloom Logic — Agent Skills

Agent skills published by [Heirloom Logic LLC](https://heirloomlogic.com) for Claude Code, Codex, Cursor, Gemini CLI, and other agent runtimes.

## Skills

| Skill | What it does | Upstream |
|---|---|---|
| [`swidux-ref`](swidux-ref/SKILL.md) | Architecture rules and copy-pasteable code templates for [Swidux](https://github.com/heirloomlogic/Swidux), a Redux-style state-management library for SwiftUI. | [heirloomlogic/Swidux](https://github.com/heirloomlogic/Swidux) |
| [`tightlip-ref`](tightlip-ref/SKILL.md) | Setup and code patterns for [Tightlip](https://github.com/heirloomlogic/Tightlip), a SwiftPM build-tool plugin that generates a `Secrets` enum from environment variables at build time. | [heirloomlogic/Tightlip](https://github.com/heirloomlogic/Tightlip) |

## Install

**GitHub CLI** (recommended — supports `@version` pinning, multi-agent, requires `gh` ≥ v2.90.0):

```bash
gh skill install heirloomlogic/skills swidux-ref --agent claude-code --scope user
```

- `--scope user` installs to `~/.claude/skills/swidux-ref/`.
- `--scope project` installs to `<cwd>/.claude/skills/swidux-ref/` so a team can commit it.
- Pin a version with `swidux-ref@v1.2.3`. List tags with `git ls-remote --tags https://github.com/heirloomlogic/skills`.
- Other agents: `--agent codex`, `--agent cursor`, `--agent gemini-cli`, etc. `gh skill install --help` shows the full list.

**skills.sh:**

```bash
npx skillsadd heirloomlogic/skills
```

Indexes this repo. Each skill folder becomes individually addressable on [skills.sh](https://skills.sh).

**Manual fallback** (no `gh`, no `npx`):

```bash
# Claude Code (default)
mkdir -p .claude/skills && \
  curl -fsSL https://github.com/heirloomlogic/skills/archive/refs/heads/main.tar.gz | \
  tar -xz --strip-components=2 -C .claude/skills skills-main/swidux-ref

# Codex / Cursor / Gemini CLI / etc. (.agents/skills/ convention)
mkdir -p .agents/skills && \
  curl -fsSL https://github.com/heirloomlogic/skills/archive/refs/heads/main.tar.gz | \
  tar -xz --strip-components=2 -C .agents/skills skills-main/swidux-ref
```

`tar` overwrites by default, so re-running either command updates the skill in place. Swap `.claude/skills` / `.agents/skills` for `~/.claude/skills` etc. for a user-wide install.

## Updating

Re-run whichever install command you used originally. To lock to a known version, pass `swidux-ref@vX.Y.Z` (gh) or replace `main` with the tag name (curl).

## Versioning

Each skill is versioned independently with per-skill tags:

```
swidux-ref@v1.0.0
swidux-ref@v1.1.0
…
```

This lets `gh skill install heirloomlogic/skills <skill>@<tag>` resolve to a specific skill commit without coupling unrelated skills.

## Contributing a new skill

Open a PR adding a `<skill-name>/` folder with a `SKILL.md` and any reference files. Skill front-matter follows the [Claude Code skills format](https://code.claude.com/docs/en/skills) (the same format works for the GitHub CLI skill manager and skills.sh).

## License

MIT. See [LICENSE](LICENSE).
