---
name: ai-skills
description: >-
  Install or update AI-Skills: clone/pull into ~/.ai-skills, ask Cursor vs Hermes
  target (and Hermes profile vs all), list skills including AI-PRO-SKILLS submodule,
  then copy chosen SKILL.md files. Use when installing Cursor or Hermes skills,
  syncing AI-Skills, or pasting the install prompt from the README.
disable-model-invocation: true
---

# AI-Skills — install prompt (Cursor or Hermes)

Follow this prompt when installing or refreshing skills.

## Critical — ask the user first

**Do not copy every skill blindly.** After clone/pull (and submodule update), ask in this order:

### 1) Target platform

> Install skills for **Cursor**, **Hermes**, or **both**?

| Target | Skills directory |
|--------|------------------|
| **Cursor** | `~/.cursor/skills/<skill-name>/SKILL.md` |
| **Hermes — all profiles** | `~/.hermes/skills/<skill-name>/SKILL.md` |
| **Hermes — this profile only** | `${HERMES_HOME}/skills/<skill-name>/SKILL.md` |

### 2) If Hermes (or both): profile scope

> For Hermes, install for **all profiles** (`~/.hermes/skills/`) or **this profile only** (`$HERMES_HOME/skills/`)?

- If **this profile**: require `HERMES_HOME` to be set; if unset, ask the user for the profile path (or export it) before copying.
- If **all**: use `~/.hermes/skills/` (create if missing).

### 3) Which skills

**List all available skills** (root **and** submodule `AI-PRO-SKILLS`), then ask which to install.

Accept: `all`, names, numbers, `only root`, `only pro`.

Always also install the meta skill `ai-skills` (this file) into every chosen target.

### Skills catalog (show this to the user)

**Root (AI-Skills)**

| # | Name | Folder | What it does |
|---|------|--------|--------------|
| 1 | `c411-torrent` | `c411-torrent/` | C411 Torznab search / download |
| 2 | `qbittorrent` | `qbittorrent-scripts/` | qBittorrent WebUI |
| 3 | `tuya` | `tuya-skill/` | Tuya IoT cloud + LAN |
| 4 | `pc-daily-report` | `pc-daily-report/` | Daily Linux host report |

**Submodule `AI-PRO-SKILLS/`** (list these too — `git submodule update --init --recursive`)

| # | Name | Folder | What it does |
|---|------|--------|--------------|
| 5 | `coolify` | `AI-PRO-SKILLS/coolify/` | Coolify deploy / status / restart |
| 6 | `zscaler` | `AI-PRO-SKILLS/zscaler/` | Zscaler ZPA / ZIA / ZIdentity |
| 7 | `agent-browser` | `AI-PRO-SKILLS/agent-browser/` | Browser automation CLI |
| 8 | `sf` | `AI-PRO-SKILLS/SF/` | Salesforce skills installer ([forcedotcom/sf-skills](https://github.com/forcedotcom/sf-skills.git) → `~/.ai-skills/sf-skills`) |
| 9 | `google-workspace` | `AI-PRO-SKILLS/google-workspace/` | Gmail / Calendar / Drive / Docs / Sheets |
| 10 | `powerpoint` | `AI-PRO-SKILLS/powerpoint/` | Create / edit .pptx decks |

Always also install: `ai-skills` ← this file (`SKILL.md` at repo root).

Example questions:

> 1. Target: **Cursor** / **Hermes** / **both**?  
> 2. If Hermes: **all profiles** (`~/.hermes/skills`) or **this profile** (`$HERMES_HOME/skills`)?  
> 3. Skills: root (c411, qbittorrent, tuya, pc-daily-report) + pro submodule (coolify, zscaler, agent-browser, sf, google-workspace, powerpoint) — which? (`all` / names / numbers)

## Prompt (do this)

```
Take the project at url: https://github.com/Acher1234/AI-Skills.git
Install it on the computer under ~ but rename the folder to .ai-skills

If ~/.ai-skills already exists:
  - cd ~/.ai-skills
  - git pull
  - git submodule update --init --recursive
Else:
  - git clone --recurse-submodules https://github.com/Acher1234/AI-Skills.git ~/.ai-skills

IMPORTANT:
1. Ask Cursor vs Hermes vs both.
2. If Hermes: ask all profiles (~/.hermes/skills) vs this profile ($HERMES_HOME/skills).
3. List every skill (including AI-PRO-SKILLS submodule) and ask which to install.
Do not copy all by default.

Then copy ONLY the chosen skills into EACH selected destination:
  Cursor:  ~/.cursor/skills/<skill-name>/SKILL.md
  Hermes all:     ~/.hermes/skills/<skill-name>/SKILL.md
  Hermes profile: $HERMES_HOME/skills/<skill-name>/SKILL.md

Always copy the root install skill (ai-skills) into each chosen destination.

Reload Cursor if Cursor was a target. For Hermes, restart/reload the agent if needed.
```

## Agent checklist

1. Clone/pull `~/.ai-skills` + submodule update.
2. Ask **Cursor / Hermes / both**.
3. If Hermes: ask **all** (`~/.hermes/skills`) vs **this profile** (`$HERMES_HOME/skills`); resolve `HERMES_HOME` if needed.
4. List skills (root + `AI-PRO-SKILLS`) and ask which to install.
5. Copy `ai-skills` + selected skills into every chosen destination root.
6. Remind: reload Cursor and/or Hermes; if `agent-browser` selected → `npm i -g agent-browser && agent-browser install`.
7. If `sf` selected → copy `AI-PRO-SKILLS/SF/SKILL.md` → `$DEST/sf/SKILL.md`, then remind to run `/sf` (lists SF skills **by theme**, syncs into `~/.ai-skills/sf-skills`).
8. If `google-workspace` or `powerpoint` selected → copy full folder; Hermes → `$DEST/productivity/<skill>/`.

## Copy map (reference)

Let `DEST` be one of:
- `~/.cursor/skills`
- `~/.hermes/skills`
- `$HERMES_HOME/skills`

| Source (`~/.ai-skills/…`) | Target |
|---------------------------|--------|
| `SKILL.md` | `$DEST/ai-skills/SKILL.md` |
| `c411-torrent/SKILL.md` | `$DEST/c411-torrent/SKILL.md` |
| `qbittorrent-scripts/SKILL.md` | `$DEST/qbittorrent/SKILL.md` |
| `tuya-skill/SKILL.md` | `$DEST/tuya/SKILL.md` |
| `pc-daily-report/SKILL.md` | `$DEST/pc-daily-report/SKILL.md` |
| `AI-PRO-SKILLS/coolify/SKILL.md` | `$DEST/coolify/SKILL.md` |
| `AI-PRO-SKILLS/zscaler/SKILL.md` | `$DEST/zscaler/SKILL.md` |
| `AI-PRO-SKILLS/agent-browser/SKILL.md` | `$DEST/agent-browser/SKILL.md` |
| `AI-PRO-SKILLS/SF/SKILL.md` | `$DEST/sf/SKILL.md` |
| `AI-PRO-SKILLS/google-workspace/` (full tree) | Cursor: `$DEST/google-workspace/` · Hermes: `$DEST/productivity/google-workspace/` |
| `AI-PRO-SKILLS/powerpoint/` (full tree) | Cursor: `$DEST/powerpoint/` · Hermes: `$DEST/productivity/powerpoint/` |

```bash
# Example: Hermes all profiles + qbittorrent only
mkdir -p ~/.hermes/skills/{ai-skills,qbittorrent}
cp ~/.ai-skills/SKILL.md ~/.hermes/skills/ai-skills/SKILL.md
cp ~/.ai-skills/qbittorrent-scripts/SKILL.md ~/.hermes/skills/qbittorrent/SKILL.md

# Example: this Hermes profile
mkdir -p "$HERMES_HOME/skills/{ai-skills,qbittorrent}"
cp ~/.ai-skills/SKILL.md "$HERMES_HOME/skills/ai-skills/SKILL.md"
cp ~/.ai-skills/qbittorrent-scripts/SKILL.md "$HERMES_HOME/skills/qbittorrent/SKILL.md"
```

## After install

- CLI working dirs stay under `~/.ai-skills/<skill-dir>` (see each skill’s `SKILL.md`).
- For **sf**: after copying the meta-skill, run `/sf` — SF trees live in `~/.ai-skills/sf-skills/skills/{skills_dir}`.
- Re-run `/ai-skills` anytime to **pull + ask targets/skills again + re-copy**.

## Notes

- Never write into `~/.cursor/skills-cursor/` (Cursor built-ins only).
- Prefer `cp` (not move). Keep secrets out of skills.
- Repo: [Acher1234/AI-Skills](https://github.com/Acher1234/AI-Skills.git) — submodule: [AI-PRO-SKILLS](https://github.com/Acher1234/AI-PRO-SKILLS.git)
