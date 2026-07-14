# 🧰 Hermes Scripts

> Collection de scripts CLI (shell / python / node) qu'Hermes Agent utilise sur la machine **kleinplex**.
> Chaque commande a son propre dossier avec un README dédié et un fichier de dépendances.

## 📁 Structure

```
hermes-script/
├── README.md               ← Ce fichier
├── SKILL_TEMPLATE.md       ← Guide pour créer un nouveau skill
├── dependencies.md         ← Dépendances transverses (outillage)
├── setup.sh                ← Bootstrap (active les hooks git)
├── .githooks/              ← Hooks git versionnés
│   └── pre-commit          ← Scan gitleaks (bloque les secrets)
├── pc-daily-report/        ← Rapport CPU/RAM/disque quotidien
├── coolify/                ← CLI déploiements Coolify
├── tuya-skill/             ← CLI Tuya IoT
├── qbittorrent-scripts/    ← CLI qBittorrent
└── ...
```

## 🔒 Sécurité — hooks git

Un hook `pre-commit` (dans `.githooks/`) lance **gitleaks** pour empêcher qu'une clé ou un token soit commité par erreur. Active-le une fois après le clone :

```bash
./setup.sh
```

> `git` n'applique pas `core.hooksPath` automatiquement au clone (sécurité), d'où cette étape unique. `setup.sh` fait `git config core.hooksPath .githooks` et vérifie que `gitleaks` est installé.

Détails et installation de `gitleaks` : voir [`dependencies.md`](dependencies.md).

## 📋 Commandes actuelles

| Commande | Description | Langage |
|----------|------------|---------|
| `pc-daily-report` | Rapport monitoring CPU/RAM/disk, livré tous les matins à 7h | bash |
| `coolify` | CLI déploiements Coolify — status, déploiement, redémarrage | python |
| `qbittorrent` | CLI gestion de torrents via l'API WebUI qBittorrent | python |

## 🧩 Créer un nouveau skill

Voir **[`SKILL_TEMPLATE.md`](SKILL_TEMPLATE.md)** pour le guide complet (structure, conventions, sécurité).

## 🚀 Utilisation

Chaque sous-projet contient :
- Un **README.md** (EN) et un **README.fr.md** (FR)
- Un **dependencies.md** listant les dépendances système requises
- Un **config.example.json** template (les vrais secrets sont gitignorés)
- Le **script** exécutable

Les scripts sont conçus pour être appelés :
- Manuellement en CLI
- Via un cron job Hermes (`cronjob` action)
- Ou directement en shell

---

*Mis à jour par Hermes Agent — chaque nouvelle commande atterrit ici.*