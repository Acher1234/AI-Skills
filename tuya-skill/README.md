# tuya-skill

CLI Python pour interagir avec l'API **Tuya IoT** — contrôle d'appareils connectés.

## Installation

```bash
pip install tuya-connector-python
cp config.example.json config.json
# Éditez config.json avec vos identifiants Tuya IoT
```

## Configuration

Le fichier `config.json` (non versionné, `.gitignore`) contient :

| Champ | Description |
|-------|-------------|
| `auth_key` | Authorization Key (Tuya IoT Platform) |
| `access_id` | Access ID / Client ID |
| `access_secret` | Access Secret / Client Secret |
| `project_code` | Project Code (Tuya IoT Platform) |
| `region` | Région : `eu`, `us`, `cn`, `in` |

Vous pouvez placer le fichier ailleurs et pointer via la variable d'environnement :

```bash
export TUYA_CONFIG_PATH=/root/.hermes/tuya-config.json
```

## Utilisation

```bash
# Générer un access token
./tuya.py token

# Lister les appareils
./tuya.py devices

# État d'un appareil
./tuya.py status <device_id>
```

## Dépendances

Voir [`dependencies.md`](dependencies.md).