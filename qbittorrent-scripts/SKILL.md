---
name: qbittorrent
description: >-
  Manage torrents via the qBittorrent WebUI API (list, add, pause, resume,
  delete, categories, tags, transfer). Use when the user mentions qBittorrent,
  qbit, torrents, or invokes /qbittorrent_*.
disable-model-invocation: true
---

# qbittorrent

## When to use

Use for qBittorrent WebUI management. Trigger phrases: "list torrents", "add magnet", "pause torrent", "qBittorrent", `/qbittorrent_list`, `/qbittorrent_add`.

## Working directory

`~/.ai-skills/qbittorrent-scripts`

## Slash commands

| Slash | CLI | Description |
|-------|-----|-------------|
| `/qbittorrent_list` | `./qbittorrent.py list [--filter F] [--category C]` | List torrents |
| `/qbittorrent_add` | `./qbittorrent.py add "magnet:…" [--category C] [--paused]` | Add magnet |
| `/qbittorrent_add-file` | `./qbittorrent.py add-file <path> […]` | Add .torrent file |
| `/qbittorrent_info` | `./qbittorrent.py info <hash>` | Torrent details |
| `/qbittorrent_files` | `./qbittorrent.py files <hash>` | List files in torrent |
| `/qbittorrent_pause` | `./qbittorrent.py pause <hash\|all>` | Pause |
| `/qbittorrent_resume` | `./qbittorrent.py resume <hash\|all>` | Resume |
| `/qbittorrent_delete` | `./qbittorrent.py delete <hash> [--files]` | Delete (optionally with files) |
| `/qbittorrent_categories` | `./qbittorrent.py categories` | List categories |
| `/qbittorrent_tags` | `./qbittorrent.py tags` | List tags |
| `/qbittorrent_transfer` | `./qbittorrent.py transfer` | Global transfer info |
| `/qbittorrent_version` | `./qbittorrent.py version` | API / app version |

Filters: `all`, `downloading`, `seeding`, `completed`, `paused`, `active`, `inactive`, `stalled`, `errored`.

## How to run

1. `cd` into `qbittorrent-scripts/`.
2. Ensure `QBITTORRENT_CONFIG_PATH` (default `/root/.hermes/qbittorrent-config.json`) or local config from `config.example.json`.
3. Run the CLI matching the slash command.
4. Return output to the user.

## Notes

- Python 3.11+, stdlib only; needs qBittorrent v4.1+ with WebUI enabled.
- Prefer hash from a prior `/qbittorrent_list` when the user names a torrent.
