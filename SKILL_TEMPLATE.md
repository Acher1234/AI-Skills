# 🧩 Comment coder un skill / How to code a skill

Ce guide explique la structure attendue pour chaque nouveau script CLI dans `hermes-script`.
This guide explains the expected structure for each new CLI script in `hermes-script`.

## 📁 Structure d'un skill

Chaque skill = **1 dossier** (à la racine ou sous `pro-skills/`), contenant :

```
hermes-script/
└── mon-skill/
    ├── SKILL.md            ← Agent skill (EN) — slash commands + how to run
    ├── README.md           ← Doc en anglais (Markdown)
    ├── README.fr.md        ← Doc en français (Markdown)
    ├── dependencies.md     ← Dépendances système/pip
    ├── .gitignore          ← Ignore les fichiers sensibles (config.json, __pycache__)
    ├── config.example.json ← Template de config (versionné, sans secrets)
    └── mon-script.py       ← Le script CLI exécutable
```

## 🎯 SKILL.md (required)

Every skill **must** ship a `SKILL.md` in its folder. It is the **English** agent entrypoint: when to use the skill, how to launch the CLI, and the **slash commands** that map to each action.

### Purpose

- Cursor / Hermes can discover and invoke the skill.
- Users (and agents) call actions with slash commands:
  - pattern: `/{skill-name}_{command}`
  - examples: `/qbittorrent_list`, `/tuya_on`, `/zscaler_zia_create-forwarding-rule`
- Nested CLI verbs use extra underscores: `/{skill}_{product}_{action}` (e.g. ZIA under zscaler).

### Required structure

```markdown
---
name: skill-name
description: What it does and when to use it (third person, include trigger terms).
disable-model-invocation: true
---

# skill-name

## When to use
One short paragraph with trigger phrases.

## Working directory
`~/.ai-skills/<skill-dir>` (e.g. `~/.ai-skills/qbittorrent-scripts`).

## Slash commands
| Slash | CLI | Description |
|-------|-----|-------------|
| `/skill-name_command` | `./script.py command …` | … |

## How to run
Steps: `cd ~/.ai-skills/<skill-dir>`, ensure config/env, then run the matching CLI for the slash command.

## Notes
Config path, activation, safety, etc.
```

### Naming rules

| Rule | Example |
|------|---------|
| `name` in frontmatter = slash prefix | `name: tuya` → `/tuya_*` |
| Lowercase, hyphens allowed in skill name | `pc-daily-report`, `c411-torrent` |
| Command segment = CLI subcommand (hyphens OK) | `/zscaler_zia_add-url` |
| One row per invocable action | Do not invent slash aliases without a real CLI |
| Body language = **English only** | French stays in `README.fr.md` / `README-FR.md` |

### Checklist when adding a skill

1. Create the folder + CLI + READMEs + `dependencies.md` + `config.example.json`
2. Write **`SKILL.md`** with full slash-command table
3. **Copy** that file into **`.cursor/skills/<skill-name>/SKILL.md`** (required for Cursor Agent / `/skill-name`)
4. Keep slash list in sync when you add/remove CLI commands
5. See root [`SKILL.md`](SKILL.md) for the full Cursor registration guide

> Cursor only loads skills from `.cursor/skills/` (or `.agents/skills/`, or `~/.cursor/skills/`). A `SKILL.md` next to the CLI is the source of truth, but it **must** also be installed under `.cursor/skills/`.


## 📝 README.md / README.fr.md

Chaque README doit contenir :
- **Installation** : comment installer les dépendances et configurer
- **Configuration** : format de `config.json` avec exemple
- **Utilisation** : toutes les commandes disponibles avec exemples
- **Filtres / Options** : liste des options (si applicable)
- **États** : table des états/icônes (si applicable)
- **Dépendances** : renvoi vers `dependencies.md`
- **Environnement** : variables d'env supportées

> `SKILL.md` = agent + slash commands (EN).  
> `README*.md` = human docs (EN + FR). Both are required; do not replace one with the other.

## 📦 dependencies.md

```markdown
| Package | Version | Install | Usage |
|---------|---------|---------|-------|
| `python3` | 3.11+ | `apt-get install python3` | Runtime |
```

## 🔐 config.example.json

Template **sans secrets** — les vraies valeurs vont dans `config.json` (gitignoré).

```json
{
  "url": "http://...",
  "username": "admin",
  "password": "YOUR_PASSWORD"
}
```

## 🐍 Script Python

Le script doit :
- Être **exécutable** (`chmod +x`)
- Utiliser `CONFIG_PATH` en variable d'env
- Fonctionner en **Python 3.11+** (stdlib si possible)
- Avoir un `argparse` avec des sous-commandes

Pattern :

```python
#!/usr/bin/env python3
"""Docstring du script."""

import argparse
import json
import os
import sys

CONFIG_PATH = os.environ.get("MY_CONFIG_PATH", "config.json")

def load_config():
    ...

def main():
    ...
```

## 🔒 Sécurité

- `config.json` **NE DOIT JAMAIS** être commité → `.gitignore`
- Les secrets passent par des variables d'env ou un fichier hors repo (`~/.hermes/...`)
- Le hook `pre-commit` scanne avec **gitleaks** pour bloquer les secrets

## 🚀 Workflow de création

```bash
# 1. Créer une branche
git checkout -b feat/mon-skill

# 2. Créer le dossier et les fichiers (inclure SKILL.md)
mkdir mon-skill
# ...

# 3. Tester
./mon-skill/mon-script.py --help

# 4. Commit + push
git add mon-skill/
git commit -m "feat: add mon-skill CLI"
git push -u origin feat/mon-skill

# 5. Créer une PR sur GitHub
```

---

*Suivez ce template pour que tous les skills restent cohérents et maintenables.*  
*Follow this template so all skills stay consistent and maintainable.*
