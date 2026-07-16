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
            ip_ranges=args.ip_range or None,
            keywords=args.keyword or None,
            super_category=args.super_category,
            description=args.description,
        )
        _print_json(created)
    elif args.action == "add-url":
        category_id = args.category_id_list[0] if args.category_id_list else None
        category_name = args.category_name_list[0] if args.category_name_list else None
        if not category_id and not category_name:
            raise ValueError("--category-id ou --category-name requis pour add-url")
        if not args.url:
            raise ValueError("--url requis pour add-url (répétable)")
        _print_json(
            zia.add_urls_to_category(
                zia_cfg,
                args.url,
                category_id=category_id,
                category_name=category_name,
            )
        )
    elif args.action == "remove-url":
        category_id = args.category_id_list[0] if args.category_id_list else None
        category_name = args.category_name_list[0] if args.category_name_list else None
        if not category_id and not category_name:
            raise ValueError("--category-id ou --category-name requis pour remove-url")
        if not args.url:
            raise ValueError("--url requis pour remove-url (répétable)")
        _print_json(
            zia.remove_urls_from_category(
                zia_cfg,
                args.url,
                category_id=category_id,
                category_name=category_name,
            )
        )
    elif args.action == "forwarding-rules":
        _print_json(zia.list_forwarding_rules(zia_cfg, search=args.search))
    elif args.action == "get-forwarding-rule":
        if not args.rule_id and not args.rule_name:
            raise ValueError("--rule-id ou --rule-name requis")
        _print_json(
            zia.get_forwarding_rule(
                zia_cfg, rule_id=args.rule_id, rule_name=args.rule_name
            )
        )
    elif args.action == "create-forwarding-rule":
        if not args.name:
            raise ValueError("--name requis pour create-forwarding-rule")
        method = (args.forward_method or "ENATDEDIP").upper()
        if method == "ENATDEDIP" and not args.gateway_id and not args.gateway_name:
            raise ValueError(
                "--gateway-id ou --gateway-name requis pour forward_method=ENATDEDIP"
            )
        _print_json(
            zia.create_forwarding_rule(
                zia_cfg,
                args.name,
                forward_method=method,
                gateway_id=args.gateway_id,
                gateway_name=args.gateway_name,
                group_ids=args.group_id or None,
                group_names=args.group_name or None,
                url_category_ids=args.category_id_list or None,
                url_category_names=args.category_name_list or None,
                dest_addresses=args.dest_ip or None,
                dest_ip_group_ids=args.dest_ip_group_id or None,
                dest_ip_group_names=args.dest_ip_group_name or None,
                description=args.description,
                order=args.order,
                rank=args.rank,
                state=args.state or "ENABLED",
            )
        )
    elif args.action == "delete-forwarding-rule":
        if not args.rule_id and not args.rule_name:
            raise ValueError("--rule-id ou --rule-name requis")
        _print_json(
            zia.delete_forwarding_rule(
                zia_cfg, rule_id=args.rule_id, rule_name=args.rule_name
            )
        )
    elif args.action == "dedicated-ips":
        _print_json(zia.list_dedicated_ips(zia_cfg))
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
        if args.add and args.remove:
            raise ValueError("--add et --remove sont mutuellement exclusifs")
        updated = zia.set_user_groups(
            zia_cfg,
            user_id,
            group_ids=args.group_id,
            group_names=args.group_name,
            add=args.add,
            remove=args.remove,
            department_id=args.department_id,
            department_name=args.department_name,
        )
        _print_json(updated)
    elif args.action == "dest-ip-groups":
        _print_json(
            zia.list_ip_destination_groups(
                zia_cfg, search=args.search, exclude_type=args.exclude_type
            )
        )
    elif args.action == "get-dest-ip-group":
        if not args.ip_group_id and not args.ip_group_name:
            raise ValueError("--ip-group-id ou --ip-group-name requis")
        _print_json(
            zia.get_ip_destination_group(
                zia_cfg, group_id=args.ip_group_id, group_name=args.ip_group_name
            )
        )
    elif args.action == "create-dest-ip-group":
        if not args.name:
            raise ValueError("--name requis pour create-dest-ip-group")
        _print_json(
            zia.create_ip_destination_group(
                zia_cfg,
                args.name,
                group_type=args.ip_group_type or "DSTN_IP",
                addresses=args.address or None,
                description=args.description,
                countries=args.country or None,
                ip_categories=args.ip_category or None,
            )
        )
    elif args.action == "update-dest-ip-group":
        if not args.ip_group_id and not args.ip_group_name:
            raise ValueError("--ip-group-id ou --ip-group-name requis")
        _print_json(
            zia.update_ip_destination_group(
                zia_cfg,
                group_id=args.ip_group_id,
                group_name=args.ip_group_name,
                name=args.name,
                group_type=args.ip_group_type,
                addresses=args.address or None,
                description=args.description,
                countries=args.country or None,
                ip_categories=args.ip_category or None,
                append_addresses=args.append,
            )
        )
    elif args.action == "delete-dest-ip-group":
        if not args.ip_group_id and not args.ip_group_name:
            raise ValueError("--ip-group-id ou --ip-group-name requis")
        _print_json(
            zia.delete_ip_destination_group(
                zia_cfg, group_id=args.ip_group_id, group_name=args.ip_group_name
            )
        )
    elif args.action == "source-ip-groups":
        _print_json(zia.list_ip_source_groups(zia_cfg, search=args.search))
    elif args.action == "get-source-ip-group":
        if not args.ip_group_id and not args.ip_group_name:
            raise ValueError("--ip-group-id ou --ip-group-name requis")
        _print_json(
            zia.get_ip_source_group(
                zia_cfg, group_id=args.ip_group_id, group_name=args.ip_group_name
            )
        )
    elif args.action == "create-source-ip-group":
        if not args.name:
            raise ValueError("--name requis pour create-source-ip-group")
        _print_json(
            zia.create_ip_source_group(
                zia_cfg,
                args.name,
                ip_addresses=args.ip or None,
                description=args.description,
            )
        )
    elif args.action == "update-source-ip-group":
        if not args.ip_group_id and not args.ip_group_name:
            raise ValueError("--ip-group-id ou --ip-group-name requis")
        _print_json(
            zia.update_ip_source_group(
                zia_cfg,
                group_id=args.ip_group_id,
                group_name=args.ip_group_name,
                name=args.name,
                ip_addresses=args.ip or None,
                description=args.description,
                append_ips=args.append,
            )
        )
    elif args.action == "delete-source-ip-group":
        if not args.ip_group_id and not args.ip_group_name:
            raise ValueError("--ip-group-id ou --ip-group-name requis")
        _print_json(
            zia.delete_ip_source_group(
                zia_cfg, group_id=args.ip_group_id, group_name=args.ip_group_name
            )
        )
    elif args.action == "activation-status":
        _print_json(zia.activation_status(zia_cfg))
    elif args.action == "activate":
        _print_json(zia.activate_changes(zia_cfg))
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
            "get-forwarding-rule",
            "create-forwarding-rule",
            "delete-forwarding-rule",
            "dedicated-ips",
            "get-user",
            "set-groups",
            "dest-ip-groups",
            "get-dest-ip-group",
            "create-dest-ip-group",
            "update-dest-ip-group",
            "delete-dest-ip-group",
            "source-ip-groups",
            "get-source-ip-group",
            "create-source-ip-group",
            "update-source-ip-group",
            "delete-source-ip-group",
            "activation-status",
            "activate",
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
        "--remove",
        action="store_true",
        help="Retire les groupes fournis, conserve les autres (set-groups)",
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
        help="Filtre recherche (forwarding-rules / departments / ip-groups)",
    )
    p_zia.add_argument(
        "--group-id",
        action="append",
        default=[],
        help="ID groupe ZIA (répétable ; set-groups / create-forwarding-rule)",
    )
    p_zia.add_argument(
        "--group-name",
        action="append",
        default=[],
        help="Nom groupe ZIA (répétable ; set-groups / create-forwarding-rule)",
    )
    p_zia.add_argument(
        "--name",
        type=str,
        help="Nom (URL category / forwarding rule / IP group)",
    )
    p_zia.add_argument(
        "--description",
        type=str,
        default=None,
        help="Description (create-url-category / create-forwarding-rule / IP groups)",
    )
    p_zia.add_argument(
        "--super-category",
        type=str,
        default="USER_DEFINED",
        help="Super category parent (défaut: USER_DEFINED)",
    )
    p_zia.add_argument(
        "--category-id",
        action="append",
        default=[],
        dest="category_id_list",
        help="ID catégorie URL (ex: CUSTOM_01, répétable ; create-forwarding-rule / add-url)",
    )
    p_zia.add_argument(
        "--category-name",
        action="append",
        default=[],
        dest="category_name_list",
        help="Nom configuré de la catégorie URL (répétable ; create-forwarding-rule / add-url)",
    )
    p_zia.add_argument(
        "--url",
        action="append",
        default=[],
        help="URL à ajouter/retirer (répétable)",
    )
    p_zia.add_argument(
        "--ip-range",
        action="append",
        default=[],
        help="Plage IP pour create-url-category (ex: 1.2.3.4 ou 1.2.3.0/24, répétable)",
    )
    p_zia.add_argument(
        "--keyword",
        action="append",
        default=[],
        help="Keyword pour create-url-category (répétable)",
    )
    p_zia.add_argument(
        "--ip-group-id",
        type=str,
        default=None,
        help="ID d'un IP group firewall (get/update/delete dest & source)",
    )
    p_zia.add_argument(
        "--ip-group-name",
        type=str,
        default=None,
        help="Nom d'un IP group firewall (get/update/delete dest & source)",
    )
    p_zia.add_argument(
        "--append",
        action="store_true",
        help="update-*-ip-group : ajoute au lieu de remplacer",
    )
    p_zia.add_argument(
        "--exclude-type",
        type=str,
        default=None,
        choices=list(zia.DEST_IP_GROUP_TYPES),
        help="Filtre list dest-ip-groups (exclut ce type)",
    )
    p_zia.add_argument(
        "--type",
        dest="ip_group_type",
        type=str,
        default=None,
        choices=list(zia.DEST_IP_GROUP_TYPES),
        help="Type de destination IP group (create/update, défaut create: DSTN_IP)",
    )
    p_zia.add_argument(
        "--address",
        action="append",
        default=[],
        help="Adresse IP/FQDN/domaine pour un destination IP group (répétable)",
    )
    p_zia.add_argument(
        "--ip",
        action="append",
        default=[],
        help="Adresse IP pour un source IP group (répétable)",
    )
    p_zia.add_argument(
        "--country",
        action="append",
        default=[],
        help="Pays pour dest IP group DSTN_OTHER (ex: COUNTRY_US, répétable)",
    )
    p_zia.add_argument(
        "--ip-category",
        action="append",
        default=[],
        help="URL category pour dest IP group DSTN_OTHER (ex: CUSTOM_01, répétable)",
    )
    p_zia.add_argument(
        "--rule-id",
        type=str,
        default=None,
        help="ID d'une forwarding rule (get/delete)",
    )
    p_zia.add_argument(
        "--rule-name",
        type=str,
        default=None,
        help="Nom d'une forwarding rule (get/delete)",
    )
    p_zia.add_argument(
        "--forward-method",
        type=str,
        default="ENATDEDIP",
        choices=list(zia.FORWARD_METHODS),
        help="Méthode de forwarding (défaut: ENATDEDIP = Dedicated IP)",
    )
    p_zia.add_argument(
        "--gateway-id",
        type=str,
        default=None,
        help="ID du Dedicated IP gateway (create-forwarding-rule ENATDEDIP)",
    )
    p_zia.add_argument(
        "--gateway-name",
        type=str,
        default=None,
        help="Nom du Dedicated IP gateway (create-forwarding-rule ENATDEDIP)",
    )
    p_zia.add_argument(
        "--dest-ip",
        action="append",
        default=[],
        help="IP/CIDR/FQDN destination pour une forwarding rule (répétable)",
    )
    p_zia.add_argument(
        "--dest-ip-group-id",
        action="append",
        default=[],
        help="ID destination IP group pour une forwarding rule (répétable)",
    )
    p_zia.add_argument(
        "--dest-ip-group-name",
        action="append",
        default=[],
        help="Nom destination IP group pour une forwarding rule (répétable)",
    )
    p_zia.add_argument(
        "--order",
        type=int,
        default=None,
        help="Ordre de la forwarding rule",
    )
    p_zia.add_argument(
        "--rank",
        type=int,
        default=7,
        help="Admin rank de la forwarding rule (1-7, défaut: 7)",
    )
    p_zia.add_argument(
        "--state",
        type=str,
        default="ENABLED",
        choices=["ENABLED", "DISABLED"],
        help="État de la forwarding rule (défaut: ENABLED)",
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
