"""ZPA (Zscaler Private Access) client for Hermes Agent CLI."""

from __future__ import annotations

from typing import Any

from zscaler.oneapi_client import LegacyZPAClient


def build_client_config(zpa_cfg: dict[str, Any]) -> dict[str, Any]:
    """Build LegacyZPAClient config from config.json zpa section."""
    config: dict[str, Any] = {
        "clientId": zpa_cfg["client_id"],
        "clientSecret": zpa_cfg["client_secret"],
        "customerId": zpa_cfg["customer_id"],
        "cloud": zpa_cfg.get("cloud") or "PRODUCTION",
        "logging": {"enabled": False, "verbose": False},
    }
    microtenant_id = (zpa_cfg.get("microtenant_id") or "").strip()
    if microtenant_id:
        config["microtenantId"] = microtenant_id
    return config


def get_client(zpa_cfg: dict[str, Any]) -> LegacyZPAClient:
    """Return an authenticated Legacy ZPA client."""
    return LegacyZPAClient(build_client_config(zpa_cfg))


def test_connection(zpa_cfg: dict[str, Any]) -> tuple[bool, str]:
    """Verify ZPA credentials by listing application segments (page size 1)."""
    try:
        with get_client(zpa_cfg) as client:
            segments, _, err = client.zpa.application_segment.list_segments(
                query_params={"page": "1", "page_size": "1"}
            )
            if err:
                return False, f"ZPA API error: {err}"
            count = len(segments) if segments else 0
            return True, f"ZPA connected (sample segments returned: {count})"
    except Exception as exc:  # noqa: BLE001
        return False, f"ZPA connection failed: {exc}"


def list_application_segments(
    zpa_cfg: dict[str, Any],
    page: int = 1,
    page_size: int = 20,
) -> list[dict[str, Any]]:
    """List ZPA application segments."""
    with get_client(zpa_cfg) as client:
        segments, _, err = client.zpa.application_segment.list_segments(
            query_params={"page": str(page), "page_size": str(page_size)}
        )
        if err:
            raise RuntimeError(f"Failed to list application segments: {err}")
        return [s.as_dict() if hasattr(s, "as_dict") else dict(s) for s in (segments or [])]


def list_segment_groups(
    zpa_cfg: dict[str, Any],
    page: int = 1,
    page_size: int = 20,
) -> list[dict[str, Any]]:
    """List ZPA segment groups."""
    with get_client(zpa_cfg) as client:
        groups, _, err = client.zpa.segment_groups.list_groups(
            query_params={"page": str(page), "page_size": str(page_size)}
        )
        if err:
            raise RuntimeError(f"Failed to list segment groups: {err}")
        return [g.as_dict() if hasattr(g, "as_dict") else dict(g) for g in (groups or [])]
