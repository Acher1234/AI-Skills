# 📦 Dependencies — hermes-script (racine)

Dépendances communes au dépôt (outillage transverse).

| Package | Version | Install | Usage |
|---------|---------|---------|-------|
| `gitleaks` | 8.x+ | `brew install gitleaks` (macOS) · `apt-get install gitleaks` (Linux) | Scan de secrets exécuté par le hook `pre-commit` pour bloquer le push de clés/tokens |

## 🔒 Installation des hooks git

Les hooks versionnés se trouvent dans `.githooks/`. Après un clone, active-les une fois :

```bash
./setup.sh
```

Ce script fait simplement `git config core.hooksPath .githooks` (git ne peut pas le faire seul au clone, pour des raisons de sécurité) et vérifie la présence de `gitleaks`.

Le hook `pre-commit` lance `gitleaks protect --staged` et **bloque le commit** si un secret est détecté.
