# 📦 Dependencies — zscaler

| Package | Version | Install | Usage |
|---------|---------|---------|-------|
| `python3` | 3.10+ | `apt-get install python3` | Runtime Python (SDK: 3.8+) |
| [`zscaler-sdk-python`](https://pypi.org/project/zscaler-sdk-python/) | `>=1.9.37` | `pip install -r requirements.txt` | SDK officiel Zscaler (ZPA, ZIA, ZIdentity / OneAPI) |

## Installation

```bash
cd zscaler
python3 -m venv .venv
source .venv/bin/activate

# Si erreur SSL (proxy / Zscaler MITM) :
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# Sinon :
pip install -r requirements.txt
```

## Modules stdlib utilisés (pas d'install)

- `argparse` — CLI
- `json` — lecture / écriture de `config.json`
- `getpass` — saisie sécurisée des secrets
- `pathlib`

## Clients SDK utilisés

| Produit | Client | Auth |
|---------|--------|------|
| ZPA | `LegacyZPAClient` | `client_id`, `client_secret`, `customer_id`, `cloud` |
| ZIA | `LegacyZIAClient` | `username`, `password`, `api_key`, `cloud` |
| ZIdentity | `ZscalerClient` (OneAPI) | `client_id`, `client_secret`, `vanity_domain` |

## Documentation SDK

- https://zscaler-sdk-python.readthedocs.io/en/stable/
- https://github.com/zscaler/zscaler-sdk-python
