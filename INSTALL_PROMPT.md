# AI-Skills — install prompt

Copy-paste the block below into a fresh Cursor / Hermes agent chat. It installs the
**`ai-skills`** meta-skill (the installer itself) into your **global** skills folder,
so that `/ai-skills` becomes available everywhere.

- Repo: <https://github.com/Acher1234/AI-Skills.git>
- Shared library: `~/.ai-skills`
- Meta-skill installed: `ai-skills` → `<global skills dir>/ai-skills/SKILL.md`

---

## Prompt (paste this)

```
Install the "ai-skills" meta-skill into my GLOBAL skills folder.

0. Detect the platform: check $TERMINAL_ENV.
   - non-empty  -> Hermes  -> install to ~/.hermes/skills/ai-skills/SKILL.md
   - empty/unset -> Cursor -> install to ~/.cursor/skills/ai-skills/SKILL.md
   If ambiguous, ask me "Cursor global or Hermes global?".

1. Clone or update the shared library:
     REPO=https://github.com/Acher1234/AI-Skills.git
     LIB=~/.ai-skills
     if [ -d "$LIB/.git" ]; then git -C "$LIB" pull --ff-only; else git clone "$REPO" "$LIB"; fi

2. Register ONLY the meta-skill's SKILL.md into the chosen global folder:
     # Cursor global:
     mkdir -p ~/.cursor/skills/ai-skills && cp "$LIB/SKILL.md" ~/.cursor/skills/ai-skills/SKILL.md
     # OR Hermes global:
     mkdir -p ~/.hermes/skills/ai-skills && cp "$LIB/SKILL.md" ~/.hermes/skills/ai-skills/SKILL.md

3. Confirm the file exists, then tell me to reload Cursor (or restart the Hermes agent)
   and run /ai-skills to install any other skill.

Do NOT copy other skills yet — just the installer. /ai-skills handles the rest.
```

---

## One-liners (if you prefer to run it yourself)

**Cursor — global** (`~/.cursor/skills/`):

```bash
REPO=https://github.com/Acher1234/AI-Skills.git; LIB=~/.ai-skills
[ -d "$LIB/.git" ] && git -C "$LIB" pull --ff-only || git clone "$REPO" "$LIB"
mkdir -p ~/.cursor/skills/ai-skills && cp "$LIB/SKILL.md" ~/.cursor/skills/ai-skills/SKILL.md
```

**Hermes — global** (`~/.hermes/skills/`):

```bash
REPO=https://github.com/Acher1234/AI-Skills.git; LIB=~/.ai-skills
[ -d "$LIB/.git" ] && git -C "$LIB" pull --ff-only || git clone "$REPO" "$LIB"
mkdir -p ~/.hermes/skills/ai-skills && cp "$LIB/SKILL.md" ~/.hermes/skills/ai-skills/SKILL.md
```

Then reload Cursor (or restart the Hermes agent) and run `/ai-skills` to install/refresh
the rest of the catalog.
