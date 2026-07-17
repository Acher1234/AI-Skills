# tuya-skill

> 🌐 *English version: [README.md](README.md)*

CLI Python pour interagir avec l'API **Tuya IoT** — contrôle d'appareils connectés (prises, climatiseurs IR, etc.).

## Installation

```bash
pip install tuya-connector-python
pip install tinytuya            # optionnel — uniquement pour le mode local (LAN)
cp config.example.json config.json
# Éditez config.json avec vos identifiants Tuya IoT
```

## Structure du projet

Le CLI est découpé en trois modules (plus un shim de compatibilité) :

| Fichier | Rôle |
|---------|------|
| `cloud.py` | Commandes Cloud (API Tuya IoT via `tuya-connector`) |
| `local.py` | Commandes Local (LAN via `tinytuya`) |
| `cmd.py` | Point d'entrée — argparse + chargement config + dispatch |
| `tuya.py` | Shim de compatibilité → lance `cmd.main()` (pour que `./tuya.py …` continue de marcher) |

`./tuya.py <commande>` et `./cmd.py <commande>` sont équivalents.

## Créer un compte Tuya (obtenir vos identifiants)

> ⚠️ Tuya change souvent son portail et ses services. Si ces étapes sont obsolètes, ouvrez une issue avec des captures d'écran pour qu'on les mette à jour.

> **Prérequis :** installez l'application **Smart Life** sur votre téléphone et appairez-y tous vos appareils *avant* de faire le lien (le projet cloud importe ce qui est déjà dans Smart Life).

1. Créez un compte développeur Tuya sur [iot.tuya.com](https://iot.tuya.com). Quand il demande l'**« Account Type »**, choisissez **« Skip this step... »**.
2. Cliquez sur l'icône **Cloud** → **Create Cloud Project**.
3. Choisissez la bonne **« Region » (Data Center)** pour votre localisation (voir la [liste des data centers Tuya](https://developer.tuya.com/en/docs/iot/oem-app-data-center-distributed?id=Kafi0ku9l07qb)). Elle correspond au champ `region` de `config.json` (`eu`, `us`, `cn`, `in`).
4. Passez l'assistant de configuration, mais **notez l'Authorization Key** : l'**Access ID / Client ID** et l'**Access Secret / Client Secret** — à reporter dans `config.json` (`access_id`, `access_secret`).
5. Cliquez sur l'icône **Cloud** → sélectionnez votre projet → **Devices** → **Link Tuya App Account**.
6. Cliquez sur **Add App Account** → une fenêtre **« Link Tuya App Account »** s'ouvre. Choisissez **« Automatic »** et **« Read Only Status »** (les commandes fonctionneront quand même). Cliquez **OK** — un **QR code** apparaît. Scannez-le avec l'app **Smart Life** : onglet **« Me »** → bouton QR/scan **[..]** en haut à droite. Cela lie tous les appareils enregistrés dans Smart Life à votre projet Tuya IoT.
   - Si le QR code ne se scanne pas, désactivez les plugins de thème du navigateur (ex. **Dark Reader**) et réessayez.
7. **Aucun appareil ?** Si rien n'apparaît après le scan, sélectionnez un **data center différent** et éditez votre projet (ou créez-en un nouveau) jusqu'à voir vos appareils appairés. Le bon data center n'est pas toujours le plus logique — ex. certains au Royaume-Uni doivent choisir **« Central Europe »** au lieu de **« Western Europe »**.
8. **Service API :** sous **« Service API »**, vérifiez que **IoT Core** et **Authorization** sont bien listés. Par sécurité, recliquez sur subscribe pour chaque service. **Désactivez les bloqueurs de popups** — sinon l'abonnement échoue silencieusement. Puis autorisez votre projet :
   - Cliquez sur l'onglet **« Service API »**
   - Cliquez sur **« Go to Authorize »**
   - Sélectionnez les API Groups dans le menu déroulant et cliquez **Subscribe**

> **Renouvellement :** l'abonnement à **IoT Core** expire au bout d'un certain temps (1 mois par défaut lors du premier abonnement). Une fois expiré, l'API ne peut plus communiquer avec votre compte Tuya et doit être renouvelé. Depuis le 12 novembre 2024, il se renouvelle pour **1, 3 ou 6 mois** en remplissant un court formulaire (objectif du projet, type de développeur).

Une fois que vous avez l'**Access ID**, l'**Access Secret**, le **project code** et la **région**, renseignez-les dans `config.json` (voir ci-dessous).

## Configuration

Le fichier `config.json` (non versionné, `.gitignore`) contient :

| Champ | Description |
|-------|-------------|
| `auth_key` | Authorization Key (Tuya IoT Platform) |
| `access_id` | Access ID / Client ID |
| `access_secret` | Access Secret / Client Secret |
| `project_code` | Project Code (Tuya IoT Platform) |
| `region` | Région : `eu`, `us`, `cn`, `in` |
| `use_local` | `true` pour privilégier le mode local (LAN), `false` pour le cloud (défaut `false`) |
| `local_devices_file` | Fichier JSON contenant les local keys (défaut `devices.json`) |

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

## Mode local (LAN via tinytuya)

Le mode local parle aux appareils **directement sur votre LAN**, sans passer par le cloud. Pour piloter un appareil en local, il faut sa **local key** — qui n'est *pas* fournie par le scan LAN. Le scan ne révèle que `ip` + `device_id` + `version` ; les local keys sont récupérées via le **cloud** (`tinytuya.Cloud.getdevices()`, le même mécanisme que le `wizard` de tinytuya).

> **Prérequis :** lancez ces commandes depuis une machine sur le **même LAN** que vos appareils, fermez l'app Smart Life, et autorisez **UDP 6666/6667/7000** et **TCP 6668** dans le pare-feu.

```bash
# 1) Scan LAN → ip + device_id + version (pas de local keys)  → écrit tuya-scan.json
./tuya.py local-scan
./tuya.py local-scan --seconds 50        # scan plus long si des appareils manquent

# 2) Récupère les local keys via le cloud, fusionne les IP du scan  → écrit devices.json
./tuya.py local-sync                      # keys masquées à l'affichage
./tuya.py local-sync --show-keys          # affiche les keys en clair
./tuya.py local-sync --no-scan --device-id <id>   # sans scan LAN, fournir un id échantillon

# 3) Liste les appareils depuis devices.json
./tuya.py local-devices
./tuya.py local-devices --show-keys
```

Fonctionnement de `local-sync` :

1. Scanne le LAN pour collecter les IP (et choisit un `device_id` échantillon).
2. Appelle `Cloud.getdevices()` avec vos `access_id` / `access_secret` / `region` → récupère `id` + `name` + `key` (local key).
3. Fusionne l'IP scannée dans chaque appareil → écrit `devices.json`.

> ⚠️ `devices.json` et `tuya-scan.json` contiennent des secrets (local keys). Ils sont déjà dans `.gitignore` — ne les committez jamais.

### Commandes locales

| Commande | Description |
|----------|-------------|
| `local-scan [--seconds N]` | Scan LAN → `ip` + `device_id` + `version` → `tuya-scan.json` |
| `local-sync [--device-id ID] [--seconds N] [--no-scan] [--show-keys]` | Récupère les local keys via le cloud → `devices.json` |
| `local-devices [--show-keys]` | Liste les appareils depuis `devices.json` |

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
