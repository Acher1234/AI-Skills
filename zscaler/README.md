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
python cli.py zia create-url-category --name "My category" --url example.com [--ip-range 1.2.3.0/24] [--keyword ssh]
python cli.py zia add-url    --category-name "My category" --url example.com
python cli.py zia remove-url --category-name "My category" --url example.com
python cli.py zia forwarding-rules [--search TEXT]
python cli.py zia get-user   --username user@example.com
python cli.py zia set-groups --username user@example.com --group-name "Group" --department-name "Dept"
python cli.py zia activation-status   # pending/active status
python cli.py zia activate            # activate pending changes

# ZIdentity
python cli.py zidentity groups
python cli.py zidentity users
```

### Config activation (ZIA only)

After create/update/delete, **ZIA** requires you to **activate** the configuration for changes to take effect. **ZPA** and **ZIdentity** apply changes immediately (no activation step).

```bash
# Check pending changes then activate (ZIA)
python cli.py zia activation-status   # e.g. {"status": "PENDING"}
python cli.py zia activate            # activates pending changes
```

### `set-groups` modes

`set-groups` supports three mutually consistent behaviours for the `groups` list. `--add` and `--remove` are **mutually exclusive**.

| Mode | Flag | Behaviour |
|------|------|-----------|
| **Replace** (default) | *(none)* | The provided list **replaces** all groups |
| **Add** | `--add` | Union: current groups **+** provided groups |
| **Remove** | `--remove` | Difference: current groups **−** provided groups (others kept) |

> ⚠️ ZIA requires a `department` on every user update. If the user has no department, pass `--department-name`/`--department-id`. Removing a group never removes a department — to move a user, add `--department-name` to the `--remove` call.

```bash
# Replace all groups (and keep/force a department)
python cli.py zia set-groups --username user@example.com --group-name "Group A" --department-name "Dept"

# Add a group, keep existing ones
python cli.py zia set-groups --username user@example.com --group-name "Group B" --add

# Remove a group, keep the others (department unchanged if already set)
python cli.py zia set-groups --username user@example.com --group-name "Group A" --remove

# Remove a group AND move the user to another department
python cli.py zia set-groups --username user@example.com --group-name "Group A" --department-name "Other Dept" --remove

# By ID
python cli.py zia set-groups --user-id 190059002 --group-id 193057301 --remove
```

### URL rules (whitelisting a URL in a custom category)

`create-url-category` and `add-url` validate every URL **locally** against the Zscaler Admin Console rules before calling the API. If a single URL is invalid, the whole request is rejected (same behaviour as the API) with an explicit error.

**Format**

- Lowercase only in the domain — `www.safemarch.com`, not `www.Safemarch.com`.
- No protocol scheme — `www.safemarch.com`, not `http://www.safemarch.com`.
- `host.domain` format; a bare TLD is refused (you cannot add `.gov`).
- ASCII characters only.
- Max length 1024 chars; domain (before `:`) ≤ 255 chars; each label between dots ≤ 63 chars.
- Underscore `_`: not allowed in the TLD or SLD — **except** in the SLD when there is no subdomain. Allowed in subdomains and subdirectories. A subdomain cannot be only `_`.
  - Valid: `ww_w.safemarch.com`, `www.safemarch.com/resources_1`, `safe_march.com`, `www_.safemarch.com`
  - Invalid: `www.safemarch.c_om`, `www.safe_march.com`, `_.safemarch.com`

**Wildcard (leading period `.`)**

- A **leading period** is the wildcard: `.safemarch.com` applies to the domain **and** its subdomains (up to 5 levels deep), as well as any path to the right.
  - `.safemarch.com` → matches `safemarch.com`, `atlanta.safemarch.com`, `serv3.serv2.serv1.atlanta.safemarch.com`, `safemarch.com/company/webinars`, …
- **No leading period** = exact match on the domain/subdomain: `safemarch.com` applies to `safemarch.com` and `safemarch.com/company/webinars` only.
- An **exact match takes priority** over a wildcard match.
- Do **not** use `*` as a leading wildcard — `.safemarch.com` is allowed, `*safemarch.com` and `*.safemarch.com` are not. An `*` inside a URL is treated as a literal character.
- Right-side wildcards are **always assumed**: `safemarch.com` also covers `safemarch.com:10443`, `safemarch.com/index.htm`, `safemarch.com/work/mail?=next`.

**Path / directory matching**

- `safemarch.com/resources` (no trailing slash) → matches that exact string.
- `safemarch.com/resources/` (trailing slash) → matches any file/directory underneath it.

```bash
# Whitelist a domain and all its subdomains (wildcard)
python cli.py zia add-url --category-name "Allowlist" --url .safemarch.com

# Whitelist an exact host only
python cli.py zia add-url --category-name "Allowlist" --url safemarch.com

# Multiple URLs at once (rejected as a whole if any is invalid)
python cli.py zia add-url --category-name "Allowlist" --url a.example.com --url .example.org
```

### Creating a custom URL category

A category can hold **URLs**, **IP ranges** and/or **keywords**. At least **one** of `--url` / `--ip-range` / `--keyword` is required (the ZIA API rejects an empty category with `At least 1 URL or keyword should be entered`). All three flags are **repeatable**.

| Flag | Content | Notes |
|------|---------|-------|
| `--url` | URL / domain (with optional leading `.` wildcard) | Validated locally (see rules above) |
| `--ip-range` | IP or CIDR (e.g. `203.0.113.10`, `198.51.100.0/24`) | Often requires the "custom IP" feature enabled on the tenant |
| `--keyword` | Free keyword | Useful as a placeholder for an IP-only category |
| `--description` | Free text | Optional |
| `--super-category` | Parent super-category | Defaults to `USER_DEFINED` |

```bash
# Git-over-SSH domains (correct wildcards, no scheme, no '*')
python cli.py zia create-url-category \
  --name "authorized git over ssh" \
  --url ".github.com" \
  --url ".gitlab.com" \
  --url ".bitbucket.org" \
  --url ".dev.azure.com" \
  --url "ssh.dev.azure.com"

# Keyword-only category (IPs added later)
python cli.py zia create-url-category \
  --name "SSH allowed IP" \
  --keyword "ssh" \
  --description "Destination IPs authorized for SSH"

# With IP ranges (when the tenant allows custom IPs)
python cli.py zia create-url-category \
  --name "SSH allowed IP" \
  --ip-range "203.0.113.10" \
  --ip-range "198.51.100.0/24" \
  --keyword "ssh"
```

> To add/remove content on an **existing** category, use `add-url` / `remove-url`. There is no dedicated update command for IP ranges / keywords in the CLI yet (use the SDK `update_url_category` if needed).

### IP groups (Cloud Firewall)

Full CRUD for **destination** and **source** IP groups. Every `get` / `update` / `delete` accepts either `--ip-group-id` or `--ip-group-name` (exact, case-insensitive).

> ⚠️ Don't confuse these with user groups: `--group-id` / `--group-name` are for `set-groups` (user groups), while `--ip-group-id` / `--ip-group-name` target firewall IP groups. Likewise `--add` is for `set-groups`, `--append` is for IP groups.

**Destination IP group types** (`--type`):

| Type | Required content |
|------|------------------|
| `DSTN_IP` | `--address` (IPs / CIDR) |
| `DSTN_FQDN` | `--address` (FQDNs) |
| `DSTN_DOMAIN` | `--address` (domains) |
| `DSTN_OTHER` | `--country` (e.g. `COUNTRY_US`) and/or `--ip-category` (e.g. `CUSTOM_01`) |

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
# Append an address (keeps existing ones)
python cli.py zia update-dest-ip-group --ip-group-name "My Dest Group" --address 203.0.113.10 --append
# Replace the address list
python cli.py zia update-dest-ip-group --ip-group-id 123456 --address 192.168.1.1 --address 192.168.1.2
python cli.py zia delete-dest-ip-group --ip-group-name "My Dest Group"

# Source IP groups
python cli.py zia source-ip-groups [--search "Corp"]
python cli.py zia get-source-ip-group --ip-group-name "Corp Sources"
python cli.py zia create-source-ip-group --name "Corp Sources" \
  --ip 203.0.113.10 --ip 198.51.100.0/24 --description "office"
# Append an IP (keeps existing ones)
python cli.py zia update-source-ip-group --ip-group-name "Corp Sources" --ip 203.0.113.20 --append
# Replace the IP list
python cli.py zia update-source-ip-group --ip-group-id 123456 --ip 203.0.113.10 --ip 203.0.113.11
python cli.py zia delete-source-ip-group --ip-group-name "Corp Sources"
```

- **Append** vs **replace**: without `--append`, `update-*` **replaces** the address/IP list; with `--append`, new entries are added to the existing ones (destination via the API `override=false`, source merged client-side with dedup).
- Update always preloads the current group first, so fields you don't pass (name, type, description, other addresses) are preserved.

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
| `zia create-url-category` | Create a URL category (`--url` / `--ip-range` / `--keyword`) |
| `zia add-url` / `remove-url` | Add / remove URLs from a category |
| `zia forwarding-rules` | List forwarding rules |
| `zia get-user` | Fetch a user (by name or ID) |
| `zia set-groups` | Assign groups / department to a user (`--add` / `--remove` / replace) |
| `zia dest-ip-groups` | List destination IP groups (`--search`, `--exclude-type`) |
| `zia get-dest-ip-group` | Get a destination IP group (by id or name) |
| `zia create-dest-ip-group` | Create a destination IP group (`--type`, `--address`, `--country`, `--ip-category`) |
| `zia update-dest-ip-group` | Update a destination IP group (`--append` to add) |
| `zia delete-dest-ip-group` | Delete a destination IP group |
| `zia source-ip-groups` | List source IP groups (`--search`) |
| `zia get-source-ip-group` | Get a source IP group (by id or name) |
| `zia create-source-ip-group` | Create a source IP group (`--ip`) |
| `zia update-source-ip-group` | Update a source IP group (`--append` to add) |
| `zia delete-source-ip-group` | Delete a source IP group |
| `zia activation-status` | Get ZIA config activation status |
| `zia activate` | Activate pending ZIA config changes |
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
