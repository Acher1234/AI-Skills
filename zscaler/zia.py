"""ZIA (Zscaler Internet Access) client for Hermes Agent CLI."""

from __future__ import annotations

from typing import Any

from zscaler.oneapi_client import LegacyZIAClient


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
    super_category: str = "USER_DEFINED",
    description: str | None = None,
) -> dict[str, Any]:
    """Create a custom ZIA URL category."""
    if not name or not name.strip():
        raise ValueError("name requis pour créer une URL category")

    kwargs: dict[str, Any] = {
        "configured_name": name.strip(),
        "custom_category": True,
    }
    if urls:
        kwargs["urls"] = urls
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


def list_forwarding_rules(
    zia_cfg: dict[str, Any],
    search: str | None = None,
) -> list[dict[str, Any]]:
    """List ZIA forwarding control rules.

    Note: ``forwarding_control`` is missing on LegacyZIAClientHelper, so we
    instantiate ForwardingControlAPI with the legacy request executor.
    """
    from zscaler.zia.forwarding_control import ForwardingControlAPI

    query_params: dict[str, Any] = {}
    if search:
        query_params["search"] = search

    with get_client(zia_cfg) as client:
        # Legacy helper has no .forwarding_control property; OneAPI client.zia does.
        zia_svc = client.zia
        if hasattr(zia_svc, "forwarding_control"):
            api = zia_svc.forwarding_control
        else:
            api = ForwardingControlAPI(zia_svc.request_executor)

        rules, _, err = api.list_rules(query_params=query_params or None)
        if err:
            raise RuntimeError(f"Failed to list forwarding rules: {err}")
        return [r.as_dict() if hasattr(r, "as_dict") else dict(r) for r in (rules or [])]


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
        add: Si True, ajoute aux groupes existants au lieu de remplacer.
        department_id / department_name: Force le département de l'user.
        default_department_id: Département utilisé seulement si l'user n'en a pas
            (requis par l'API ZIA sur PUT /users).
    """
    groups_payload = resolve_group_ids(zia_cfg, group_ids=group_ids, group_names=group_names)
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

        if add:
            existing = [
                {"id": int(g["id"])}
                for g in (current.get("groups") or [])
                if g.get("id") not in (None, 0, "0")
            ]
            seen = {g["id"] for g in existing}
            for g in groups_payload:
                if g["id"] not in seen:
                    seen.add(g["id"])
                    existing.append(g)
            groups_payload = existing

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
