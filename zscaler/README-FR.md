# zscaler

> 🇫🇷 Version française — 🇬🇧 [English version](README.md)

CLI Python pour administrer **ZPA**, **ZIA** et **ZIdentity** via le SDK officiel [`zscaler-sdk-python`](https://pypi.org/project/zscaler-sdk-python/).

## Structure

```
zscaler/
├── cli.py                 # Point d'entrée Hermes Agent CLI
├── zpa.py                 # Client & opérations ZPA
├── zia.py                 # Client & opérations ZIA
├── zidentity.py           # Client & opérations ZIdentity
├── add_users_to_group.sh  # Ajout en masse d'users ZIA à un groupe
├── config.json            # Tokens locaux (NON versionné — .gitignore)
├── config.example.json    # Modèle de configuration
├── requirements.txt
├── dependencies.md
├── README.md              # Version anglaise
└── README-FR.md           # Ce fichier (FR)
```

## Prérequis

Voir [`dependencies.md`](dependencies.md).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

## Configuration (tokens)

1. Copier l'exemple :
   ```bash
   cp config.example.json config.json
   ```
2. Renseigner les tokens dans `config.json`, **ou** les saisir interactivement :
   ```bash
   python cli.py setup
   ```

### ZPA (`config.json` → `zpa`)

| Clé JSON | Env / SDK |
|----------|-----------|
| `client_id` | `ZPA_CLIENT_ID` |
| `client_secret` | `ZPA_CLIENT_SECRET` |
| `customer_id` | `ZPA_CUSTOMER_ID` |
| `cloud` | `ZPA_CLOUD` (`PRODUCTION`, `ZPATWO`, `BETA`, `GOV`, `GOVUS`) |

### ZIA (`config.json` → `zia`)

| Clé JSON | Description |
|----------|-------------|
| `username` | Compte admin API |
| `password` | Mot de passe |
| `api_key` | Clé API ZIA |
| `cloud` | Cloud ZIA (`zscaler`, `zscalerone`, …) |

### ZIdentity (`config.json` → `zidentity`)

| Clé JSON | Description |
|----------|-------------|
| `client_id` | OneAPI Client ID |
| `client_secret` | OneAPI Client Secret |
| `vanity_domain` | Domaine vanity ZIdentity |
| `cloud` | Optionnel (`beta`, …) |
| `customer_id` | Optionnel (requis pour ZPA via OneAPI) |

Le CLI **lit toujours** `config.json` au démarrage. Si un token est vide, il le **demande** en interactif puis propose de l'enregistrer.

## Utilisation

```bash
# Setup interactif des tokens
python cli.py setup

# Test de connexion
python cli.py test            # tout
python cli.py test zpa        # un seul produit
python cli.py test zia
python cli.py test zidentity

# ZPA
python cli.py zpa segments
python cli.py zpa groups

# ZIA
python cli.py zia users
python cli.py zia groups
python cli.py zia departments [--search TEXTE]
python cli.py zia url-categories
python cli.py zia create-url-category --name "Ma catégorie" [--url exemple.com]
python cli.py zia add-url    --category-name "Ma catégorie" --url exemple.com
python cli.py zia remove-url --category-name "Ma catégorie" --url exemple.com
python cli.py zia forwarding-rules [--search TEXTE]
python cli.py zia get-user   --username user@exemple.com
python cli.py zia set-groups --username user@exemple.com --group-name "Groupe" --department-name "Dépt" --add

# ZIdentity
python cli.py zidentity groups
python cli.py zidentity users
```

### Script d'ajout en masse

`add_users_to_group.sh` ajoute des utilisateurs ZIA (depuis des exports JSON) à un groupe + département en réutilisant `cli.py zia set-groups` :

```bash
./add_users_to_group.sh "Vo2 - Canada" "Canada" users1.json [users2.json ...]
```

## Commandes disponibles

| Commande | Description |
|----------|-------------|
| `setup` | Configure les tokens (interactif) |
| `test [produit]` | Teste la connexion API (all / zpa / zia / zidentity) |
| `zpa segments` | Liste les application segments |
| `zpa groups` | Liste les segment groups |
| `zia users` | Liste les utilisateurs |
| `zia groups` | Liste les groupes |
| `zia departments` | Liste les départements |
| `zia url-categories` | Liste les catégories d'URL |
| `zia create-url-category` | Crée une catégorie d'URL |
| `zia add-url` / `remove-url` | Ajoute / retire des URLs d'une catégorie |
| `zia forwarding-rules` | Liste les forwarding rules |
| `zia get-user` | Récupère un utilisateur (par nom ou ID) |
| `zia set-groups` | Assigne groupes / département à un utilisateur |
| `zidentity groups` / `users` | Liste groupes / utilisateurs ZIdentity |

## Documentation API / SDK

**En cas de doute sur l'implémentation d'une fonction, toute la documentation est ici :**

- SDK Python (auth, clients, exemples) : https://zscaler-sdk-python.readthedocs.io/en/stable/
- Référence GitHub : https://github.com/zscaler/zscaler-sdk-python
- Hub automation / API Reference : https://automate.zscaler.com/docs/
  - [ZPA API](https://automate.zscaler.com/docs/docs/api-reference-and-guides/api-reference/zpa)
  - [ZIA API](https://automate.zscaler.com/docs/docs/api-reference-and-guides/api-reference/zia)
  - [ZIdentity API](https://automate.zscaler.com/docs/docs/api-reference-and-guides/api-reference/zid)

Ajouter une commande = s'appuyer sur le client déjà initialisé dans `zpa.py` / `zia.py` / `zidentity.py`, puis exposer l'action dans `cli.py`.

## Sécurité

- Ne pas committer `config.json` (déjà dans `.gitignore`).
- Utiliser `config.example.json` comme modèle sans secrets.
