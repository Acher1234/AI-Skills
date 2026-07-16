# tuya-skill

> 🌐 *English version: [README.md](README.md)*

CLI Python pour interagir avec l'API **Tuya IoT** — contrôle d'appareils connectés (prises, climatiseurs IR, etc.).

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
# Générer un access token (test d'authentification)
./tuya.py token

# Lister tous les appareils (nom, ID, modèle, statut)
./tuya.py devices

# Disponibilité d'un appareil (online / offline)
./tuya.py status <device_id>

# État détaillé avec labels lisibles (mode, vitesse, température...)
./tuya.py state <device_id>

# Allumer un appareil
./tuya.py on <device_id>

# Éteindre un appareil
./tuya.py off <device_id>

# Renommer un appareil
./tuya.py rename <device_id> "Nouveau nom"
```

## Commandes disponibles

| Commande | Description |
|----------|-------------|
| `token` | Génère un access token (vérifie les identifiants) |
| `devices` | Liste tous les appareils du compte |
| `status <device_id>` | Disponibilité : `🟢 online` / `🔴 offline` |
| `state <device_id>` | État détaillé (power, mode, temp, wind...) avec labels |
| `on <device_id>` | Allume l'appareil |
| `off <device_id>` | Éteint l'appareil |
| `rename <device_id> <nom>` | Renomme l'appareil |

> `on` / `off` détectent automatiquement le bon code de commande :
> `switch_1` pour les prises, `switch` pour les climatiseurs IR.

## Exemples de sortie

### devices
```
📱 Appareils Tuya (2):

  • Prise salon
    ID       : bfxxxxxxxxxxxxxxxxxx
    Model    : SP-01
    Status   : 🟢 online

  • Clim chambre
    ID       : bfyyyyyyyyyyyyyyyyyy
    Model    : IR-AC
    Status   : 🔴 offline
```

### state
```
📊 État de « bfxxxxxxxxxxxxxxxxxx » :

  🔌 Switch            : 🟢 ON
  🔄 Mode              : cool
  🌡️ Temp             : 22
  💨 Wind              : auto
```

## Correspondance des valeurs

| Code | Valeurs |
|------|---------|
| `mode` | `0` auto · `1` cool · `2` heat · `3` fan · `4` dry |
| `wind` / `fan` | `0` low · `1` mid · `2` high · `3` auto |

## Régions Tuya (endpoints)

| Région | Base URL |
|--------|----------|
| `eu` | `https://openapi.tuyaeu.com` |
| `us` | `https://openapi.tuyaus.com` |
| `cn` | `https://openapi.tuyacn.com` |
| `in` | `https://openapi.tuyain.com` |

## Dépendances

Voir [`dependencies.md`](dependencies.md) pour la liste complète.

## API Tuya utilisée

- `GET /v2.0/cloud/thing/device` — liste des appareils
- `GET /v1.0/devices/{id}/status` — état détaillé
- `POST /v1.0/devices/{id}/commands` — envoi de commandes (on/off)
- `PUT /v1.0/devices/{id}` — renommage
