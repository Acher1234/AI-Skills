# zscaler

> 🇬🇧 English version — 🇫🇷 [Version française](README-FR.md)

Python CLI to manage **ZPA**, **ZIA** and **ZIdentity** through the official [`zscaler-sdk-python`](https://pypi.org/project/zscaler-sdk-python/) SDK.

## Structure

```
zscaler/
├── cli.py                 # Hermes Agent CLI entry point
├── zpa.py                 # ZPA client & operations
├── zia.py                 # ZIA client & operations
├── zidentity.py           # ZIdentity client & operations
├── add_users_to_group.sh  # Bulk-add ZIA users to a group
├── config.json            # Local tokens (NOT versioned — .gitignore)
├── config.example.json    # Configuration template
├── requirements.txt
├── dependencies.md
├── README.md              # This file (EN)
└── README-FR.md           # French version
```

## Requirements

See [`dependencies.md`](dependencies.md).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

## Configuration (tokens)

1. Copy the example:
   ```bash
   cp config.example.json config.json
   ```
2. Fill in the tokens in `config.json`, **or** enter them interactively:
   ```bash
   python cli.py setup
   ```

### ZPA (`config.json` → `zpa`)

| JSON key | Env / SDK |
|----------|-----------|
| `client_id` | `ZPA_CLIENT_ID` |
| `client_secret` | `ZPA_CLIENT_SECRET` |
| `customer_id` | `ZPA_CUSTOMER_ID` |
| `cloud` | `ZPA_CLOUD` (`PRODUCTION`, `ZPATWO`, `BETA`, `GOV`, `GOVUS`) |

### ZIA (`config.json` → `zia`)

| JSON key | Description |
|----------|-------------|
| `username` | API admin account |
| `password` | Password |
| `api_key` | ZIA API key |
| `cloud` | ZIA cloud (`zscaler`, `zscalerone`, …) |

### ZIdentity (`config.json` → `zidentity`)

| JSON key | Description |
|----------|-------------|
| `client_id` | OneAPI Client ID |
| `client_secret` | OneAPI Client Secret |
| `vanity_domain` | ZIdentity vanity domain |
| `cloud` | Optional (`beta`, …) |
| `customer_id` | Optional (required for ZPA over OneAPI) |

The CLI **always reads** `config.json` at startup. If a token is empty, it **prompts** for it interactively and offers to save it.

## Usage

```bash
# Interactive token setup
python cli.py setup

# Connection test
python cli.py test            # everything
python cli.py test zpa        # a single product
python cli.py test zia
python cli.py test zidentity

# ZPA
python cli.py zpa segments
python cli.py zpa groups

# ZIA
python cli.py zia users
python cli.py zia groups
python cli.py zia departments [--search TEXT]
python cli.py zia url-categories
python cli.py zia create-url-category --name "My category" [--url example.com]
python cli.py zia add-url    --category-name "My category" --url example.com
python cli.py zia remove-url --category-name "My category" --url example.com
python cli.py zia forwarding-rules [--search TEXT]
python cli.py zia get-user   --username user@example.com
python cli.py zia set-groups --username user@example.com --group-name "Group" --department-name "Dept" --add

# ZIdentity
python cli.py zidentity groups
python cli.py zidentity users
```

### Bulk-add script

`add_users_to_group.sh` adds ZIA users (from JSON exports) to a group + department by reusing `cli.py zia set-groups`:

```bash
./add_users_to_group.sh "GROUP" "DEPARTEMENT" users1.json [users2.json ...]
```

## Available commands

| Command | Description |
|---------|-------------|
| `setup` | Configure tokens (interactive) |
| `test [product]` | Test API connection (all / zpa / zia / zidentity) |
| `zpa segments` | List application segments |
| `zpa groups` | List segment groups |
| `zia users` | List users |
| `zia groups` | List groups |
| `zia departments` | List departments |
| `zia url-categories` | List URL categories |
| `zia create-url-category` | Create a URL category |
| `zia add-url` / `remove-url` | Add / remove URLs from a category |
| `zia forwarding-rules` | List forwarding rules |
| `zia get-user` | Fetch a user (by name or ID) |
| `zia set-groups` | Assign groups / department to a user |
| `zidentity groups` / `users` | List ZIdentity groups / users |

## API / SDK documentation

**When in doubt about how to implement a function, all the documentation is here:**

- Python SDK (auth, clients, examples): https://zscaler-sdk-python.readthedocs.io/en/stable/
- GitHub reference: https://github.com/zscaler/zscaler-sdk-python
- Automation hub / API Reference: https://automate.zscaler.com/docs/
  - [ZPA API](https://automate.zscaler.com/docs/docs/api-reference-and-guides/api-reference/zpa)
  - [ZIA API](https://automate.zscaler.com/docs/docs/api-reference-and-guides/api-reference/zia)
  - [ZIdentity API](https://automate.zscaler.com/docs/docs/api-reference-and-guides/api-reference/zid)

Adding a command = rely on the client already initialized in `zpa.py` / `zia.py` / `zidentity.py`, then expose the action in `cli.py`.

## Security

- Never commit `config.json` (already in `.gitignore`).
- Use `config.example.json` as a template without secrets.
