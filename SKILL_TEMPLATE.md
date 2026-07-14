# 🧩 Comment coder un skill / How to code a skill

Ce guide explique la structure attendue pour chaque nouveau script CLI dans `hermes-script`.
This guide explains the expected structure for each new CLI script in `hermes-script`.

## 📁 Structure d'un skill

Chaque skill = **1 dossier** à la racine du repo, contenant :

```
hermes-script/
└── mon-skill/
    ├── README.md           ← Doc en anglais (Markdown)
    ├── README.fr.md        ← Doc en français (Markdown)
    ├── dependencies.md     ← Dépendances système/pip
    ├── .gitignore          ← Ignore les fichiers sensibles (config.json, __pycache__)
    ├── config.example.json ← Template de config (versionné, sans secrets)
    └── mon-script.py       ← Le script CLI exécutable
```

## 📝 README.md / README.fr.md

Chaque README doit contenir :
- **Installation** : comment installer les dépendances et configurer
- **Configuration** : format de `config.json` avec exemple
- **Utilisation** : toutes les commandes disponibles avec exemples
- **Filtres / Options** : liste des options (si applicable)
- **États** : table des états/icônes (si applicable)
- **Dépendances** : renvoi vers `dependencies.md`
- **Environnement** : variables d'env supportées

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

# 2. Créer le dossier et les fichiers
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