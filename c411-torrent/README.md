# c411-torrent

CLI to search and download torrents via the **C411 API** (Torznab).

## Installation

```bash
export C411_CONFIG_PATH=/root/.hermes/c411-config.json
```

### Configuration

Copy `config.example.json` to your config path and fill in your details.

```json
{
  "url": "https://c411.org",
  "api_key": "YOUR_API_KEY",
  "download_path": "/home/data/disk1/torrents"
}
```

## Usage

```bash
# Search
./c411.py search "rick morty" --cat tv --limit 5

# Download by hash or URL
./c411.py download 438930e39153273f8ef3b0c6c60882ced31c1ab7
./c411.py download https://c411.org/torrents/438930e391...
```

## Categories / Catégories

`all`, `movies`, `tv`, `music`, `games`, `software`, `anime`, `books`

## Dependencies

- **Python 3.11+** — stdlib only

## Environment

| Variable | Default |
|----------|---------|
| `C411_CONFIG_PATH` | `/root/.hermes/c411-config.json` |