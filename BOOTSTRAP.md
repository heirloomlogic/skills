# Bootstrapping `heirloomlogic/skills`

This directory (`.context/heirloomlogic-skills/`) is the staged content for the new public repo. It is **not** part of the Swidux repo — `.context/` is gitignored.

When you're ready, run the steps below to publish the repo and tag the initial release.

## 1. Create the public repo on GitHub

```bash
gh repo create heirloomlogic/skills \
  --public \
  --description "Agent skills published by Heirloom Logic LLC for Claude Code, Codex, Cursor, Gemini CLI, and other agent runtimes."
```

## 2. Push the staged content

From the Swidux workspace root:

```bash
TMP="$(mktemp -d)/skills"
cp -R .context/heirloomlogic-skills "$TMP"
cd "$TMP"
git init -b main
git add .
git commit -m "Initial commit: swidux-ref skill"
git remote add origin git@github.com:heirloomlogic/skills.git
git push -u origin main
```

(Adjust the `origin` URL if you use a custom SSH host alias, e.g. `git@heirloomlogic.github.com:heirloomlogic/skills.git`.)

## 3. Tag the initial release

```bash
cd "$TMP"
git tag swidux-ref@v1.0.0
git push origin swidux-ref@v1.0.0
```

`gh skill install heirloomlogic/skills swidux-ref@v1.0.0` now resolves.

## 4. Verify the install commands work

From any scratch directory **outside** `$TMP` and outside the Swidux repo:

```bash
# GitHub CLI
gh skill install heirloomlogic/skills swidux-ref --agent claude-code --scope user
ls ~/.claude/skills/swidux-ref/        # expect: SKILL.md  swidux-patterns.md

# skills.sh
mkdir /tmp/skillsadd-test && cd /tmp/skillsadd-test
npx skillsadd heirloomlogic/skills

# curl fallback
mkdir /tmp/curl-test && cd /tmp/curl-test
mkdir -p .claude/skills && \
  curl -fsSL https://github.com/heirloomlogic/skills/archive/refs/heads/main.tar.gz | \
  tar -xz --strip-components=2 -C .claude/skills skills-main/swidux-ref
ls .claude/skills/swidux-ref/          # expect: SKILL.md  swidux-patterns.md
```

If all three resolve, the Swidux branch's new README / AgentSkill.md install instructions are now correct.

## 5. Optional — list on skills.sh

skills.sh auto-discovers `<org>/skills` repos. No manual submission needed. The skill should appear in the directory within a few hours of the first push.

## 6. After verification — delete this staging directory

You can `rm -rf .context/heirloomlogic-skills/` once the public repo is live. It's gitignored, so it doesn't affect the Swidux repo, but it's no longer needed.
