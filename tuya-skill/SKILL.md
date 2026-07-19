---
name: tuya
description: >-
  Control Tuya IoT devices via cloud API or LAN (tinytuya): list devices, on/off,
  status/state, rename, IR climate, local-scan/sync. Use when the user mentions
  Tuya, Smart Life, plugs, AC, or invokes /tuya_*.
disable-model-invocation: true
---

# tuya

## When to use

Use for Tuya cloud or local LAN device control. Trigger phrases: "turn on plug", "tuya devices", "local-scan", `/tuya_devices`, `/tuya_on`, `/tuya_local-sync`.

## Working directory

`~/.ai-skills/tuya-skill`

Entrypoint: `./tuya.py` (or `./cmd.py` — equivalent).

## Shared environment (see AI-Skills README)

- **Python**: run through the shared venv — `~/.ai-skills/.venv/bin/python tuya.py …`. Install the deps once into the shared venv from the skill dir: `~/.ai-skills/install.sh pip init .` (installs this skill's `requirements.txt`; do not create a per-skill venv).
- **Config**: this skill keeps its **own** `config.json` — placed **next to the installed `SKILL.md`** (the chosen client's skill folder: `~/.cursor/skills/…`, `./.cursor/skills/…` for a project, `$HERMES_HOME/.../…`, etc.), exactly where a `.env` would go. Override with `TUYA_CONFIG_PATH` if needed. Never commit `config.json`, `devices.json`, or `tuya-scan.json` (they hold local keys).

## Slash commands

### Cloud

| Slash | CLI | Description |
|-------|-----|-------------|
| `/tuya_token` | `./tuya.py token` | Test auth / get token |
| `/tuya_devices` | `./tuya.py devices` | List cloud devices |
| `/tuya_status` | `./tuya.py status <device_id>` | Online / offline |
| `/tuya_state` | `./tuya.py state <device_id>` | Detailed state |
| `/tuya_on` | `./tuya.py on <device_id>` | Turn on |
| `/tuya_off` | `./tuya.py off <device_id>` | Turn off |
| `/tuya_rename` | `./tuya.py rename <device_id> "Name"` | Rename device |
| `/tuya_clim` | `./tuya.py clim <device_id> …` | IR climate controls (if supported) |
| `/tuya_cloud-sync` | `./tuya.py cloud-sync` | Cloud sync helper |

### Local (LAN)

| Slash | CLI | Description |
|-------|-----|-------------|
| `/tuya_local-scan` | `./tuya.py local-scan [--seconds N]` | LAN scan → `tuya-scan.json` |
| `/tuya_local-sync` | `./tuya.py local-sync […]` | Fetch local keys → `devices.json` |
| `/tuya_local-devices` | `./tuya.py local-devices [--show-keys]` | List local devices |
| `/tuya_local-status` | `./tuya.py local-status <device_id>` | Local availability |
| `/tuya_local-state` | `./tuya.py local-state <device_id>` | Local detailed state |
| `/tuya_local-on` | `./tuya.py local-on <device_id>` | Local turn on |
| `/tuya_local-off` | `./tuya.py local-off <device_id>` | Local turn off |
| `/tuya_local-clim` | `./tuya.py local-clim <device_id> …` | Local IR climate |

## How to run

1. `cd ~/.ai-skills/tuya-skill`.
2. Ensure the shared venv has the deps (`~/.ai-skills/install.sh pip init .`) and `config.json` **next to the installed `SKILL.md`** (`TUYA_CONFIG_PATH` overrides).
3. Prefer resolving device name → id via `/tuya_devices` or `/tuya_local-devices` before on/off.
4. Run the CLI for the slash command with `~/.ai-skills/.venv/bin/python tuya.py <cmd>`; return output.

## Notes

- Never commit `config.json`, `devices.json`, or `tuya-scan.json` (local keys).
- Local mode requires same LAN, Smart Life closed, UDP/TCP ports open — see `README.md`.
