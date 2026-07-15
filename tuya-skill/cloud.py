#!/usr/bin/env python3
"""
Commandes Cloud (API Tuya IoT) pour le CLI Tuya.

Utilise le SDK `tuya-connector-python` pour parler à l'API cloud Tuya.
"""

import json
import os
import sys

from tuya_connector import TuyaOpenAPI

TUYA_BASE_URLS = {
    "eu": "https://openapi.tuyaeu.com",
    "us": "https://openapi.tuyaus.com",
    "cn": "https://openapi.tuyacn.com",
    "in": "https://openapi.tuyain.com",
}

STATE_LABELS = {
    "power": "🔌 Power", "mode": "🔄 Mode", "temp": "🌡️ Temp",
    "wind": "💨 Wind", "switch_1": "🔌 Switch", "switch_2": "🔌 Switch 2",
    "child_lock": "🔒 Child Lock", "countdown_1": "⏱ Countdown",
    "fan": "💨 Fan",
}
STATE_MODES = {"0": "auto", "1": "cool", "2": "heat", "3": "fan", "4": "dry"}
STATE_WINDS = {"0": "low", "1": "mid", "2": "high", "3": "auto"}

DEFAULT_MODE_MAP = {"cold": 1, "heat": 2, "auto": 0, "fan": 3, "dry": 4}

BRAND_MAPS = {
    "electra": {"cold": 0, "heat": 1, "auto": 2, "fan": 3, "dry": 4},
}


def _get_mode_map(device_id):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "devices.json")
    if os.path.exists(path):
        with open(path) as f:
            devices = json.load(f)
        for d in devices:
            if d.get("id") == device_id:
                brand = d.get("mode_map", "default")
                return BRAND_MAPS.get(brand, DEFAULT_MODE_MAP)
    return DEFAULT_MODE_MAP


def get_client(config):
    region = config.get("region", "eu")
    base_url = TUYA_BASE_URLS.get(region, TUYA_BASE_URLS["eu"])
    client = TuyaOpenAPI(base_url, config["access_id"], config["access_secret"])
    response = client.connect()
    if not response.get("success"):
        print(f"❌ Connexion échouée : {response}")
        sys.exit(1)
    return client


def _human_value(code, value):
    raw = str(value)
    if isinstance(value, bool):
        return "🟢 ON" if value else "🔴 OFF"
    if code == "mode":
        return STATE_MODES.get(raw, raw)
    if code in ("wind", "fan"):
        return STATE_WINDS.get(raw, raw)
    return value


def cmd_token(config):
    region = config.get("region", "eu")
    base_url = TUYA_BASE_URLS.get(region, TUYA_BASE_URLS["eu"])
    client = TuyaOpenAPI(base_url, config["access_id"], config["access_secret"])
    response = client.connect()
    result = response.get("result", {})
    token = result.get("access_token", "")
    print(f"✅ Token généré !")
    print(f"   access_token : {token[:20]}...{token[-10:]}" if len(token) > 30 else f"   access_token : {token}")
    print(f"   expire_time  : {result.get('expire_time', '-')}s")
    print(f"   uid          : {result.get('uid', '-')}")
    print(f"   platform_url : {TUYA_BASE_URLS.get(config.get('region', 'eu'), '?')}")


def cmd_devices(config):
    client = get_client(config)
    response = client.get("/v2.0/cloud/thing/device?page_no=1&page_size=20")
    if not response.get("success"):
        print(f"❌ {response}")
        return
    result = response.get("result", {})
    if isinstance(result, list):
        devices = result
    elif isinstance(result, dict):
        devices = result.get("list", result.get("devices", []))
    else:
        devices = []
    if not devices:
        print("   Aucun appareil trouvé.")
        return
    print(f"📱 Appareils Tuya ({len(devices)}):")
    print()
    for d in devices:
        name = d.get("customName", d.get("name", "-"))
        print(f"  • {name}")
        print(f"    ID       : {d.get('id', '-')}")
        print(f"    Model    : {d.get('model', '-')}")
        is_online = d.get("isOnline", d.get("online", False))
        print(f"    Status   : {'🟢 online' if is_online else '🔴 offline'}")
        print()


def cmd_status(config, device_id):
    client = get_client(config)
    response = client.get("/v2.0/cloud/thing/device?page_no=1&page_size=20")
    if not response.get("success"):
        print(f"❌ {response}")
        return
    result = response.get("result", [])
    if isinstance(result, dict):
        result = result.get("list", [])
    device = next((d for d in result if d.get("id") == device_id), None)
    if not device:
        print(f"❌ Appareil {device_id} introuvable.")
        return
    name = device.get("customName", device.get("name", "-"))
    is_online = device.get("isOnline", False)
    status_str = "🟢 ONLINE" if is_online else "🔴 OFFLINE"
    print(f"{status_str}  |  {name}")
    print(f"   Model    : {device.get('model', '-')}")
    print(f"   Product  : {device.get('productName', '-')}")
    if device.get("ip"):
        print(f"   IP       : {device['ip']}")


def cmd_state(config, device_id):
    client = get_client(config)
    response = client.get(f"/v1.0/devices/{device_id}/status")
    if not response.get("success"):
        print(f"❌ {response}")
        return
    status = response.get("result", [])
    print(f"📊 État de « {device_id} » :")
    print()
    for s in status:
        code = s.get("code", "-")
        label = STATE_LABELS.get(code, code)
        value = _human_value(code, s.get("value", "-"))
        print(f"  {label:20s} : {value}")


def cmd_switch(config, device_id, value):
    client = get_client(config)
    for code in ("switch_1", "switch"):
        data = {"commands": [{"code": code, "value": value}]}
        response = client.post(f"/v1.0/devices/{device_id}/commands", data)
        if response.get("success"):
            print(f"✅ {'🟢 ON' if value else '🔴 OFF'}  |  {device_id}")
            return
    print(f"❌ {response}")


def cmd_rename(config, device_id, new_name):
    client = get_client(config)
    data = {"name": new_name}
    response = client.put(f"/v1.0/devices/{device_id}", data)
    if response.get("success"):
        print(f"✅ Renommé → « {new_name} »  |  {device_id}")
    else:
        print(f"❌ {response}")


def cmd_clim(config, device_id, mode, temp, fan):
    """Règle une clim IR (mode, température, ventilation)."""
    client = get_client(config)
    mode_map = _get_mode_map(device_id)
    fan_map = {"auto": 0, "low": 1, "mid": 2, "high": 3}

    m_val = mode_map.get(mode, 0)
    f_val = fan_map.get(fan, 0)

    for c, v in [("M", m_val), ("T", temp), ("F", f_val)]:
        data = {"commands": [{"code": c, "value": v}]}
        client.post(f"/v1.0/devices/{device_id}/commands", data)

    labels = {"cold": "❄️ Froid", "heat": "🔥 Chaud", "auto": "🌬️ Auto", "fan": "💨 Ventilo", "dry": "💧 Dry"}
    print(f"✅ {labels.get(mode, mode)}  |  🌡️ {temp}°C  |  💨 {fan}")


def cmd_cloud_sync(config, show_keys=False):
    """Récupère les devices et local keys via le Cloud → devices.json (no local scan)."""
    client = get_client(config)
    response = client.get("/v2.0/cloud/thing/device?page_no=1&page_size=20")
    if not response.get("success"):
        print(f"❌ {response}")
        return
    result = response.get("result", [])
    if isinstance(result, dict):
        result = result.get("list", result.get("devices", []))
    if not result:
        print("❌ Aucun appareil trouvé.")
        return

    devices = []
    for d in result:
        name = d.get("customName", d.get("name", "-"))
        entry = {
            "id": d.get("id"),
            "name": name,
            "local_key": d.get("localKey", ""),
            "ip": d.get("ip", ""),
            "version": "",
            "model": d.get("model", ""),
            "product_id": d.get("productId", ""),
        }
        if "clim" in name.lower() or "mazgan" in name.lower():
            entry["mode_map"] = "electra"
        devices.append(entry)

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "devices.json")
    with open(path, "w") as f:
        json.dump(devices, f, indent=2)
        f.write("\n")

    print(f"✅ {len(devices)} appareil(s) → {path}")
    if show_keys:
        for d in devices:
            key = d["local_key"]
            shown = f"{key[:10]}..." if key else "-"
            print(f"  • {d['name']:25s} | key: {shown}")
    else:
        print("   (utilisez --show-keys pour voir les clés)")