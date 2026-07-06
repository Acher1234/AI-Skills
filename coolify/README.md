# coolify

CLI pour interroger l'état des déploiements sur des instances **Coolify**.

## Installation

```bash
# Rien à installer — script Python standalone (stdlib uniquement)
# Juste créer la config :
cp config.example.json config.json
# Puis éditer config.json avec vos instances Coolify
```

## Configuration

Le fichier `config.json` est cherché dans le dossier du script par défaut.
Vous pouvez le placer ailleurs et pointer via la variable d'environnement :

```bash
export COOLIFY_CONFIG_PATH=/root/.hermes/coolify-config.json
```

Contenu du fichier : un tableau d'instances Coolify.

```json
{
  "instances": [
    {
      "name": "production",
      "url": "https://coolify.votre-domaine.com",
      "token": "votre-token-api",
      "applications": {
        "mon-app": "uuid-de-l-application",
        "api": "uuid-api"
      }
    },
    {
      "name": "staging",
      "url": "https://staging.coolify.votre-domaine.com",
      "token": "votre-token-api",
      "applications": {
        "mon-app": "uuid-staging"
      }
    }
  ]
}
```

| Champ | Description |
|-------|-------------|
| `name` | Nom logique de l'instance (pour le CLI) |
| `url` | URL racine de l'instance Coolify |
| `token` | Token API Coolify (Bearer auth) |
| `applications` | Objet `nom_local: uuid_coolify` des apps à monitorer |

> ⚠️ `config.json` est dans `.gitignore` — seul `config.example.json` est versionné.

## Utilisation

```bash
# Lister les instances configurées
./coolify.py instances

# Statut actuel d'une app (infos + dernier déploiement)
./coolify.py status production mon-app

# Derniers 5 déploiements d'une app
./coolify.py deployments production mon-app

# Derniers 10 déploiements
./coolify.py deployments production mon-app -n 10
```

## Exemple de sortie

```
📊 Statut de « mon-app » sur « production »
   UUID : abc123-def456

   🔤 Nom          : Mon App
   🌐 Domaine      : https://mon-app.example.com
   📦 Type         : dockerfile
   📍 Statut       : ✅ running
   🕐 Créée le     : 01/01/2025 12:00:00

   🔄 Dernier déploiement :
      Commit       : a1b2c3d4e5f6
      Statut       : ✅ success
      Début        : 05/07/2026 14:30:00
      Durée        : 2m 15s
```

```
📋 Derniers 5 déploiements de « mon-app » sur « production »

  ✅  Commit: a1b2c3d4e5f6  | 05/07/2026 14:30:00  | Durée: 2m 15s
     ID: dep-uuid-1

  ❌  Commit: f6e5d4c3b2a1  | 05/07/2026 12:00:00  | Durée: 1m 30s
     ID: dep-uuid-2
```

## API Coolify utilisée

- `GET /api/v1/applications/{uuid}`
- `GET /api/v1/applications/{uuid}/deployments?per_page=N`
