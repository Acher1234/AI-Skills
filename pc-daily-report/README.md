# pc-daily-report

Rapport de monitoring quotidien pour la machine **kleinplex**.

## Description

Utilise les données collectées par `sysstat` (`sar`) pour produire un résumé de la journée écoulée : CPU, RAM, disque, et top processus. Le rapport est livré automatiquement à **7h00** sur Telegram via un cron job Hermes.

## Utilisation

```bash
# Exécution directe
./pc-daily-report.sh

# Via cron job Hermes (no_agent mode — livré tel quel)
cronjob action=create \
  name="Rapport quotidien" \
  schedule="0 7 * * *" \
  script="pc-daily-report.sh" \
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

── 🖥 CPU ──
▸ Moyenne — User: 4.9% | System: 1.0% | IOWait: 0.0% | Idle: 94.1%
▸ Top 3 pics CPU : ...

── 💾 RAM ──
▸ Utilisation moyenne : 7.0%  ...
...
```

## Dépendances

Voir [`dependencies.md`](dependencies.md) pour la liste complète des dépendances.

## Cron job actif

- **Horaire :** `0 7 * * *` (tous les jours à 7h)
- **Mode :** `no_agent` (script pur, pas de LLM)