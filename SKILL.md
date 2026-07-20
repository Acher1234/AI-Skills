---
name: ai-skills
description: >-
  Install or update AI-Skills into Cursor, Claude, Hermes, or OpenClaw. Clone/pull
  this repo into ~/.ai-skills (shared library), auto-detect the tool via TERMINAL_ENV
  / CLAUDECODE, ask target + scope, then copy (cp) chosen SKILL.md files. Any external
  git skill repo is cloned ONCE into ~/.ai-skills/ext via `install.sh fetch`; each skill
  installs its OWN deps on first run via `install.sh pip init` / `npm init` into a shared
  env (~/.ai-skills/.venv). Use when installing/refreshing skills, adding a skill from a
  git URL, sharing a python/npm env across projects, or running /ai-skills.
disable-model-invocation: true
---

# AI-Skills — the skill installer (Cursor / Claude / Hermes / OpenClaw)

This skill **is** the installer. It manages a **single shared library and a single
shared Python/npm environment** on the machine, then registers chosen skills into
any tool. Nothing is re-cloned or re-installed per project.

> **Targets:** `cursor`, `claude`, `hermes`, `openclaw`.
> **`claude` and `openclaw` are in progress** — their paths (see the
> [Targets table](#targets--scopes)) are working defaults and may still change.

## Core idea — shared library, shared env

Heavy things live **once** under `$AI_SKILLS_HOME` (default `~/.ai-skills`); each
tool only gets the lightweight `SKILL.md`.

```
~/.ai-skills/            shared library root (this repo, or $AI_SKILLS_HOME)
├── install.sh           this installer's helper script
├── common/              shared helpers — skill_home (lib shared + .env per workspace)
├── ext/<repo>/          external git skills, cloned ONCE (shared)
├── .venv/               shared Python venv — every python skill reuses it
├── AI-PRO-SKILLS/       pro submodule (coolify, zscaler, sf, jira, …)
└── <built-in skills>/   c411-torrent, qbittorrent-scripts, tuya-skill, …

                         node deps via `./install.sh npm init` (shared skill dir)

        │ register = cp ONLY SKILL.md ; put .env/config next to the registered skill ↓
~/.cursor/skills/<name>/{SKILL.md,.env}   (or ./.cursor/skills/<name>/ per project)
```

**Hybrid model:** CLI code is **shared**; credentials (`.env` / `config.json` / tokens)
are **per workspace**, resolved by [`common/skill_home.py`](common/skill_home.py)
(`SkillHome("c411-torrent")`, `SkillHome("tuya")`, …).

## Hybrid model — shared CLI, local secrets (`common/skill_home`)

Do **not** put secrets in `~/.ai-skills/<skill>/` (that would force one account for every
project). Do **not** copy the full skill tree into Cursor/Hermes for Python CLIs that follow
this pattern.

| Layer | Location | Shared? |
|-------|----------|---------|
| CLI / Python code | `~/.ai-skills/<skill>/` | **Yes** — one copy on the machine |
| Python deps | `~/.ai-skills/.venv` | **Yes** |
| Registered skill | `$DEST/<skill>/SKILL.md` only | Lightweight discovery copy |
| Credentials | `$DEST/<skill>/.env` (or `config.json`) | **No** — per workspace / profile |

**Credential resolution** (`SkillHome("<name>").env_path()`), in order:

1. `<NAME>_ENV_PATH` override (e.g. `C411_TORRENT_ENV_PATH`)
2. Project: `./.cursor/skills/<name>/.env` (also `.claude` / `.openclaw` / Hermes)
3. Workspace root: `./.env`
4. Global: `~/.cursor/skills/<name>/.env` (and Hermes / Claude / OpenClaw equivalents)
5. Tool-level fallback: `~/.cursor/.env`, `$HERMES_HOME/.env`, …

Skills that keep their own `config.json` follow the same per-workspace placement (next to
the registered `SKILL.md`); use `SkillHome(...).credential_path("config.json")` to resolve it.

**Authoring a skill that uses it:**

```python
# <skill>/_skill_home.py — thin wrapper
from pathlib import Path
import sys
_LIB = Path(__file__).resolve().parent
sys.path.insert(0, str(_LIB.parent))
from common.skill_home import SkillHome
_home = SkillHome("my-skill", library_home=_LIB)
env_path = _home.env_path()
```

```bash
# Register (Cursor project = different account per repo)
mkdir -p ./.cursor/skills/my-skill
cp ~/.ai-skills/my-skill/SKILL.md ./.cursor/skills/my-skill/SKILL.md
cp ~/.ai-skills/my-skill/.env.example ./.cursor/skills/my-skill/.env
# edit ./.cursor/skills/my-skill/.env

# Run from the shared library
cd ~/.ai-skills/my-skill
~/.ai-skills/.venv/bin/python cli.py test
```

Agent authors: Cursor rule [`.cursor/rules/ai-skills-hybrid.mdc`](.cursor/rules/ai-skills-hybrid.mdc)
encodes the same conventions when editing skills in this repo.

## Helper script — [`install.sh`](install.sh) (3 commands)

`~/.ai-skills/install.sh` has **exactly three** commands. They only manage the
**shared** cache/env — nothing per project:

```bash
./install.sh fetch <git-url> [name]   # clone/pull an external skill repo → ~/.ai-skills/ext/<name>
./install.sh pip init [dir]           # create/reuse the shared venv, install <dir> deps into it
./install.sh npm init [dir]           # install <dir> node deps (shared skill dir)
```

- **Registering** a skill into a tool is a plain `cp` (see the [Copy map](#copy-map-reference)).
- **Dependencies are each skill's job.** A skill calls `install.sh pip init .` /
  `install.sh npm init .` from its own folder on **first run** — installed once into
  the shared venv (`~/.ai-skills/.venv`), reused across projects. The installer never
  bulk-installs anything.

## Targets & scopes

| Tool | Scope | Skills directory |
|------|-------|------------------|
| **cursor** | `global` | `~/.cursor/skills/<name>/` |
| **cursor** | `project` | `./.cursor/skills/<name>/` |
| **claude** | `global` | `~/.claude/skills/<name>/` *(WIP)* |
| **claude** | `project` | `./.claude/skills/<name>/` *(WIP)* |
| **hermes** | `all` | `~/.hermes/skills/<name>/` |
| **hermes** | `profile` | `${HERMES_HOME}/skills/<name>/` |
| **openclaw** | `global` | `~/.openclaw/skills/<name>/` *(WIP)* |
| **openclaw** | `project` | `./.openclaw/skills/<name>/` *(WIP)* |

## Critical — ask the user first

**Do not copy every skill blindly.** After clone/pull (and submodule update),
resolve the tool (auto-detect first), then ask in this order:

### 0) Auto-detect the tool

Check the environment:

- **`TERMINAL_ENV` set (non-empty)** → **Hermes**. Skip to the Hermes profile scope (step 2).
- **`CLAUDECODE`/`CLAUDE_CODE` set, or `~/.claude` exists** (and no `TERMINAL_ENV`) → likely **Claude**.
- **Otherwise** → assume **Cursor**.
- **OpenClaw** is chosen explicitly (WIP). Only fall back to the tool question (step 1)
  if detection is ambiguous or the user wants **several** tools.

### 1) Target tool (only if not auto-detected)

> Install skills for **Cursor**, **Claude**, **Hermes**, and/or **OpenClaw**? (one or several)

### 2) Scope

- **Cursor / Claude / OpenClaw** → **global** (`~/.<tool>/skills`) or **this project** (`./.<tool>/skills`).
- **Hermes** → **all profiles** (`~/.hermes/skills`) or **this profile** (`$HERMES_HOME/skills`; resolve `HERMES_HOME`, ask if unset).

### 3) Which skills

Ask for any of:
- **built-in** skills from AI-Skills (catalog below),
- **pro** skills — read `AI-PRO-SKILLS/SKILL.md` for its catalog (don't list them here),
- an **external git URL** (any skill repo), or
- a **local path** to a skill folder.

Always also install the meta skill `ai-skills` (this file) into every chosen target.

### Skills catalog (show this to the user)

**Root (AI-Skills)**

| # | Name | Folder | What it does |
|---|------|--------|--------------|
| 1 | `c411-torrent` | `c411-torrent/` | C411 Torznab search / download |
| 2 | `qbittorrent` | `qbittorrent-scripts/` | qBittorrent WebUI |
| 3 | `tuya` | `tuya-skill/` | Tuya IoT cloud + LAN |
| 4 | `pc-daily-report` | `pc-daily-report/` | Daily Linux host report |

**Submodule `AI-PRO-SKILLS/`** (`git submodule update --init --recursive`)

Do **not** enumerate the pro skills here — the submodule is its own installer with its
own catalog. To offer pro skills, **read `AI-PRO-SKILLS/SKILL.md`** (the `ai-pro-skills`
meta-skill) and use the catalog listed there. It stays in sync as pro skills are added
or renamed, so this file never needs updating for them.

**External** — any git URL (cloned into `~/.ai-skills/ext/<name>`).

## Flow (do this)

```
# 0) Shared library — clone/pull into ~/.ai-skills (rename to .ai-skills)
If ~/.ai-skills exists:  cd ~/.ai-skills && git pull && git submodule update --init --recursive
Else:                    git clone --recurse-submodules https://github.com/Acher1234/AI-Skills.git ~/.ai-skills

# 1) Detect tool: $TERMINAL_ENV set → Hermes; $CLAUDECODE or ~/.claude → Claude; else Cursor.
#    OpenClaw only when explicitly asked. Ask if ambiguous / several tools wanted.
# 2) Ask scope (see table). For Hermes-profile, resolve HERMES_HOME.
# 3) Ask what to install: built-in name(s), external git URL, or local path. Do not copy all by default.

# 4a) EXTERNAL git skill → fetch it into the shared cache (clone once):
SRC=$(cd ~/.ai-skills && ./install.sh fetch <git-url> [name])
# 4b) BUILT-IN or LOCAL skill: SRC is its folder under ~/.ai-skills/…

# 5) Register = copy ONLY the SKILL.md into each chosen tool/scope (+ always ai-skills).
#    Resolve DEST from the Targets table, then (see Copy map):
mkdir -p "$DEST/<name>" && cp "$SRC/SKILL.md" "$DEST/<name>/SKILL.md"
mkdir -p "$DEST/ai-skills" && cp ~/.ai-skills/SKILL.md "$DEST/ai-skills/SKILL.md"

# 6) Reload Cursor / Claude / OpenClaw, or reload the Hermes agent.
# NOTE: the installer does NOT install deps. Each skill runs `./install.sh pip init .`
#       (or `npm init .`) itself on first run → shared venv ~/.ai-skills/.venv.
```

## Examples

```bash
cd ~/.ai-skills

# Built-in → Hermes (all profiles): register = cp the SKILL.md
mkdir -p ~/.hermes/skills/{qbittorrent,ai-skills}
cp ~/.ai-skills/qbittorrent-scripts/SKILL.md ~/.hermes/skills/qbittorrent/SKILL.md
cp ~/.ai-skills/SKILL.md                     ~/.hermes/skills/ai-skills/SKILL.md

# External git skill → Claude (global): fetch once, then cp the SKILL.md
SRC=$(./install.sh fetch https://github.com/some/cool-skill.git cool-skill)
mkdir -p ~/.claude/skills/cool-skill
cp "$SRC/SKILL.md" ~/.claude/skills/cool-skill/SKILL.md
# same skill also into Cursor (this project) — no re-clone
mkdir -p ./.cursor/skills/cool-skill
cp "$SRC/SKILL.md" ./.cursor/skills/cool-skill/SKILL.md

# The cool-skill installs ITS OWN deps on first run (shared venv):
./install.sh pip init "$SRC"     # or, from inside the skill: ./install.sh pip init .
```

## Agent checklist

1. Clone/pull `~/.ai-skills` + `git submodule update --init --recursive`.
2. Detect tool (`$TERMINAL_ENV` → Hermes; `$CLAUDECODE`/`~/.claude` → Claude; else Cursor). Ask if ambiguous / several.
3. Ask scope; resolve `HERMES_HOME` for Hermes-profile.
4. Ask what to install (built-in / external git URL / local path). Don't copy all by default.
5. External repo → `./install.sh fetch <url> [name]` (clone once into the shared cache).
6. **Register = `cp` the `SKILL.md`** into `$DEST/<name>/` for each chosen target (see Copy map); always also copy `ai-skills`.
7. **Dependencies are each skill's responsibility** — the skill runs `./install.sh pip init .` / `npm init .` on first run into the shared venv (`~/.ai-skills/.venv`), once per machine. The installer never bulk-installs deps.
8. **Pro skills (`AI-PRO-SKILLS/*`)** → don't handle them here; **read `AI-PRO-SKILLS/SKILL.md`** and follow its catalog / copy map / special cases (e.g. `sf` → `/sf`, `jira` → `/jira`, `agent-browser` npm install, `google-workspace` / `powerpoint` full-folder copy).
9. Remind: reload the tool(s).

## Copy map (reference)

Pick `DEST` from the [Targets table](#targets--scopes): `~/.cursor/skills`, `./.cursor/skills`,
`~/.claude/skills`, `./.claude/skills`, `~/.hermes/skills`, `$HERMES_HOME/skills`,
`~/.openclaw/skills`, or `./.openclaw/skills`. Then `mkdir -p "$DEST/<name>"` and `cp`:

| Source (`~/.ai-skills/…`) | Target |
|---------------------------|--------|
| `SKILL.md` | `$DEST/ai-skills/SKILL.md` |
| `c411-torrent/SKILL.md` | `$DEST/c411-torrent/SKILL.md` |
| `qbittorrent-scripts/SKILL.md` | `$DEST/qbittorrent/SKILL.md` |
| `tuya-skill/SKILL.md` | `$DEST/tuya/SKILL.md` |
| `pc-daily-report/SKILL.md` | `$DEST/pc-daily-report/SKILL.md` |
| **pro skills** (`AI-PRO-SKILLS/*`) | see `AI-PRO-SKILLS/SKILL.md` for its own copy map — don't hardcode them here |
| `ext/<name>/SKILL.md` | `$DEST/<name>/SKILL.md` |

## After install

- CLI working dirs stay under `~/.ai-skills/<skill-dir>` (or `~/.ai-skills/ext/<name>`).
- Python skills should use the shared interpreter `~/.ai-skills/.venv/bin/python`.
- For **sf**: after registering the meta-skill, run `/sf` — SF trees live in `~/.ai-skills/sf-skills/skills/{skills_dir}`.
- Re-run `/ai-skills` anytime to **pull + ask targets/skills again + re-register**.

## Notes

- Override the shared library location with `AI_SKILLS_HOME` (default `~/.ai-skills`).
- Never write into `~/.cursor/skills-cursor/` (Cursor built-ins only).
- Register with `cp` (copy, not move). Prefer **per-skill** credentials next to the registered
  skill (`$DEST/<name>/.env` or `config.json`) so each workspace can differ; tool-level `.env`
  (`~/.cursor/.env`, `$HERMES_HOME/.env`, …) remains a fallback. Use
  [`common/skill_home.py`](common/skill_home.py) from Python CLIs.
- Claude / OpenClaw support is **in progress** — adjust their paths in the Targets table if needed.
- Repo: [Acher1234/AI-Skills](https://github.com/Acher1234/AI-Skills.git) — submodule: [AI-PRO-SKILLS](https://github.com/Acher1234/AI-PRO-SKILLS.git)
