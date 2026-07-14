# qbittorrent-scripts

CLI pour gérer les torrents via l'**API WebUI de qBittorrent**.

## Installation

```bash
export QBITTORRENT_CONFIG_PATH=/root/.hermes/qbittorrent-config.json
```

### Configuration

Copiez `config.example.json` vers le chemin de config et remplissez vos identifiants.

```json
{
  "url": "http://192.168.2.2:9999",
  "username": "admin",
  "password": "VOTRE_MOT_DE_PASSE"
}
```

Seul le template est versionné — la vraie config est gitignorée.

## Utilisation

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

## Filtres

`all`, `downloading`, `seeding`, `completed`, `paused`, `active`, `inactive`, `stalled`, `errored`

## États

| Icône | État | Signification |
|-------|------|---------------|
| ⬇️ | downloading | Téléchargement en cours |
| ⬆️ | uploading | Envoi en cours (seeding) |
| ⏸️ | pausedDL / pausedUP | En pause |
| ⏳ | queuedDL / queuedUP | En file d'attente |
| 🔍 | checkingDL / checkingUP | Vérification |
| ❌ | error | Erreur |
| ⚠️ | missingFiles | Fichiers manquants |

## Dépendances

- **Python 3.11+** — stdlib uniquement
- **qBittorrent v4.1+** avec WebUI activée

## Environnement

| Variable | Défaut |
|----------|--------|
| `QBITTORRENT_CONFIG_PATH` | `/root/.hermes/qbittorrent-config.json` |