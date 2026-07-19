---
name: pc-daily-report
description: >-
  Generate a daily Linux host report (uptime, CPU/RAM via sar, disk, top
  processes). Use when the user asks for a daily report, sysstat summary, or
  invokes /pc-daily-report_run.
disable-model-invocation: true
---

# pc-daily-report

## When to use

Use for daily machine health summaries on Linux. Trigger phrases: "daily report", "rapport quotidien", "sar CPU RAM", `/pc-daily-report_run`.

## Working directory

`~/.ai-skills/pc-daily-report`

## Slash commands

| Slash | CLI | Description |
|-------|-----|-------------|
| `/pc-daily-report_run` | `./pc-daily-report.sh` | Print today's monitoring report |

## How to run

1. `cd` into `pc-daily-report/`.
2. Ensure `sysstat` / `sar` data is available (`SADIR` defaults to `/var/log/sysstat`).
3. Execute `./pc-daily-report.sh` and return the full stdout to the user.

## Notes

- Bash script (no Python subcommands).
- Often scheduled via Hermes cron at `0 7 * * *` with `no_agent=true`.
- See `dependencies.md` for packages.
