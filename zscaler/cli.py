#!/usr/bin/env python3
"""Hermes Agent CLI — Zscaler management (ZPA / ZIA / ZIdentity)."""

from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path
from typing import Any

import zia
import zidentity
import zpa

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
EXAMPLE_CONFIG_PATH = ROOT / "config.example.json"

PLACEHOLDER_PREFIXES = ("YOUR_",)


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load tokens from config.json."""
    if not path.exists():
        raise FileNotFoundError(
            f"Config introuvable: {path}\n"
            f"Copiez {EXAMPLE_CONFIG_PATH.name} vers config.json et renseignez les tokens."
        )
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def save_config(config: dict[str, Any], path: Path = CONFIG_PATH) -> None:
    """Persist config.json."""
    with path.open("w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)
        fh.write("\n")


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    if not text:
        return True
    return any(text.startswith(prefix) for prefix in PLACEHOLDER_PREFIXES)


def _prompt_value(label: str, *, secret: bool = False, default: str = "") -> str:
    hint = f" [{default}]" if default and not secret else ""
    prompt = f"  {label}{hint}: "
    if secret:
        value = getpass.getpass(prompt)
    else:
        value = input(prompt).strip()
    if not value and default:
        return default
    return value.strip()


def ensure_section_credentials(
    config: dict[str, Any],
    section: str,
    required_fields: list[tuple[str, str, bool]],
    *,
    interactive: bool = True,
) -> dict[str, Any]:
    """
    Ensure required tokens exist for a product section.
    If missing and interactive, ask the user and optionally save to config.json.
    """
    section_cfg = dict(config.get(section) or {})
    missing = [key for key, _, _ in required_fields if _is_missing(section_cfg.get(key))]

    if not missing:
        return section_cfg

    if not interactive:
        raise ValueError(
            f"Tokens manquants dans config.json [{section}]: {', '.join(missing)}"
        )

    print(f"\nConfiguration {section.upper()} — tokens manquants: {', '.join(missing)}")
    print("Saisissez les valeurs (laisser vide pour conserver la valeur actuelle si présente).\n")

    for key, label, secret in required_fields:
        current = str(section_cfg.get(key) or "").strip()
        default = "" if _is_missing(current) else current
        value = _prompt_value(label, secret=secret, default=default)
        if value:
            section_cfg[key] = value

    still_missing = [key for key, _, _ in required_fields if _is_missing(section_cfg.get(key))]
    if still_missing:
        raise ValueError(
            f"Tokens toujours manquants pour [{section}]: {', '.join(still_missing)}"
        )

    config[section] = section_cfg
    answer = input("\nEnregistrer dans config.json ? [Y/n]: ").strip().lower()
    if answer in ("", "y", "yes", "o", "oui"):
        save_config(config)
        print(f"Config sauvegardée: {CONFIG_PATH}")

    return section_cfg


ZPA_FIELDS = [
    ("client_id", "ZPA_CLIENT_ID", False),
    ("client_secret", "ZPA_CLIENT_SECRET", True),
    ("customer_id", "ZPA_CUSTOMER_ID", False),
    ("cloud", "ZPA_CLOUD (ex: PRODUCTION)", False),
]

ZIA_FIELDS = [
    ("username", "ZIA_USERNAME", False),
    ("password", "ZIA_PASSWORD", True),
    ("api_key", "ZIA_API_KEY", True),
    ("cloud", "ZIA_CLOUD (ex: zscaler)", False),
]

ZIDENTITY_FIELDS = [
    ("client_id", "ZSCALER_CLIENT_ID", False),
    ("client_secret", "ZSCALER_CLIENT_SECRET", True),
    ("vanity_domain", "ZSCALER_VANITY_DOMAIN", False),
]


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, default=str))


def cmd_setup(_: argparse.Namespace) -> int:
    """Interactive setup of all product tokens."""
    if not CONFIG_PATH.exists() and EXAMPLE_CONFIG_PATH.exists():
        save_config(load_config(EXAMPLE_CONFIG_PATH))
        print(f"config.json créé depuis {EXAMPLE_CONFIG_PATH.name}")

    config = load_config()
    ensure_section_credentials(config, "zpa", ZPA_FIELDS)
    ensure_section_credentials(config, "zia", ZIA_FIELDS)
    ensure_section_credentials(config, "zidentity", ZIDENTITY_FIELDS)
    print("\nSetup terminé.")
    return 0


def cmd_test(args: argparse.Namespace) -> int:
    config = load_config()
    targets = []
    if args.product in ("all", "zpa"):
        targets.append(("zpa", ZPA_FIELDS, zpa.test_connection))
    if args.product in ("all", "zia"):
        targets.append(("zia", ZIA_FIELDS, zia.test_connection))
    if args.product in ("all", "zidentity"):
        targets.append(("zidentity", ZIDENTITY_FIELDS, zidentity.test_connection))

    ok_all = True
    for section, fields, tester in targets:
        try:
            section_cfg = ensure_section_credentials(config, section, fields)
            success, message = tester(section_cfg)
        except Exception as exc:  # noqa: BLE001
            success, message = False, str(exc)
        status = "OK" if success else "FAIL"
        print(f"[{status}] {section.upper()}: {message}")
        ok_all = ok_all and success
    return 0 if ok_all else 1


def cmd_zpa(args: argparse.Namespace) -> int:
    config = load_config()
    zpa_cfg = ensure_section_credentials(config, "zpa", ZPA_FIELDS)

    if args.action == "segments":
        _print_json(zpa.list_application_segments(zpa_cfg, page=args.page, page_size=args.page_size))
    elif args.action == "groups":
        _print_json(zpa.list_segment_groups(zpa_cfg, page=args.page, page_size=args.page_size))
    else:
        raise ValueError(f"Action ZPA inconnue: {args.action}")
    return 0


def cmd_zia(args: argparse.Namespace) -> int:
    config = load_config()
    zia_cfg = ensure_section_credentials(config, "zia", ZIA_FIELDS)

    if args.action == "users":
        _print_json(zia.list_users(zia_cfg, page=args.page, page_size=args.page_size))
    elif args.action == "groups":
        _print_json(zia.list_groups(zia_cfg, page=args.page, page_size=args.page_size))
    elif args.action == "departments":
        _print_json(
            zia.list_departments(
                zia_cfg,
                page=args.page,
                page_size=args.page_size,
                search=args.search,
            )
        )
    elif args.action == "url-categories":
        _print_json(zia.list_url_categories(zia_cfg))
    elif args.action == "create-url-category":
        if not args.name:
            raise ValueError("--name requis pour create-url-category")
        created = zia.create_url_category(
            zia_cfg,
            args.name,
            urls=args.url or None,
            super_category=args.super_category,
            description=args.description,
        )
        _print_json(created)
    elif args.action == "add-url":
        if not args.category_id and not args.category_name:
            raise ValueError("--category-id ou --category-name requis pour add-url")
        if not args.url:
            raise ValueError("--url requis pour add-url (répétable)")
        _print_json(
            zia.add_urls_to_category(
                zia_cfg,
                args.url,
                category_id=args.category_id,
                category_name=args.category_name,
            )
        )
    elif args.action == "remove-url":
        if not args.category_id and not args.category_name:
            raise ValueError("--category-id ou --category-name requis pour remove-url")
        if not args.url:
            raise ValueError("--url requis pour remove-url (répétable)")
        _print_json(
            zia.remove_urls_from_category(
                zia_cfg,
                args.url,
                category_id=args.category_id,
                category_name=args.category_name,
            )
        )
    elif args.action == "forwarding-rules":
        _print_json(zia.list_forwarding_rules(zia_cfg, search=args.search))
    elif args.action == "get-user":
        if args.user_id:
            _print_json(zia.get_user(zia_cfg, args.user_id))
        elif args.username:
            _print_json(zia.get_user_by_username(zia_cfg, args.username))
        else:
            raise ValueError("--username ou --user-id requis pour get-user")
    elif args.action == "set-groups":
        user_id = args.user_id
        if not user_id and args.username:
            user_id = zia.get_user_by_username(zia_cfg, args.username)["id"]
        if not user_id:
            raise ValueError("--user-id ou --username est requis pour set-groups")
        if not args.group_id and not args.group_name:
            raise ValueError("Fournir au moins --group-id ou --group-name")
        updated = zia.set_user_groups(
            zia_cfg,
            user_id,
            group_ids=args.group_id,
            group_names=args.group_name,
            add=args.add,
            department_id=args.department_id,
            department_name=args.department_name,
        )
        _print_json(updated)
    else:
        raise ValueError(f"Action ZIA inconnue: {args.action}")
    return 0


def cmd_zidentity(args: argparse.Namespace) -> int:
    config = load_config()
    zid_cfg = ensure_section_credentials(config, "zidentity", ZIDENTITY_FIELDS)

    if args.action == "groups":
        _print_json(zidentity.list_groups(zid_cfg))
    elif args.action == "users":
        _print_json(zidentity.list_users(zid_cfg))
    else:
        raise ValueError(f"Action ZIdentity inconnue: {args.action}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hermes",
        description="Hermes Agent CLI — gestion Zscaler (ZPA / ZIA / ZIdentity)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_setup = sub.add_parser("setup", help="Configurer les tokens (interactif)")
    p_setup.set_defaults(func=cmd_setup)

    p_test = sub.add_parser("test", help="Tester la connexion API")
    p_test.add_argument(
        "product",
        nargs="?",
        default="all",
        choices=["all", "zpa", "zia", "zidentity"],
        help="Produit à tester (défaut: all)",
    )
    p_test.set_defaults(func=cmd_test)

    p_zpa = sub.add_parser("zpa", help="Commandes ZPA")
    p_zpa.add_argument("action", choices=["segments", "groups"])
    p_zpa.add_argument("--page", type=int, default=1)
    p_zpa.add_argument("--page-size", type=int, default=20)
    p_zpa.set_defaults(func=cmd_zpa)

    p_zia = sub.add_parser("zia", help="Commandes ZIA")
    p_zia.add_argument(
        "action",
        choices=[
            "users",
            "groups",
            "departments",
            "url-categories",
            "create-url-category",
            "add-url",
            "remove-url",
            "forwarding-rules",
            "get-user",
            "set-groups",
        ],
    )
    p_zia.add_argument("--page", type=int, default=1)
    p_zia.add_argument("--page-size", type=int, default=20)
    p_zia.add_argument("--user-id", type=str, help="ID user ZIA (get-user / set-groups)")
    p_zia.add_argument(
        "--username",
        type=str,
        help="Nom ou email user ZIA (get-user / set-groups)",
    )
    p_zia.add_argument(
        "--add",
        action="store_true",
        help="Ajoute aux groupes existants au lieu de remplacer (set-groups)",
    )
    p_zia.add_argument(
        "--department-id",
        type=str,
        default=None,
        help="ID département ZIA (set-groups)",
    )
    p_zia.add_argument(
        "--department-name",
        type=str,
        default=None,
        help="Nom département ZIA (set-groups)",
    )
    p_zia.add_argument(
        "--search",
        type=str,
        default=None,
        help="Filtre recherche (forwarding-rules / departments)",
    )
    p_zia.add_argument(
        "--group-id",
        action="append",
        default=[],
        help="ID groupe ZIA (répétable, set-groups)",
    )
    p_zia.add_argument(
        "--group-name",
        action="append",
        default=[],
        help="Nom groupe ZIA (répétable, set-groups)",
    )
    p_zia.add_argument(
        "--name",
        type=str,
        help="Nom de la URL category (create-url-category)",
    )
    p_zia.add_argument(
        "--description",
        type=str,
        default=None,
        help="Description (create-url-category)",
    )
    p_zia.add_argument(
        "--super-category",
        type=str,
        default="USER_DEFINED",
        help="Super category parent (défaut: USER_DEFINED)",
    )
    p_zia.add_argument(
        "--category-id",
        type=str,
        help="ID catégorie URL (ex: CUSTOM_01)",
    )
    p_zia.add_argument(
        "--category-name",
        type=str,
        help="Nom configuré de la catégorie URL",
    )
    p_zia.add_argument(
        "--url",
        action="append",
        default=[],
        help="URL à ajouter/retirer (répétable)",
    )
    p_zia.set_defaults(func=cmd_zia)

    p_zid = sub.add_parser("zidentity", help="Commandes ZIdentity")
    p_zid.add_argument("action", choices=["groups", "users"])
    p_zid.set_defaults(func=cmd_zidentity)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrompu.", file=sys.stderr)
        return 130
    except Exception as exc:  # noqa: BLE001
        print(f"Erreur: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
