# 🧰 Hermes Scripts

> Collection de scripts CLI (shell / python / node) qu'Hermes Agent utilise sur la machine **kleinplex** (Raspberry Pi).
> Chaque commande a son propre dossier avec un README dédié.

## 📁 Structure

```
hermes-script/
├── README.md               ← Ce fichier
├── daily-raspy-report/     ← Rapport CPU/RAM/disque quotidien
├── coolify/                ← CLI déploiements Coolify
└── ...                     ← (À venir : tri filebot, deploiement, etc.)
```

## 📋 Commandes actuelles

| Commande | Description | Langage |
|----------|------------|---------|
| `daily-raspy-report` | Rapport monitoring CPU/RAM/disk, livré tous les matins à 7h | bash |
| `coolify` | CLI déploiements Coolify — status, déploiement, redémarrage | python |

## 🚀 Utilisation

Chaque dossier contient :
- Un **README** expliquant la commande
- Le **script** exécutable

Les scripts sont conçus pour être appelés :
- Manuellement en CLI
- Via un cron job Hermes (`cronjob` action)
- Ou directement en shell

## 📦 Dépendances système

- `sysstat` (sar) — collecte des métriques CPU/RAM
- `filebot` — tri des films/séries
- `chromium-browser` — génération PDF (snap)
- `node` / `npm` — pour les scripts Node

---

*Mis à jour par Hermes Agent — chaque nouvelle commande atterrit ici.*
