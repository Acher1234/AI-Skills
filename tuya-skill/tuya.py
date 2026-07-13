#!/usr/bin/env python3
"""
Tuya CLI — interroge l'API Tuya IoT pour contrôler des appareils connectés.

Usage:
  ./tuya.py token              # Génère et affiche un access token
  ./tuya.py devices             # Liste les appareils
  ./tuya.py state <device_id>   # État simplifié (ON/OFF)
  ./tuya.py status <device_id>  # État complet
  ./tuya.py on <device_id>      # Allumer
  ./tuya.py off <device_id>     # Éteindre
  ./tuya.py switch <device_id> [on/off]  # Basculer
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
        name = d.get('customName', d.get('name', '-'))
        print(f"  • {name}")
        print(f"    ID       : {d.get('id', '-')}")
        print(f"    Model    : {d.get('model', '-')}")
        is_online = d.get("isOnline", d.get("online", False))
        print(f"    Status   : {'🟢 online' if is_online else '🔴 offline'}")
        print()


def cmd_state(config, device_id):
    client = get_client(config)
    response = client.get(f"/v1.0/devices/{device_id}/status")
    if not response.get("success"):
        print(f"❌ {response}")
        return
    status = response.get("result", [])
    switch = next((s for s in status if "switch" in s.get("code", "")), None)
    if switch:
        is_on = switch.get("value", False)
        print(f"{'🟢 ON' if is_on else '🔴 OFF'}  |  {switch['code']} = {switch['value']}")
    else:
        for s in status:
            print(f"  {s.get('code', '-'):20s} : {s.get('value', '-')}")


def cmd_status(config, device_id):
    client = get_client(config)
    response = client.get(f"/v1.0/devices/{device_id}/status")
    if not response.get("success"):
        print(f"❌ {response}")
        return
    status = response.get("result", [])
    print(f"📊 État de « {device_id} » :")
    print()
    for s in status:
        print(f"  {s.get('code', '-'):20s} : {s.get('value', '-')}")


def cmd_switch(config, device_id, value):
    client = get_client(config)
    data = {"commands": [{"code": "switch_1", "value": value}]}
    response = client.post(f"/v1.0/devices/{device_id}/commands", data)
    if response.get("success"):
        print(f"✅ {'🟢 ON' if value else '🔴 OFF'}  |  {device_id}")
    else:
        print(f"❌ {response}")


# ─── CLI ───────────────────────────────────────────────────────────────────

def main():
    config = load_config()
    parser = argparse.ArgumentParser(description="Tuya CLI — contrôle des appareils Tuya IoT")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("token", help="Génère un access token")
    sub.add_parser("devices", help="Liste les appareils")

    p_state = sub.add_parser("state", help="État simplifié (ON/OFF)")
    p_state.add_argument("device_id")

    p_status = sub.add_parser("status", help="État complet")
    p_status.add_argument("device_id")

    p_on = sub.add_parser("on", help="Allumer")
    p_on.add_argument("device_id")

    p_off = sub.add_parser("off", help="Éteindre")
    p_off.add_argument("device_id")

    args = parser.parse_args()

    if args.command == "token":
        cmd_token(config)
    elif args.command == "devices":
        cmd_devices(config)
    elif args.command == "state":
        cmd_state(config, args.device_id)
    elif args.command == "status":
        cmd_status(config, args.device_id)
    elif args.command == "on":
        cmd_switch(config, args.device_id, True)
    elif args.command == "off":
        cmd_switch(config, args.device_id, False)


if __name__ == "__main__":
    main()