# qbittorrent-scripts

CLI to manage torrents via the **qBittorrent WebUI API**.

## Installation

```bash
export QBITTORRENT_CONFIG_PATH=/root/.hermes/qbittorrent-config.json
```

### Configuration

Copy `config.example.json` to your config path and fill in your details.

```json
{
  "url": "http://192.168.2.2:9999",
  "username": "admin",
  "password": "YOUR_PASSWORD"
}
```

Only the template is tracked by git — the real config is gitignored.

## Usage

```bash
./qbittorrent.py list [--filter downloading|seeding|paused] [--category movies]
./qbittorrent.py add "magnet:?xt=..." [--category movies] [--paused]
./qbittorrent.py info <hash>
./qbittorrent.py files <hash>
./qbittorrent.py pause <hash|all>
./qbittorrent.py resume <hash|all>
./qbittorrent.py delete <hash> [--files]
./qbittorrent.py version
./qbittorrent.py categories
./qbittorrent.py tags
./qbittorrent.py transfer
```

## Filters

`all`, `downloading`, `seeding`, `completed`, `paused`, `active`, `inactive`, `stalled`, `errored`

## States

| Icon | State | Meaning |
|------|-------|---------|
| ⬇️ | downloading | Downloading |
| ⬆️ | uploading | Uploading (seeding) |
| ⏸️ | pausedDL / pausedUP | Paused |
| ⏳ | queuedDL / queuedUP | Queued |
| 🔍 | checkingDL / checkingUP | Checking |
| ❌ | error | Error |
| ⚠️ | missingFiles | Missing files |

## Dependencies

- **Python 3.11+** — stdlib only
- **qBittorrent v4.1+** with WebUI enabled

## Environment

| Variable | Default |
|----------|---------|
| `QBITTORRENT_CONFIG_PATH` | `/root/.hermes/qbittorrent-config.json` |