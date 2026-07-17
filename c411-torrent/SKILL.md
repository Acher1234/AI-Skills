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

## Slash commands

| Slash | CLI | Description |
|-------|-----|-------------|
| `/c411-torrent_search` | `./c411.py search "<query>" [--cat CAT] [--limit N]` | Search torrents |
| `/c411-torrent_download` | `./c411.py download <url\|hash>` | Download by URL or info-hash |

Categories: `all`, `movies`, `tv`, `music`, `games`, `software`, `anime`, `books`.

## How to run

1. `cd` into `c411-torrent/`.
2. Ensure config exists (`C411_CONFIG_PATH`, default `/root/.hermes/c411-config.json`) — copy from `config.example.json` if needed.
3. Map the slash command to the CLI row above and execute it.
4. Return CLI stdout/stderr to the user.

## Notes

- Python 3.11+, stdlib only.
- Never commit real `config.json` / API keys.
