"""ZIdentity client for Hermes Agent CLI (OneAPI / ZscalerClient)."""

from __future__ import annotations

from typing import Any

from zscaler import ZscalerClient


def build_client_config(zid_cfg: dict[str, Any]) -> dict[str, Any]:
    """Build ZscalerClient (OneAPI) config from config.json zidentity section."""
    config: dict[str, Any] = {
        "clientId": zid_cfg["client_id"],
        "clientSecret": zid_cfg["client_secret"],
        "vanityDomain": zid_cfg["vanity_domain"],
        "logging": {"enabled": False, "verbose": False},
    }
    cloud = (zid_cfg.get("cloud") or "").strip()
    if cloud:
        config["cloud"] = cloud
    customer_id = (zid_cfg.get("customer_id") or "").strip()
    if customer_id:
        config["customerId"] = customer_id
    return config


def get_client(zid_cfg: dict[str, Any]) -> ZscalerClient:
    """Return an authenticated OneAPI Zscaler client for ZIdentity."""
    return ZscalerClient(build_client_config(zid_cfg))


def _records_as_dicts(page_obj: Any) -> list[dict[str, Any]]:
    """Normalize ZIdentity paginated responses (`.records`) to dicts."""
    if page_obj is None:
        return []
    records = getattr(page_obj, "records", None)
    if records is None:
        if hasattr(page_obj, "as_dict"):
            return [page_obj.as_dict()]
        return [dict(page_obj)]
    return [r.as_dict() if hasattr(r, "as_dict") else dict(r) for r in records]


def test_connection(zid_cfg: dict[str, Any]) -> tuple[bool, str]:
    """Verify ZIdentity credentials by listing groups."""
    try:
        with get_client(zid_cfg) as client:
            groups, _, err = client.zidentity.groups.list_groups()
            if err:
                return False, f"ZIdentity API error: {err}"
            count = len(getattr(groups, "records", []) or [])
            return True, f"ZIdentity connected (groups returned: {count})"
    except Exception as exc:  # noqa: BLE001
        return False, f"ZIdentity connection failed: {exc}"


def list_groups(zid_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """List ZIdentity groups."""
    with get_client(zid_cfg) as client:
        groups, _, err = client.zidentity.groups.list_groups()
        if err:
            raise RuntimeError(f"Failed to list ZIdentity groups: {err}")
        return _records_as_dicts(groups)


def list_users(zid_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """List ZIdentity users."""
    with get_client(zid_cfg) as client:
        users, _, err = client.zidentity.users.list_users()
        if err:
            raise RuntimeError(f"Failed to list ZIdentity users: {err}")
        return _records_as_dicts(users)
