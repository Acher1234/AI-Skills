# daily-raspy-report

Rapport de monitoring quotidien pour la machine **kleinplex** (Raspberry Pi).

## Description

Utilise les données collectées par `sysstat` (`sar`) pour produire un résumé de la journée écoulée : CPU, RAM, disque, et top processus. Le rapport est livré automatiquement à **7h00** sur Telegram via un cron job Hermes.

## Utilisation

```bash
# Exécution directe
./daily-raspy-report.sh

# Via cron job Hermes (no_agent mode — livré tel quel)
cronjob action=create \
  name="Rapport quotidien" \
  schedule="0 7 * * *" \
  script="daily-raspy-report.sh" \
  no_agent=true \
  deliver=origin
```

## Exemple de sortie

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📊 RAPPORT QUOTIDIEN — kleinplex
  2026-06-29
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏱ UPTIME & LOAD
up 11:05,  3 users,  load average: 0.69, 0.63, 0.57

── 🖥 CPU — 8 cœurs ARM ──
▸ Moyenne — User: 4.9% | System: 1.0% | IOWait: 0.0% | Idle: 94.1%
▸ Top 3 pics CPU : ...

── 💾 RAM — 5.7 GiB total ──
▸ Utilisation moyenne : 7.0%  ...
...
```

## Dépendances

- `sysstat` (paquet système) — fournit `sar`
- Fichiers de données : `/var/log/sysstat/sa??`

## Cron job actif

- **Job ID :** `e7b53e1ca8e1`
- **Horaire :** `0 7 * * *` (tous les jours à 7h)
- **Mode :** `no_agent` (script pur, pas de LLM)
