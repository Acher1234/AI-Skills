#!/usr/bin/env python3
"""
Tuya CLI — interroge l'API Tuya IoT pour contrôler des appareils connectés.

Usage:
  ./tuya.py token                    # Génère un access token
  ./tuya.py devices                   # Liste tous les appareils
  ./tuya.py status <device_id>        # Disponibilité (online/offline)
  ./tuya.py state <device_id>         # État détaillé avec labels
  ./tuya.py on <device_id>            # Allumer
  ./tuya.py off <device_id>           # Éteindre
  ./tuya.py rename <device_id> <nom>  # Renommer
"""

import argparse
import json
import os
import sys

from tuya_connector import TuyaOpenAPI

CONFIG_PATH = os.environ.get(
    "TUYA_CONFIG_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"),
)

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


def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Config introuvable : {CONFIG_PATH}")
        print(f"   Copiez config.example.json → config.json et remplissez vos données.")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


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


# ─── Commands ──────────────────────────────────────────────────────────────

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
    # Pour plugs: switch_1, pour clims IR: switch
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


# ─── CLI ───────────────────────────────────────────────────────────────────

def main():
    config = load_config()
    parser = argparse.ArgumentParser(description="Tuya CLI — contrôle des appareils Tuya IoT")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("token", help="Génère un access token")
    sub.add_parser("devices", help="Liste les appareils")

    p_status = sub.add_parser("status", help="Disponibilité (online/offline)")
    p_status.add_argument("device_id")

    p_state = sub.add_parser("state", help="État détaillé avec labels")
    p_state.add_argument("device_id")

    p_on = sub.add_parser("on", help="Allumer")
    p_on.add_argument("device_id")

    p_off = sub.add_parser("off", help="Éteindre")
    p_off.add_argument("device_id")

    p_rename = sub.add_parser("rename", help="Renommer un appareil")
    p_rename.add_argument("device_id")
    p_rename.add_argument("name", help="Nouveau nom")

    args = parser.parse_args()

    if args.command == "token":
        cmd_token(config)
    elif args.command == "devices":
        cmd_devices(config)
    elif args.command == "status":
        cmd_status(config, args.device_id)
    elif args.command == "state":
        cmd_state(config, args.device_id)
    elif args.command == "on":
        cmd_switch(config, args.device_id, True)
    elif args.command == "off":
        cmd_switch(config, args.device_id, False)
    elif args.command == "rename":
        cmd_rename(config, args.device_id, args.name)


if __name__ == "__main__":
    main()