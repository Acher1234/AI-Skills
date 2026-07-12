#!/usr/bin/env python3
"""
Tuya CLI — interroge l'API Tuya IoT pour contrôler des appareils connectés.

Usage:
  ./tuya.py token              # Génère et affiche un access token
  ./tuya.py devices             # Liste les appareils
  ./tuya.py status <device_id>  # État d'un appareil
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


# ─── Config ────────────────────────────────────────────────────────────────

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Config introuvable : {CONFIG_PATH}")
        print(f"   Copiez config.example.json → config.json et remplissez vos données.")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_client(config):
    """Crée et connecte un client Tuya OpenAPI."""
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
    """Génère et affiche un access token."""
    region = config.get("region", "eu")
    base_url = TUYA_BASE_URLS.get(region, TUYA_BASE_URLS["eu"])
    client = TuyaOpenAPI(base_url, config["access_id"], config["access_secret"])
    # connect() already fetched the token
    response = client.connect()
    result = response.get("result", {})
    token = result.get("access_token", "")
    print(f"✅ Token généré !")
    print(f"   access_token : {token[:20]}...{token[-10:]}" if len(token) > 30 else f"   access_token : {token}")
    print(f"   expire_time  : {result.get('expire_time', '-')}s")
    print(f"   uid          : {result.get('uid', '-')}")
    print(f"   platform_url : {TUYA_BASE_URLS.get(config.get('region', 'eu'), '?')}")


def cmd_devices(config):
    """Liste les appareils Tuya."""
    client = get_client(config)
    project_code = config.get("project_code", "")
    response = client.get(f"/v1.0/devices?project_code={project_code}")

    if not response.get("success"):
        print(f"❌ {response}")
        return

    devices = response.get("result", {}).get("devices", [])
    if not devices:
        print("   Aucun appareil trouvé.")
        return

    print(f"📱 Appareils Tuya ({len(devices)}):")
    print()
    for d in devices:
        print(f"  • {d.get('name', '-')}")
        print(f"    ID       : {d.get('id', '-')}")
        print(f"    Model    : {d.get('model', '-')}")
        status = "🟢 online" if d.get("online") else "🔴 offline"
        print(f"    Status   : {status}")
        print()


def cmd_status(config, device_id):
    """Affiche l'état d'un appareil."""
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


# ─── CLI ───────────────────────────────────────────────────────────────────

def main():
    config = load_config()
    parser = argparse.ArgumentParser(description="Tuya CLI — contrôle des appareils Tuya IoT")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("token", help="Génère et affiche un access token")
    sub.add_parser("devices", help="Liste les appareils")

    p_status = sub.add_parser("status", help="État d'un appareil")
    p_status.add_argument("device_id", help="ID de l'appareil")

    args = parser.parse_args()

    if args.command == "token":
        cmd_token(config)
    elif args.command == "devices":
        cmd_devices(config)
    elif args.command == "status":
        cmd_status(config, args.device_id)


if __name__ == "__main__":
    main()