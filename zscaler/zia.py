"""ZIA (Zscaler Internet Access) client for Hermes Agent CLI."""

from __future__ import annotations

import re
from typing import Any
from zscaler.zia.dedicated_ip_gateways import DedicatedIPGatewaysAPI
from zscaler.oneapi_client import LegacyZIAClient
from zscaler.zia.forwarding_control import ForwardingControlAPI
# --- Zscaler URL-category rules (whitelisting) -----------------------------
URL_MAX_LENGTH = 1024
DOMAIN_MAX_LENGTH = 255

LABEL_MAX_LENGTH = 63
_LABEL_RE = re.compile(r"^[a-z0-9_-]+$")


def validate_url(url: str) -> str:
    """
    Valide une URL selon les règles d'une custom URL category Zscaler.

    Renvoie l'URL nettoyée (trim) si elle est valide, sinon lève ``ValueError``
    avec la raison. On reproduit les contraintes de l'Admin Console pour
    rejeter localement une URL invalide avant que l'API ne rejette toute la
    requête.

    Règles principales :
    - ASCII uniquement, longueur <= 1024 caractères.
    - Pas de schéma de protocole (``http://``, ``https://``, ...).
    - Domaine en minuscules, format ``host.domain`` (un TLD seul est refusé).
    - Label de domaine <= 63 caractères, domaine (avant ``:``) <= 255.
    - Underscore ``_`` interdit dans le TLD et le SLD, sauf pour le SLD quand
      il n'y a pas de sous-domaine. Un sous-domaine ne peut pas être ``_``.
    - Wildcard = point initial (``.exemple.com``) — jusqu'à 5 niveaux de
      sous-domaines. ``*`` en début de domaine est interdit ; ailleurs il est
      traité comme un caractère littéral.
    """
    if url is None:
        raise ValueError("URL vide")
    trimmed = url.strip()
    if not trimmed:
        raise ValueError("URL vide")

    try:
        trimmed.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"URL {url!r}: caractères non-ASCII interdits") from exc

    if len(trimmed) > URL_MAX_LENGTH:
        raise ValueError(
            f"URL {url!r}: {len(trimmed)} caractères, maximum {URL_MAX_LENGTH}"
        )

    if "://" in trimmed:
        raise ValueError(
            f"URL {url!r}: ne pas inclure le schéma de protocole "
            "(http://, https://, ...)"
        )

    if trimmed.startswith("*"):
        raise ValueError(
            f"URL {url!r}: '*' interdit en début de domaine. "
            "Utilisez un point initial ('.exemple.com') pour un wildcard."
        )

    host_part = trimmed[1:] if trimmed.startswith(".") else trimmed

    for sep in ("/", "?"):
        idx = host_part.find(sep)
        if idx != -1:
            host_part = host_part[:idx]
    if not host_part:
        raise ValueError(f"URL {url!r}: domaine manquant")

    host = host_part
    if ":" in host:
        host, port = host.split(":", 1)
        if not port.isdigit():
            raise ValueError(f"URL {url!r}: port invalide {port!r}")

    if len(host) > DOMAIN_MAX_LENGTH:
        raise ValueError(
            f"URL {url!r}: domaine de {len(host)} caractères, "
            f"maximum {DOMAIN_MAX_LENGTH}"
        )

    if host != host.lower():
        raise ValueError(f"URL {url!r}: le domaine doit être en minuscules")

    labels = host.split(".")
    if any(not label for label in labels):
        raise ValueError(f"URL {url!r}: label de domaine vide (point en trop)")
    if len(labels) < 2:
        raise ValueError(
            f"URL {url!r}: un TLD seul n'est pas autorisé "
            "(format host.domain requis)"
        )

    for label in labels:
        if len(label) > LABEL_MAX_LENGTH:
            raise ValueError(
                f"URL {url!r}: label {label!r} > {LABEL_MAX_LENGTH} caractères"
            )
        if not _LABEL_RE.match(label):
            raise ValueError(
                f"URL {url!r}: label {label!r} invalide "
                "(autorisé: a-z, 0-9, '-', '_')"
            )

    tld, sld, subdomains = labels[-1], labels[-2], labels[:-2]
    if "_" in tld:
        raise ValueError(f"URL {url!r}: underscore interdit dans le TLD {tld!r}")
    if "_" in sld and subdomains:
        raise ValueError(
            f"URL {url!r}: underscore interdit dans le SLD {sld!r} "
            "lorsqu'un sous-domaine est présent"
        )
    for sub in subdomains:
        if sub == "_":
            raise ValueError(
                f"URL {url!r}: un sous-domaine ne peut pas être uniquement '_'"
            )

    return trimmed


def validate_urls(urls: list[str]) -> list[str]:
    """Valide une liste d'URLs. Rejette tout le lot si une URL est invalide."""
    validated: list[str] = []
    errors: list[str] = []
    for url in urls:
        try:
            validated.append(validate_url(url))
        except ValueError as exc:
            errors.append(str(exc))
    if errors:
        raise ValueError(
            "URL(s) invalide(s) — requête rejetée:\n  - " + "\n  - ".join(errors)
        )
    return validated


def build_client_config(zia_cfg: dict[str, Any]) -> dict[str, Any]:
    """Build LegacyZIAClient config from config.json zia section."""
    return {
        "username": zia_cfg["username"],
        "password": zia_cfg["password"],
        "api_key": zia_cfg["api_key"],
        "cloud": zia_cfg.get("cloud") or "zscaler",
        "logging": {"enabled": False, "verbose": False},
    }


def get_client(zia_cfg: dict[str, Any]) -> LegacyZIAClient:
    """Return an authenticated Legacy ZIA client."""
    return LegacyZIAClient(build_client_config(zia_cfg))


def test_connection(zia_cfg: dict[str, Any]) -> tuple[bool, str]:
    """Verify ZIA credentials by listing users (page size 1)."""
    try:
        with get_client(zia_cfg) as client:
            users, _, err = client.zia.user_management.list_users(
                query_params={"page": 1, "pageSize": 1}
            )
            if err:
                return False, f"ZIA API error: {err}"
            count = len(users) if users else 0
            return True, f"ZIA connected (sample users returned: {count})"
    except Exception as exc:  # noqa: BLE001
        return False, f"ZIA connection failed: {exc}"


def list_users(
    zia_cfg: dict[str, Any],
    page: int = 1,
    page_size: int = 20,
) -> list[dict[str, Any]]:
    """List ZIA users."""
    with get_client(zia_cfg) as client:
        users, _, err = client.zia.user_management.list_users(
            query_params={"page": page, "pageSize": page_size}
        )
        if err:
            raise RuntimeError(f"Failed to list ZIA users: {err}")
        return [u.as_dict() if hasattr(u, "as_dict") else dict(u) for u in (users or [])]


def list_groups(
    zia_cfg: dict[str, Any],
    page: int = 1,
    page_size: int = 100,
) -> list[dict[str, Any]]:
    """List ZIA user groups (max page_size: 1000)."""
    with get_client(zia_cfg) as client:
        groups, _, err = client.zia.user_management.list_groups(
            query_params={"page": page, "page_size": page_size}
        )
        if err:
            raise RuntimeError(f"Failed to list ZIA groups: {err}")
        return [g.as_dict() if hasattr(g, "as_dict") else dict(g) for g in (groups or [])]


def list_departments(
    zia_cfg: dict[str, Any],
    page: int = 1,
    page_size: int = 100,
    search: str | None = None,
) -> list[dict[str, Any]]:
    """List ZIA departments (max page_size: 1000)."""
    query_params: dict[str, Any] = {"page": page, "page_size": page_size}
    if search:
        query_params["search"] = search

    with get_client(zia_cfg) as client:
        departments, _, err = client.zia.user_management.list_departments(
            query_params=query_params
        )
        if err:
            raise RuntimeError(f"Failed to list ZIA departments: {err}")
        return [
            d.as_dict() if hasattr(d, "as_dict") else dict(d)
            for d in (departments or [])
        ]


def list_url_categories(zia_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """List ZIA URL categories."""
    with get_client(zia_cfg) as client:
        categories, _, err = client.zia.url_categories.list_categories()
        if err:
            raise RuntimeError(f"Failed to list URL categories: {err}")
        return [
            c.as_dict() if hasattr(c, "as_dict") else dict(c)
            for c in (categories or [])
        ]


def get_url_category(
    zia_cfg: dict[str, Any],
    *,
    category_id: str | None = None,
    category_name: str | None = None,
) -> dict[str, Any]:
    """Get a URL category by ID (e.g. CUSTOM_01) or configured_name."""
    if not category_id and not category_name:
        raise ValueError("category_id ou category_name requis")

    if category_id:
        with get_client(zia_cfg) as client:
            cat, _, err = client.zia.url_categories.get_category(category_id)
            if err:
                raise RuntimeError(f"Failed to get URL category {category_id}: {err}")
            if cat is None:
                raise RuntimeError(f"URL category introuvable: {category_id}")
            return cat.as_dict() if hasattr(cat, "as_dict") else dict(cat)

    needle = category_name.strip().casefold()
    for cat in list_url_categories(zia_cfg):
        configured = str(cat.get("configured_name") or "").casefold()
        cid = str(cat.get("id") or "").casefold()
        if configured == needle or cid == needle:
            return cat
    raise RuntimeError(f"URL category introuvable: {category_name!r}")


def create_url_category(
    zia_cfg: dict[str, Any],
    name: str,
    *,
    urls: list[str] | None = None,
    ip_ranges: list[str] | None = None,
    keywords: list[str] | None = None,
    super_category: str = "USER_DEFINED",
    description: str | None = None,
) -> dict[str, Any]:
    """
    Create a custom ZIA URL category.

    Au moins un contenu parmi ``urls`` / ``ip_ranges`` / ``keywords`` est
    requis (l'API ZIA rejette sinon avec
    ``At least 1 URL or keyword should be entered``).

    Note: ``ip_ranges`` nécessite souvent que la fonctionnalité "custom IP"
    soit activée sur le tenant.
    """
    if not name or not name.strip():
        raise ValueError("name requis pour créer une URL category")

    if not urls and not ip_ranges and not keywords:
        raise ValueError(
            "Fournir au moins --url, --ip-range ou --keyword "
            "(requis par l'API ZIA)."
        )

    kwargs: dict[str, Any] = {
        "configured_name": name.strip(),
        "custom_category": True,
    }
    if urls:
        kwargs["urls"] = validate_urls(urls)
    if ip_ranges:
        kwargs["ip_ranges"] = ip_ranges
    if keywords:
        kwargs["keywords"] = keywords
    if description:
        kwargs["description"] = description

    with get_client(zia_cfg) as client:
        created, _, err = client.zia.url_categories.add_url_category(
            super_category=super_category,
            **kwargs,
        )
        if err:
            raise RuntimeError(f"Failed to create URL category {name!r}: {err}")
        return created.as_dict() if hasattr(created, "as_dict") else dict(created)


def add_urls_to_category(
    zia_cfg: dict[str, Any],
    urls: list[str],
    *,
    category_id: str | None = None,
    category_name: str | None = None,
) -> dict[str, Any]:
    """Add one or more URLs to an existing URL category."""
    if not urls:
        raise ValueError("Au moins une URL est requise")
    urls = validate_urls(urls)

    cat = get_url_category(zia_cfg, category_id=category_id, category_name=category_name)
    cid = str(cat["id"])
    configured_name = cat.get("configured_name") or cat.get("id")

    with get_client(zia_cfg) as client:
        updated, _, err = client.zia.url_categories.add_urls_to_category(
            category_id=cid,
            configured_name=configured_name,
            urls=urls,
        )
        if err:
            raise RuntimeError(f"Failed to add URLs to category {cid}: {err}")
        return updated.as_dict() if hasattr(updated, "as_dict") else dict(updated)


def remove_urls_from_category(
    zia_cfg: dict[str, Any],
    urls: list[str],
    *,
    category_id: str | None = None,
    category_name: str | None = None,
) -> dict[str, Any]:
    """Remove one or more URLs from an existing URL category."""
    if not urls:
        raise ValueError("Au moins une URL est requise")

    cat = get_url_category(zia_cfg, category_id=category_id, category_name=category_name)
    cid = str(cat["id"])
    configured_name = cat.get("configured_name") or cat.get("id")

    with get_client(zia_cfg) as client:
        updated, _, err = client.zia.url_categories.delete_urls_from_category(
            category_id=cid,
            configured_name=configured_name,
            urls=urls,
        )
        if err:
            raise RuntimeError(f"Failed to remove URLs from category {cid}: {err}")
        return updated.as_dict() if hasattr(updated, "as_dict") else dict(updated)


# --- Forwarding Control / Dedicated IP -------------------------------------
FORWARD_METHODS = (
    "DIRECT",
    "PROXYCHAIN",
    "ZIA",
    "ZPA",
    "ECZPA",
    "ECSELF",
    "DROP",
    "ENATDEDIP",
    "GEOIP",
)
FORWARDING_RULE_NAME_MAX = 31


def _forwarding_control_api(client: Any) -> Any:
    """Return ForwardingControlAPI (Legacy helper may lack the property)."""

    zia_svc = client.zia
    if hasattr(zia_svc, "forwarding_control"):
        return zia_svc.forwarding_control
    return ForwardingControlAPI(zia_svc.request_executor)


def _dedicated_ip_gateways_api(client: Any) -> Any:
    """Return DedicatedIPGatewaysAPI (Legacy helper may lack the property)."""
    zia_svc = client.zia
    if hasattr(zia_svc, "dedicated_ip_gateways"):
        return zia_svc.dedicated_ip_gateways
    return DedicatedIPGatewaysAPI(zia_svc.request_executor)


def list_forwarding_rules(
    zia_cfg: dict[str, Any],
    search: str | None = None,
) -> list[dict[str, Any]]:
    """List ZIA forwarding control rules."""
    query_params: dict[str, Any] = {}
    if search:
        query_params["search"] = search

    with get_client(zia_cfg) as client:
        rules, _, err = _forwarding_control_api(client).list_rules(
            query_params=query_params or None
        )
        if err:
            raise RuntimeError(f"Failed to list forwarding rules: {err}")
        return [_to_dict(r) for r in (rules or [])]


def get_forwarding_rule(
    zia_cfg: dict[str, Any],
    *,
    rule_id: int | str | None = None,
    rule_name: str | None = None,
) -> dict[str, Any]:
    """Get a forwarding control rule by ID or exact name."""
    if rule_id is not None and str(rule_id).strip():
        with get_client(zia_cfg) as client:
            rule, _, err = _forwarding_control_api(client).get_rule(str(rule_id))
            if err:
                raise RuntimeError(f"Failed to get forwarding rule {rule_id}: {err}")
            if rule is None:
                raise RuntimeError(f"Forwarding rule introuvable: {rule_id}")
            return _to_dict(rule)

    if not rule_name or not rule_name.strip():
        raise ValueError("rule_id ou rule_name requis")

    needle = rule_name.strip().casefold()
    matches = [
        r
        for r in list_forwarding_rules(zia_cfg, search=rule_name)
        if str(r.get("name") or "").casefold() == needle
    ]
    if not matches:
        matches = [
            r
            for r in list_forwarding_rules(zia_cfg)
            if str(r.get("name") or "").casefold() == needle
        ]
    if not matches:
        raise RuntimeError(f"Forwarding rule introuvable: {rule_name!r}")
    if len(matches) > 1:
        ids = ", ".join(str(r.get("id")) for r in matches)
        raise RuntimeError(f"Plusieurs forwarding rules pour {rule_name!r}: {ids}")
    return matches[0]


def list_dedicated_ips(zia_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """List the org's ZIA dedicated IPs (Dedicated IP Gateways).

    Renvoie la liste des dedicated IP gateways du tenant (endpoint
    ``/dedicatedIPGateways/lite``).
    """
    with get_client(zia_cfg) as client:
        gateways, _, err = _dedicated_ip_gateways_api(client).list_dedicated_ip_gw_lite()
        if err:
            raise RuntimeError(f"Failed to list dedicated IP gateways: {err}")
        return [_to_dict(g) for g in (gateways or [])]


def resolve_dedicated_ip_gateway(
    zia_cfg: dict[str, Any],
    *,
    gateway_id: int | str | None = None,
    gateway_name: str | None = None,
) -> dict[str, Any]:
    """Resolve a dedicated IP gateway to ``{"id": ..., "name": ...}``."""
    gateways = list_dedicated_ips(zia_cfg)

    if gateway_id is not None and str(gateway_id).strip():
        gid = int(gateway_id)
        for gw in gateways:
            if int(gw.get("id") or 0) == gid:
                return {"id": int(gw["id"]), "name": gw.get("name")}
        available = ", ".join(f"{g.get('id')}:{g.get('name')}" for g in gateways)
        raise RuntimeError(f"Dedicated IP gateway introuvable: id={gid}. Disponibles: {available}")

    if not gateway_name or not gateway_name.strip():
        raise ValueError("gateway_id ou gateway_name requis")

    needle = gateway_name.strip().casefold()
    matches = [g for g in gateways if str(g.get("name") or "").casefold() == needle]
    if not matches:
        available = ", ".join(sorted(str(g.get("name") or "?") for g in gateways))
        raise RuntimeError(
            f"Dedicated IP gateway introuvable: {gateway_name!r}. Disponibles: {available}"
        )
    if len(matches) > 1:
        ids = ", ".join(str(g.get("id")) for g in matches)
        raise RuntimeError(f"Plusieurs dedicated IP gateways pour {gateway_name!r}: {ids}")
    return {"id": int(matches[0]["id"]), "name": matches[0].get("name")}


def resolve_url_category_ids(
    zia_cfg: dict[str, Any],
    *,
    category_ids: list[str] | None = None,
    category_names: list[str] | None = None,
) -> list[str]:
    """Resolve URL category IDs / configured names to category ID strings (e.g. CUSTOM_01)."""
    resolved: list[str] = []
    seen: set[str] = set()

    for cid in category_ids or []:
        text = str(cid).strip()
        if not text:
            continue
        key = text.casefold()
        if key not in seen:
            seen.add(key)
            resolved.append(text)

    for name in category_names or []:
        cat = get_url_category(zia_cfg, category_name=name)
        cid = str(cat.get("id") or "").strip()
        if not cid:
            raise RuntimeError(f"URL category sans id: {name!r}")
        key = cid.casefold()
        if key not in seen:
            seen.add(key)
            resolved.append(cid)

    return resolved


def resolve_dest_ip_group_ids(
    zia_cfg: dict[str, Any],
    *,
    group_ids: list[int | str] | None = None,
    group_names: list[str] | None = None,
) -> list[int]:
    """Resolve destination IP group IDs and/or names to integer IDs."""
    resolved: list[int] = []
    seen: set[int] = set()

    for gid in group_ids or []:
        gid_int = int(gid)
        if gid_int not in seen:
            seen.add(gid_int)
            resolved.append(gid_int)

    for name in group_names or []:
        group = get_ip_destination_group(zia_cfg, group_name=name)
        gid_int = int(group["id"])
        if gid_int not in seen:
            seen.add(gid_int)
            resolved.append(gid_int)

    return resolved


def create_forwarding_rule(
    zia_cfg: dict[str, Any],
    name: str,
    *,
    forward_method: str = "ENATDEDIP",
    gateway_id: int | str | None = None,
    gateway_name: str | None = None,
    group_ids: list[int | str] | None = None,
    group_names: list[str] | None = None,
    url_category_ids: list[str] | None = None,
    url_category_names: list[str] | None = None,
    dest_addresses: list[str] | None = None,
    dest_ip_group_ids: list[int | str] | None = None,
    dest_ip_group_names: list[str] | None = None,
    description: str | None = None,
    order: int | None = None,
    rank: int = 7,
    state: str = "ENABLED",
) -> dict[str, Any]:
    """
    Create a ZIA forwarding control rule.

    Cas typique Dedicated IP (``ENATDEDIP``) :
    - groupes users (``group_ids`` / ``group_names``)
    - URL categories (``url_category_ids`` / ``url_category_names`` → ``destIpCategories``)
    - destinations IP (``dest_addresses`` et/ou destination IP groups)
    - gateway dedicated IP (``gateway_id`` / ``gateway_name``)
    """
    name = (name or "").strip()
    if not name:
        raise ValueError("name requis")
    if len(name) > FORWARDING_RULE_NAME_MAX:
        raise ValueError(
            f"name trop long ({len(name)}), maximum {FORWARDING_RULE_NAME_MAX} caractères"
        )

    method = (forward_method or "ENATDEDIP").strip().upper()
    if method not in FORWARD_METHODS:
        raise ValueError(
            f"forward_method invalide: {forward_method!r}. "
            f"Supportés: {', '.join(FORWARD_METHODS)}"
        )

    state_norm = (state or "ENABLED").strip().upper()
    if state_norm not in ("ENABLED", "DISABLED"):
        raise ValueError("state doit être ENABLED ou DISABLED")

    kwargs: dict[str, Any] = {
        "name": name,
        "type": "FORWARDING",
        "forward_method": method,
        "state": state_norm,
        "rank": int(rank),
    }
    if description:
        kwargs["description"] = description
    if order is not None:
        kwargs["order"] = int(order)

    if method == "ENATDEDIP":
        gateway = resolve_dedicated_ip_gateway(
            zia_cfg, gateway_id=gateway_id, gateway_name=gateway_name
        )
        # API wire key is dedicatedIPGateway (IP majuscules) — pas dedicatedIpGateway
        # que produirait la conversion snake_case → camelCase du SDK.
        kwargs["dedicatedIPGateway"] = gateway
    elif gateway_id is not None or gateway_name:
        raise ValueError(
            "gateway_id / gateway_name ne s'appliquent qu'avec forward_method=ENATDEDIP"
        )

    if group_ids or group_names:
        groups = resolve_group_ids(zia_cfg, group_ids=group_ids, group_names=group_names)
        kwargs["groups"] = [g["id"] for g in groups]

    categories = resolve_url_category_ids(
        zia_cfg, category_ids=url_category_ids, category_names=url_category_names
    )
    if categories:
        kwargs["dest_ip_categories"] = categories

    addresses = [a.strip() for a in (dest_addresses or []) if a and a.strip()]
    if addresses:
        kwargs["dest_addresses"] = addresses

    dest_groups = resolve_dest_ip_group_ids(
        zia_cfg, group_ids=dest_ip_group_ids, group_names=dest_ip_group_names
    )
    if dest_groups:
        kwargs["dest_ip_groups"] = dest_groups

    with get_client(zia_cfg) as client:
        created, _, err = _forwarding_control_api(client).add_rule(**kwargs)
        if err:
            raise RuntimeError(f"Failed to create forwarding rule {name!r}: {err}")
        return _to_dict(created)


def delete_forwarding_rule(
    zia_cfg: dict[str, Any],
    *,
    rule_id: int | str | None = None,
    rule_name: str | None = None,
) -> dict[str, Any]:
    """Delete a forwarding control rule by ID or name."""
    current = get_forwarding_rule(zia_cfg, rule_id=rule_id, rule_name=rule_name)
    rid = current["id"]
    with get_client(zia_cfg) as client:
        _, _, err = _forwarding_control_api(client).delete_rule(str(rid))
        if err:
            raise RuntimeError(f"Failed to delete forwarding rule {rid}: {err}")
    return {"deleted": True, "id": rid, "name": current.get("name")}


# --- IP groups (ZIA Cloud Firewall) ----------------------------------------
DEST_IP_GROUP_TYPES = ("DSTN_IP", "DSTN_FQDN", "DSTN_DOMAIN", "DSTN_OTHER")


def _to_dict(obj: Any) -> dict[str, Any]:
    return obj.as_dict() if hasattr(obj, "as_dict") else dict(obj)


def _resolve_group_by_name(list_fn: Any, group_name: str, kind: str) -> dict[str, Any]:
    """Résout un groupe par nom (match exact casefold) via un lister ``list_fn(search=...)``."""
    needle = (group_name or "").strip().casefold()
    if not needle:
        raise ValueError(f"nom de {kind} vide")

    def _exact(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [g for g in items if str(g.get("name") or "").casefold() == needle]

    matches = _exact(list_fn(search=group_name))
    if not matches:
        matches = _exact(list_fn(search=None))
    if not matches:
        raise RuntimeError(f"{kind} introuvable: {group_name!r}")
    if len(matches) > 1:
        ids = ", ".join(str(g.get("id")) for g in matches)
        raise RuntimeError(f"Plusieurs {kind} pour {group_name!r}: {ids}")
    return matches[0]


def list_ip_destination_groups(
    zia_cfg: dict[str, Any],
    *,
    search: str | None = None,
    exclude_type: str | None = None,
) -> list[dict[str, Any]]:
    """List ZIA destination IP groups."""
    query_params: dict[str, Any] = {}
    if search:
        query_params["search"] = search
    kwargs: dict[str, Any] = {}
    if exclude_type:
        kwargs["exclude_type"] = exclude_type

    with get_client(zia_cfg) as client:
        groups, _, err = client.zia.cloud_firewall.list_ip_destination_groups(
            query_params=query_params or None, **kwargs
        )
        if err:
            raise RuntimeError(f"Failed to list destination IP groups: {err}")
        return [_to_dict(g) for g in (groups or [])]


def get_ip_destination_group(
    zia_cfg: dict[str, Any],
    *,
    group_id: int | str | None = None,
    group_name: str | None = None,
) -> dict[str, Any]:
    """Get a destination IP group by ID or name."""
    if group_id is not None and str(group_id).strip():
        with get_client(zia_cfg) as client:
            grp, _, err = client.zia.cloud_firewall.get_ip_destination_group(int(group_id))
            if err:
                raise RuntimeError(f"Failed to get destination IP group {group_id}: {err}")
            if grp is None:
                raise RuntimeError(f"Destination IP group introuvable: {group_id}")
            return _to_dict(grp)
    if not group_name or not group_name.strip():
        raise ValueError("--ip-group-id ou --ip-group-name requis")
    return _resolve_group_by_name(
        lambda search=None: list_ip_destination_groups(zia_cfg, search=search),
        group_name,
        "destination IP group",
    )


def create_ip_destination_group(
    zia_cfg: dict[str, Any],
    name: str,
    *,
    group_type: str = "DSTN_IP",
    addresses: list[str] | None = None,
    description: str | None = None,
    countries: list[str] | None = None,
    ip_categories: list[str] | None = None,
) -> dict[str, Any]:
    """Create a ZIA destination IP group."""
    if not name or not name.strip():
        raise ValueError("name requis pour créer un destination IP group")
    if group_type not in DEST_IP_GROUP_TYPES:
        raise ValueError(
            f"type invalide {group_type!r}. Types: {', '.join(DEST_IP_GROUP_TYPES)}"
        )
    if group_type == "DSTN_OTHER":
        if not countries and not ip_categories:
            raise ValueError("DSTN_OTHER requiert --country et/ou --ip-category")
    elif not addresses:
        raise ValueError(f"{group_type} requiert au moins --address")

    kwargs: dict[str, Any] = {"name": name.strip(), "type": group_type}
    if description:
        kwargs["description"] = description
    if addresses:
        kwargs["addresses"] = addresses
    if countries:
        kwargs["countries"] = countries
    if ip_categories:
        kwargs["ip_categories"] = ip_categories

    with get_client(zia_cfg) as client:
        created, _, err = client.zia.cloud_firewall.add_ip_destination_group(**kwargs)
        if err:
            raise RuntimeError(f"Failed to create destination IP group {name!r}: {err}")
        return _to_dict(created)


def update_ip_destination_group(
    zia_cfg: dict[str, Any],
    *,
    group_id: int | str | None = None,
    group_name: str | None = None,
    name: str | None = None,
    group_type: str | None = None,
    addresses: list[str] | None = None,
    description: str | None = None,
    countries: list[str] | None = None,
    ip_categories: list[str] | None = None,
    append_addresses: bool = False,
) -> dict[str, Any]:
    """Update a destination IP group (replace by default, append with ``append_addresses``)."""
    current = get_ip_destination_group(zia_cfg, group_id=group_id, group_name=group_name)
    gid = int(current["id"])

    kwargs: dict[str, Any] = {
        "name": name if name is not None else current.get("name"),
        "type": group_type if group_type is not None else current.get("type"),
    }
    desc = description if description is not None else current.get("description")
    if desc is not None:
        kwargs["description"] = desc

    if addresses is not None:
        kwargs["addresses"] = addresses
    elif current.get("addresses") is not None:
        kwargs["addresses"] = current.get("addresses")

    if countries is not None:
        kwargs["countries"] = countries
    elif current.get("countries"):
        kwargs["countries"] = current.get("countries")

    if ip_categories is not None:
        kwargs["ip_categories"] = ip_categories
    elif current.get("ip_categories"):
        kwargs["ip_categories"] = current.get("ip_categories")

    # override=false => append les addresses fournies aux existantes (API ZIA)
    query_params = (
        {"override": False} if append_addresses and addresses is not None else None
    )

    with get_client(zia_cfg) as client:
        updated, _, err = client.zia.cloud_firewall.update_ip_destination_group(
            gid, query_params=query_params, **kwargs
        )
        if err:
            raise RuntimeError(f"Failed to update destination IP group {gid}: {err}")
        return _to_dict(updated)


def delete_ip_destination_group(
    zia_cfg: dict[str, Any],
    *,
    group_id: int | str | None = None,
    group_name: str | None = None,
) -> dict[str, Any]:
    """Delete a destination IP group by ID or name."""
    current = get_ip_destination_group(zia_cfg, group_id=group_id, group_name=group_name)
    gid = int(current["id"])
    with get_client(zia_cfg) as client:
        _, _, err = client.zia.cloud_firewall.delete_ip_destination_group(gid)
        if err:
            raise RuntimeError(f"Failed to delete destination IP group {gid}: {err}")
    return {"deleted": True, "id": gid, "name": current.get("name")}


def list_ip_source_groups(
    zia_cfg: dict[str, Any],
    *,
    search: str | None = None,
) -> list[dict[str, Any]]:
    """List ZIA source IP groups."""
    query_params: dict[str, Any] = {}
    if search:
        query_params["search"] = search
    with get_client(zia_cfg) as client:
        groups, _, err = client.zia.cloud_firewall.list_ip_source_groups(
            query_params=query_params or None
        )
        if err:
            raise RuntimeError(f"Failed to list source IP groups: {err}")
        return [_to_dict(g) for g in (groups or [])]


def get_ip_source_group(
    zia_cfg: dict[str, Any],
    *,
    group_id: int | str | None = None,
    group_name: str | None = None,
) -> dict[str, Any]:
    """Get a source IP group by ID or name."""
    if group_id is not None and str(group_id).strip():
        with get_client(zia_cfg) as client:
            grp, _, err = client.zia.cloud_firewall.get_ip_source_group(int(group_id))
            if err:
                raise RuntimeError(f"Failed to get source IP group {group_id}: {err}")
            if grp is None:
                raise RuntimeError(f"Source IP group introuvable: {group_id}")
            return _to_dict(grp)
    if not group_name or not group_name.strip():
        raise ValueError("--ip-group-id ou --ip-group-name requis")
    return _resolve_group_by_name(
        lambda search=None: list_ip_source_groups(zia_cfg, search=search),
        group_name,
        "source IP group",
    )


def create_ip_source_group(
    zia_cfg: dict[str, Any],
    name: str,
    *,
    ip_addresses: list[str] | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Create a ZIA source IP group."""
    if not name or not name.strip():
        raise ValueError("name requis pour créer un source IP group")
    if not ip_addresses:
        raise ValueError("Au moins une --ip est requise pour un source IP group")

    kwargs: dict[str, Any] = {"name": name.strip(), "ip_addresses": ip_addresses}
    if description:
        kwargs["description"] = description

    with get_client(zia_cfg) as client:
        created, _, err = client.zia.cloud_firewall.add_ip_source_group(**kwargs)
        if err:
            raise RuntimeError(f"Failed to create source IP group {name!r}: {err}")
        return _to_dict(created)


def update_ip_source_group(
    zia_cfg: dict[str, Any],
    *,
    group_id: int | str | None = None,
    group_name: str | None = None,
    name: str | None = None,
    ip_addresses: list[str] | None = None,
    description: str | None = None,
    append_ips: bool = False,
) -> dict[str, Any]:
    """Update a source IP group (replace by default, append with ``append_ips``)."""
    current = get_ip_source_group(zia_cfg, group_id=group_id, group_name=group_name)
    gid = int(current["id"])

    kwargs: dict[str, Any] = {
        "name": name if name is not None else current.get("name"),
    }
    desc = description if description is not None else current.get("description")
    if desc is not None:
        kwargs["description"] = desc

    if ip_addresses is not None:
        if append_ips:
            existing = list(current.get("ip_addresses") or [])
            seen = {ip.casefold() for ip in existing}
            merged = list(existing)
            for ip in ip_addresses:
                if ip.casefold() not in seen:
                    seen.add(ip.casefold())
                    merged.append(ip)
            kwargs["ip_addresses"] = merged
        else:
            kwargs["ip_addresses"] = ip_addresses
    else:
        kwargs["ip_addresses"] = list(current.get("ip_addresses") or [])

    with get_client(zia_cfg) as client:
        updated, _, err = client.zia.cloud_firewall.update_ip_source_group(gid, **kwargs)
        if err:
            raise RuntimeError(f"Failed to update source IP group {gid}: {err}")
        return _to_dict(updated)


def delete_ip_source_group(
    zia_cfg: dict[str, Any],
    *,
    group_id: int | str | None = None,
    group_name: str | None = None,
) -> dict[str, Any]:
    """Delete a source IP group by ID or name."""
    current = get_ip_source_group(zia_cfg, group_id=group_id, group_name=group_name)
    gid = int(current["id"])
    with get_client(zia_cfg) as client:
        _, _, err = client.zia.cloud_firewall.delete_ip_source_group(gid)
        if err:
            raise RuntimeError(f"Failed to delete source IP group {gid}: {err}")
    return {"deleted": True, "id": gid, "name": current.get("name")}


def get_user(zia_cfg: dict[str, Any], user_id: int | str) -> dict[str, Any]:
    """Get a ZIA user by ID."""
    with get_client(zia_cfg) as client:
        user, _, err = client.zia.user_management.get_user(int(user_id))
        if err:
            raise RuntimeError(f"Failed to get ZIA user {user_id}: {err}")
        if user is None:
            raise RuntimeError(f"ZIA user not found: {user_id}")
        return user.as_dict() if hasattr(user, "as_dict") else dict(user)


def get_user_by_username(
    zia_cfg: dict[str, Any],
    username: str,
) -> dict[str, Any]:
    """
    Get a ZIA user by username (name or email).

    Uses the ZIA ``name`` starts-with filter, then prefers an exact match
    on ``name`` or ``email`` (case-insensitive).
    """
    needle = username.strip()
    if not needle:
        raise ValueError("username vide")

    with get_client(zia_cfg) as client:
        users, _, err = client.zia.user_management.list_users(
            query_params={"name": needle, "page": 1, "pageSize": 100}
        )
        if err:
            raise RuntimeError(f"Failed to search ZIA user {needle!r}: {err}")

        results = [u.as_dict() if hasattr(u, "as_dict") else dict(u) for u in (users or [])]

        # Si le filtre name ne matche pas un email, retente une page plus large
        # filtrée côté client sur email/name.
        if not results and "@" in needle:
            users, _, err = client.zia.user_management.list_users(
                query_params={"page": 1, "pageSize": 10000}
            )
            if err:
                raise RuntimeError(f"Failed to list ZIA users for email lookup: {err}")
            results = [
                u.as_dict() if hasattr(u, "as_dict") else dict(u) for u in (users or [])
            ]

    needle_cf = needle.casefold()
    exact = [
        u
        for u in results
        if str(u.get("name") or "").casefold() == needle_cf
        or str(u.get("email") or "").casefold() == needle_cf
    ]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise RuntimeError(
            f"Plusieurs users exacts pour {needle!r}: "
            + ", ".join(f"{u.get('id')}:{u.get('email')}" for u in exact)
        )

    # starts-with unique
    partial = [
        u
        for u in results
        if needle_cf in str(u.get("name") or "").casefold()
        or needle_cf in str(u.get("email") or "").casefold()
    ]
    if len(partial) == 1:
        return partial[0]
    if not partial:
        raise RuntimeError(f"ZIA user introuvable: {needle!r}")
    raise RuntimeError(
        f"Plusieurs users pour {needle!r}, précisez le nom/email exact: "
        + ", ".join(f"{u.get('id')}:{u.get('email') or u.get('name')}" for u in partial[:10])
    )


def resolve_group_ids(
    zia_cfg: dict[str, Any],
    group_ids: list[int | str] | None = None,
    group_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Resolve group IDs and/or names to ZIA group payloads ``[{"id": ...}]``."""
    resolved: list[dict[str, Any]] = []
    seen: set[int] = set()

    for gid in group_ids or []:
        gid_int = int(gid)
        if gid_int not in seen:
            seen.add(gid_int)
            resolved.append({"id": gid_int})

    if group_names:
        groups = list_groups(zia_cfg, page=1, page_size=1000)
        by_name = {str(g.get("name", "")).casefold(): g for g in groups}
        for name in group_names:
            match = by_name.get(name.casefold())
            if not match:
                available = ", ".join(sorted(g.get("name") or "?" for g in groups))
                raise ValueError(
                    f"Groupe introuvable: {name!r}. Groupes disponibles: {available}"
                )
            gid_int = int(match["id"])
            if gid_int not in seen:
                seen.add(gid_int)
                resolved.append({"id": gid_int})

    if not resolved:
        raise ValueError("Aucun groupe fourni (group_ids / group_names).")
    return resolved


def resolve_department_id(
    zia_cfg: dict[str, Any],
    *,
    department_id: int | str | None = None,
    department_name: str | None = None,
) -> int | None:
    """Resolve a department by ID or name (case-insensitive) to its ID."""
    if department_id is not None and str(department_id).strip():
        return int(department_id)
    if not department_name or not department_name.strip():
        return None

    needle = department_name.strip().casefold()
    departments = list_departments(zia_cfg, page=1, page_size=1000)
    for dept in departments:
        if str(dept.get("name") or "").casefold() == needle:
            return int(dept["id"])
    available = ", ".join(sorted(d.get("name") or "?" for d in departments))
    raise ValueError(
        f"Département introuvable: {department_name!r}. Disponibles: {available}"
    )


def set_user_groups(
    zia_cfg: dict[str, Any],
    user_id: int | str,
    *,
    group_ids: list[int | str] | None = None,
    group_names: list[str] | None = None,
    add: bool = False,
    remove: bool = False,
    department_id: int | str | None = None,
    department_name: str | None = None,
    default_department_id: int | str | None = None,
) -> dict[str, Any]:
    """
    Modifie les groupes d'un user ZIA.

    Args:
        user_id: ID ZIA du user.
        group_ids: IDs de groupes.
        group_names: Noms de groupes (ex: \"GROUPE\").
        add: Si True, ajoute les groupes fournis aux groupes existants (union).
        remove: Si True, retire les groupes fournis en conservant les autres
            (différence). Mutuellement exclusif avec ``add``.
        department_id / department_name: Force le département de l'user.
        default_department_id: Département utilisé seulement si l'user n'en a pas
            (requis par l'API ZIA sur PUT /users).
    """
    if add and remove:
        raise ValueError("add et remove sont mutuellement exclusifs")

    target_groups = resolve_group_ids(zia_cfg, group_ids=group_ids, group_names=group_names)
    forced_department_id = resolve_department_id(
        zia_cfg, department_id=department_id, department_name=department_name
    )

    with get_client(zia_cfg) as client:
        user, _, err = client.zia.user_management.get_user(int(user_id))
        if err:
            raise RuntimeError(f"Failed to get ZIA user {user_id}: {err}")
        if user is None:
            raise RuntimeError(f"ZIA user not found: {user_id}")

        current = user.as_dict() if hasattr(user, "as_dict") else dict(user)

        existing = [
            {"id": int(g["id"])}
            for g in (current.get("groups") or [])
            if g.get("id") not in (None, 0, "0")
        ]

        if remove:
            remove_ids = {g["id"] for g in target_groups}
            groups_payload = [g for g in existing if g["id"] not in remove_ids]
        elif add:
            seen = {g["id"] for g in existing}
            groups_payload = list(existing)
            for g in target_groups:
                if g["id"] not in seen:
                    seen.add(g["id"])
                    groups_payload.append(g)
        else:
            groups_payload = target_groups

        department = current.get("department")
        if forced_department_id is not None:
            department_payload = {"id": forced_department_id}
        elif isinstance(department, dict) and department.get("id"):
            department_payload = {"id": int(department["id"])}
        elif default_department_id is not None:
            department_payload = {"id": int(default_department_id)}
        else:
            raise RuntimeError(
                f"User {user_id} n'a pas de département; "
                "passez --department-name/--department-id (requis par ZIA)."
            )

        kwargs: dict[str, Any] = {
            "name": current.get("name"),
            "email": current.get("email"),
            "groups": groups_payload,
            "department": department_payload,
        }
        if current.get("comments") is not None:
            kwargs["comments"] = current["comments"]

        updated, _, err = client.zia.user_management.update_user(str(user_id), **kwargs)
        if err:
            raise RuntimeError(f"Failed to update groups for user {user_id}: {err}")
        return updated.as_dict() if hasattr(updated, "as_dict") else dict(updated)


# --- Config activation ------------------------------------------------------
def activation_status(zia_cfg: dict[str, Any]) -> dict[str, Any]:
    """Get the ZIA configuration activation status (e.g. ACTIVE / PENDING)."""
    with get_client(zia_cfg) as client:
        result, _, err = client.zia.activate.status()
        if err:
            raise RuntimeError(f"Failed to get ZIA activation status: {err}")
        return _to_dict(result)


def activate_changes(zia_cfg: dict[str, Any]) -> dict[str, Any]:
    """Activate pending ZIA configuration changes."""
    with get_client(zia_cfg) as client:
        result, _, err = client.zia.activate.activate()
        if err:
            raise RuntimeError(f"Failed to activate ZIA changes: {err}")
        return _to_dict(result)
