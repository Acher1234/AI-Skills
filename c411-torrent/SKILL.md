---
name: c411-torrent
description: >-
  Search and download torrents via the C411 Torznab API. Use when the user asks
  to search C411, download a torrent by hash/URL, or invokes /c411-torrent_*.
disable-model-invocation: true
---

# c411-torrent

## When to use

Use for C411 / Torznab search and download. Trigger phrases: "search c411", "download torrent", "torznab", `/c411-torrent_search`, `/c411-torrent_download`.

## Working directory

`~/.ai-skills/c411-torrent`

## Shared environment (see AI-Skills README)

- **Python**: run through the shared venv — `~/.ai-skills/.venv/bin/python c411.py …` (stdlib-only; if deps are ever added, install once with `~/.ai-skills/install.sh pip init .`). Do not create a per-skill venv.
- **Config**: this skill keeps its **own** `config.json` — placed **next to the installed `SKILL.md`**, i.e. in the chosen client's skill folder (`~/.cursor/skills/c411-torrent/`, `./.cursor/skills/c411-torrent/` for a project, `$HERMES_HOME/.../c411-torrent/`, etc.), exactly where a `.env` would go. Override with `C411_CONFIG_PATH` if needed. Never commit a real API key.

## Slash commands

| Slash | CLI | Description |
|-------|-----|-------------|
| `/c411-torrent_search` | `./c411.py search "<query>" [--cat CAT] [--limit N]` | Search torrents |
| `/c411-torrent_download` | `./c411.py download <url\|hash>` | Download by URL or info-hash |

Categories: `all`, `movies`, `tv`, `music`, `games`, `software`, `anime`, `books`.

## How to run

1. `cd ~/.ai-skills/c411-torrent`.
2. Ensure `config.json` exists **next to the installed `SKILL.md`** (the chosen client's skill folder) — copy from `config.example.json` if needed. `C411_CONFIG_PATH` overrides the location.
3. Map the slash command to the CLI row above and run it with the shared interpreter: `~/.ai-skills/.venv/bin/python c411.py <cmd>`.
4. Return CLI stdout/stderr to the user.

## Notes

- Python 3.11+, stdlib only.
- Never commit real `config.json` / API keys.
