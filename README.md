# 🧰 Hermes Scripts

> Collection de scripts CLI (shell / python / node) qu'Hermes Agent utilise sur la machine **kleinplex**.
> Chaque commande a son propre dossier avec un README dédié et un fichier de dépendances.

## 📁 Structure

```
hermes-script/
├── README.md               ← Ce fichier
├── pc-daily-report/        ← Rapport CPU/RAM/disque quotidien
│   ├── README.md           ← Documentation de la commande
│   ├── dependencies.md     ← Dépendances requises
│   └── pc-daily-report.sh  ← Le script
├── coolify/                ← CLI déploiements Coolify
│   ├── README.md
│   └── coolify.py
└── ...                     ← (À venir : tri filebot, déploiement, etc.)
```

## 📋 Commandes actuelles

| Commande | Description | Langage |
|----------|------------|---------|
| `pc-daily-report` | Rapport monitoring CPU/RAM/disk, livré tous les matins à 7h | bash |
| `coolify` | CLI déploiements Coolify — status, déploiement, redémarrage | python |

## 🚀 Utilisation

Chaque sous-projet contient :
- Un **README.md** expliquant la commande, son usage et des exemples
- Un **dependencies.md** listant les dépendances système requises
- Le **script** exécutable

Les scripts sont conçus pour être appelés :
- Manuellement en CLI
- Via un cron job Hermes (`cronjob` action)
- Ou directement en shell

---

*Mis à jour par Hermes Agent — chaque nouvelle commande atterrit ici.*