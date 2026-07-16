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
python cli.py zia create-url-category --name "Ma catégorie" --url exemple.com [--ip-range 1.2.3.0/24] [--keyword ssh]
python cli.py zia add-url    --category-name "Ma catégorie" --url exemple.com
python cli.py zia remove-url --category-name "Ma catégorie" --url exemple.com
python cli.py zia forwarding-rules [--search TEXTE]
python cli.py zia get-user   --username user@exemple.com
python cli.py zia set-groups --username user@exemple.com --group-name "Groupe" --department-name "Dépt"
python cli.py zia activation-status   # statut pending/active
python cli.py zia activate            # active les changements en attente

# ZIdentity
python cli.py zidentity groups
python cli.py zidentity users
```

### Activation de la configuration (ZIA uniquement)

Après un create/update/delete, **ZIA** nécessite une **activation** de la configuration pour que les changements prennent effet. **ZPA** et **ZIdentity** appliquent les changements immédiatement (pas d'étape d'activation).

```bash
# Vérifier les changements en attente puis activer (ZIA)
python cli.py zia activation-status   # ex. {"status": "PENDING"}
python cli.py zia activate            # active les changements en attente
```

### Modes de `set-groups`

`set-groups` propose trois comportements pour la liste des `groups`. `--add` et `--remove` sont **mutuellement exclusifs**.

| Mode | Flag | Comportement |
|------|------|--------------|
| **Replace** (défaut) | *(aucun)* | La liste fournie **remplace** tous les groupes |
| **Add** | `--add` | Union : groupes actuels **+** groupes fournis |
| **Remove** | `--remove` | Différence : groupes actuels **−** groupes fournis (les autres sont conservés) |

> ⚠️ ZIA impose un `department` à chaque mise à jour d'user. Si l'user n'en a pas, passez `--department-name`/`--department-id`. Retirer un groupe ne retire jamais un département — pour déplacer un user, ajoutez `--department-name` à l'appel `--remove`.

```bash
# Remplacer tous les groupes (et conserver/forcer un département)
python cli.py zia set-groups --username user@exemple.com --group-name "Groupe A" --department-name "Dépt"

# Ajouter un groupe, conserver les existants
python cli.py zia set-groups --username user@exemple.com --group-name "Groupe B" --add

# Retirer un groupe, conserver les autres (département inchangé si déjà défini)
python cli.py zia set-groups --username user@exemple.com --group-name "Groupe A" --remove

# Retirer un groupe ET déplacer l'user vers un autre département
python cli.py zia set-groups --username user@exemple.com --group-name "Groupe A" --department-name "Autre dépt" --remove

# Par ID
python cli.py zia set-groups --user-id 190059002 --group-id 193057301 --remove
```

### Règles d'URL (whitelister une URL dans une catégorie custom)

`create-url-category` et `add-url` valident chaque URL **localement** selon les règles de l'Admin Console Zscaler avant d'appeler l'API. Si une seule URL est invalide, toute la requête est rejetée (même comportement que l'API) avec une erreur explicite.

**Format**

- Minuscules uniquement pour le domaine — `www.safemarch.com`, pas `www.Safemarch.com`.
- Pas de schéma de protocole — `www.safemarch.com`, pas `http://www.safemarch.com`.
- Format `host.domain` ; un TLD seul est refusé (impossible d'ajouter `.gov`).
- Caractères ASCII uniquement.
- Longueur max 1024 caractères ; domaine (avant `:`) ≤ 255 caractères ; chaque label entre points ≤ 63 caractères.
- Underscore `_` : interdit dans le TLD et le SLD — **sauf** dans le SLD lorsqu'il n'y a pas de sous-domaine. Autorisé dans les sous-domaines et sous-répertoires. Un sous-domaine ne peut pas être uniquement `_`.
  - Valide : `ww_w.safemarch.com`, `www.safemarch.com/resources_1`, `safe_march.com`, `www_.safemarch.com`
  - Invalide : `www.safemarch.c_om`, `www.safe_march.com`, `_.safemarch.com`

**Wildcard (point initial `.`)**

- Un **point initial** est le wildcard : `.safemarch.com` s'applique au domaine **et** à ses sous-domaines (jusqu'à 5 niveaux), ainsi qu'à tout chemin à sa droite.
  - `.safemarch.com` → correspond à `safemarch.com`, `atlanta.safemarch.com`, `serv3.serv2.serv1.atlanta.safemarch.com`, `safemarch.com/company/webinars`, …
- **Sans point initial** = correspondance exacte sur le domaine/sous-domaine : `safemarch.com` ne s'applique qu'à `safemarch.com` et `safemarch.com/company/webinars`.
- Une **correspondance exacte est prioritaire** sur une correspondance par wildcard.
- Ne **pas** utiliser `*` comme wildcard en début de domaine — `.safemarch.com` est autorisé, `*safemarch.com` et `*.safemarch.com` non. Un `*` dans une URL est traité comme un caractère littéral.
- Les wildcards à droite sont **toujours implicites** : `safemarch.com` couvre aussi `safemarch.com:10443`, `safemarch.com/index.htm`, `safemarch.com/work/mail?=next`.

**Correspondance chemin / répertoire**

- `safemarch.com/resources` (sans slash final) → correspond à cette chaîne exacte.
- `safemarch.com/resources/` (avec slash final) → correspond à tout fichier/répertoire en dessous.

```bash
# Whitelister un domaine et tous ses sous-domaines (wildcard)
python cli.py zia add-url --category-name "Allowlist" --url .safemarch.com

# Whitelister uniquement un host exact
python cli.py zia add-url --category-name "Allowlist" --url safemarch.com

# Plusieurs URLs d'un coup (tout est rejeté si une seule est invalide)
python cli.py zia add-url --category-name "Allowlist" --url a.example.com --url .example.org
```

### Créer une catégorie d'URL custom

Une catégorie peut contenir des **URLs**, des **plages IP** et/ou des **keywords**. Au moins **un** de `--url` / `--ip-range` / `--keyword` est requis (l'API ZIA refuse une catégorie vide avec `At least 1 URL or keyword should be entered`). Ces trois flags sont **répétables**.

| Flag | Contenu | Notes |
|------|---------|-------|
| `--url` | URL / domaine (wildcard `.` initial possible) | Validé localement (voir règles ci-dessus) |
| `--ip-range` | IP ou CIDR (ex : `203.0.113.10`, `198.51.100.0/24`) | Nécessite souvent la fonctionnalité "custom IP" activée sur le tenant |
| `--keyword` | Mot-clé libre | Utile comme placeholder pour une catégorie IP-only |
| `--description` | Texte libre | Optionnel |
| `--super-category` | Super-catégorie parente | Défaut : `USER_DEFINED` |

```bash
# Domaines Git-over-SSH (wildcards corrects, sans schéma, sans '*')
python cli.py zia create-url-category \
  --name "authorized git over ssh" \
  --url ".github.com" \
  --url ".gitlab.com" \
  --url ".bitbucket.org" \
  --url ".dev.azure.com" \
  --url "ssh.dev.azure.com"

# Catégorie keyword-only (IPs ajoutées plus tard)
python cli.py zia create-url-category \
  --name "SSH allowed IP" \
  --keyword "ssh" \
  --description "Destination IPs authorized for SSH"

# Avec des plages IP (si le tenant autorise les IPs custom)
python cli.py zia create-url-category \
  --name "SSH allowed IP" \
  --ip-range "203.0.113.10" \
  --ip-range "198.51.100.0/24" \
  --keyword "ssh"
```

> Pour ajouter/retirer du contenu sur une catégorie **existante**, utilisez `add-url` / `remove-url`. Il n'existe pas encore de commande dédiée pour mettre à jour les plages IP / keywords dans le CLI (utiliser le SDK `update_url_category` si besoin).

### IP groups (Cloud Firewall)

CRUD complet pour les IP groups **destination** et **source**. Chaque `get` / `update` / `delete` accepte `--ip-group-id` ou `--ip-group-name` (exact, insensible à la casse).

> ⚠️ À ne pas confondre avec les groupes d'utilisateurs : `--group-id` / `--group-name` concernent `set-groups` (user groups), tandis que `--ip-group-id` / `--ip-group-name` visent les IP groups firewall. De même `--add` est pour `set-groups`, `--append` pour les IP groups.

**Types de destination IP group** (`--type`) :

| Type | Contenu requis |
|------|----------------|
| `DSTN_IP` | `--address` (IPs / CIDR) |
| `DSTN_FQDN` | `--address` (FQDNs) |
| `DSTN_DOMAIN` | `--address` (domaines) |
| `DSTN_OTHER` | `--country` (ex : `COUNTRY_US`) et/ou `--ip-category` (ex : `CUSTOM_01`) |

```bash
# Destination IP groups
python cli.py zia dest-ip-groups [--search "MyGroup"] [--exclude-type DSTN_OTHER]
python cli.py zia get-dest-ip-group --ip-group-name "My Dest Group"
python cli.py zia get-dest-ip-group --ip-group-id 123456
python cli.py zia create-dest-ip-group --name "My Dest Group" --type DSTN_IP \
  --address 192.168.1.1 --address 10.0.0.0/24 --description "lab"
python cli.py zia create-dest-ip-group --name "FQDN Dest" --type DSTN_FQDN \
  --address example.com --address app.example.com
python cli.py zia create-dest-ip-group --name "Country Dest" --type DSTN_OTHER \
  --country COUNTRY_US --ip-category CUSTOM_01
# Ajouter une adresse (conserve les existantes)
python cli.py zia update-dest-ip-group --ip-group-name "My Dest Group" --address 203.0.113.10 --append
# Remplacer la liste d'adresses
python cli.py zia update-dest-ip-group --ip-group-id 123456 --address 192.168.1.1 --address 192.168.1.2
python cli.py zia delete-dest-ip-group --ip-group-name "My Dest Group"

# Source IP groups
python cli.py zia source-ip-groups [--search "Corp"]
python cli.py zia get-source-ip-group --ip-group-name "Corp Sources"
python cli.py zia create-source-ip-group --name "Corp Sources" \
  --ip 203.0.113.10 --ip 198.51.100.0/24 --description "office"
# Ajouter une IP (conserve les existantes)
python cli.py zia update-source-ip-group --ip-group-name "Corp Sources" --ip 203.0.113.20 --append
# Remplacer la liste d'IPs
python cli.py zia update-source-ip-group --ip-group-id 123456 --ip 203.0.113.10 --ip 203.0.113.11
python cli.py zia delete-source-ip-group --ip-group-name "Corp Sources"
```

- **Append** vs **replace** : sans `--append`, `update-*` **remplace** la liste d'adresses/IPs ; avec `--append`, les nouvelles entrées sont ajoutées aux existantes (destination via l'API `override=false`, source mergé côté client avec dédup).
- L'update précharge toujours le groupe courant, donc les champs non fournis (nom, type, description, autres adresses) sont conservés.

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
| `zia create-url-category` | Crée une catégorie d'URL (`--url` / `--ip-range` / `--keyword`) |
| `zia add-url` / `remove-url` | Ajoute / retire des URLs d'une catégorie |
| `zia forwarding-rules` | Liste les forwarding rules |
| `zia get-user` | Récupère un utilisateur (par nom ou ID) |
| `zia set-groups` | Assigne groupes / département à un utilisateur (`--add` / `--remove` / replace) |
| `zia dest-ip-groups` | Liste les destination IP groups (`--search`, `--exclude-type`) |
| `zia get-dest-ip-group` | Récupère un destination IP group (par id ou nom) |
| `zia create-dest-ip-group` | Crée un destination IP group (`--type`, `--address`, `--country`, `--ip-category`) |
| `zia update-dest-ip-group` | Met à jour un destination IP group (`--append` pour ajouter) |
| `zia delete-dest-ip-group` | Supprime un destination IP group |
| `zia source-ip-groups` | Liste les source IP groups (`--search`) |
| `zia get-source-ip-group` | Récupère un source IP group (par id ou nom) |
| `zia create-source-ip-group` | Crée un source IP group (`--ip`) |
| `zia update-source-ip-group` | Met à jour un source IP group (`--append` pour ajouter) |
| `zia delete-source-ip-group` | Supprime un source IP group |
| `zia activation-status` | Statut d'activation de la config ZIA |
| `zia activate` | Active les changements ZIA en attente |
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
