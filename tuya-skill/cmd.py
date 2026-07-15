#!/usr/bin/env python3
"""
Tuya CLI — point d'entrée (dispatch Cloud / Local).

La logique métier vit dans :
  - cloud.py  → commandes Cloud (API Tuya IoT)
  - local.py  → commandes Local (LAN via tinytuya)

Usage (Cloud):
  ./cmd.py token                    # Génère un access token
  ./cmd.py devices                  # Liste tous les appareils
  ./cmd.py status <device_id>       # Disponibilité (online/offline)
  ./cmd.py state <device_id>        # État détaillé avec labels
  ./cmd.py on <device_id>           # Allumer
  ./cmd.py off <device_id>          # Éteindre
  ./cmd.py rename <device_id> <nom> # Renommer

Usage (Local / LAN via tinytuya):
  ./cmd.py local-scan               # Scan LAN → ip + device_id + version
  ./cmd.py local-sync               # Récupère les local keys (Cloud) → devices.json
  ./cmd.py local-devices            # Liste les appareils depuis devices.json
  ./cmd.py local-status <device>    # Disponibilité en LAN (online/offline)
  ./cmd.py local-state <device>     # État détaillé en LAN (DPS)
  ./cmd.py local-on <device>        # Allumer en LAN
  ./cmd.py local-off <device>       # Éteindre en LAN
"""

import argparse
import json
import os
import sys

import cloud
import local

CONFIG_PATH = os.environ.get(
    "TUYA_CONFIG_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"),
)


def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Config introuvable : {CONFIG_PATH}")
        print("   Copiez config.example.json → config.json et remplissez vos données.")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def build_parser():
    parser = argparse.ArgumentParser(description="Tuya CLI — contrôle des appareils Tuya IoT")
    sub = parser.add_subparsers(dest="command", required=True)

    # ─── Cloud ───────────────────────────────────────────────────────────
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

    p_clim = sub.add_parser("clim", help="Régler une clim (mode, température, ventilation)")
    p_clim.add_argument("device_id")
    p_clim.add_argument("mode", choices=["cold", "heat", "auto", "fan", "dry"], help="Mode")
    p_clim.add_argument("temp", type=int, help="Température (16-30)")
    p_clim.add_argument("--fan", choices=["auto", "low", "mid", "high"], default="auto", help="Ventilation")

    # ─── Local ───────────────────────────────────────────────────────────
    p_lscan = sub.add_parser("local-scan", help="Scan LAN → ip + device_id + version")
    p_lscan.add_argument("--seconds", type=int, default=18, help="Durée du scan (défaut 18)")

    p_lsync = sub.add_parser(
        "local-sync", help="Récupère les local keys (Cloud) → devices.json"
    )
    p_lsync.add_argument("--device-id", help="Device ID échantillon (sinon pris du scan)")
    p_lsync.add_argument("--seconds", type=int, default=18, help="Durée du scan LAN")
    p_lsync.add_argument("--no-scan", action="store_true", help="Ne pas scanner le LAN")
    p_lsync.add_argument("--show-keys", action="store_true", help="Afficher les local keys en clair")

    p_ldev = sub.add_parser("local-devices", help="Liste les appareils depuis devices.json")
    p_ldev.add_argument("--show-keys", action="store_true", help="Afficher les local keys en clair")

    p_lstatus = sub.add_parser("local-status", help="Disponibilité en LAN (online/offline)")
    p_lstatus.add_argument("device_id", help="Device ID ou nom (depuis devices.json)")

    p_lstate = sub.add_parser("local-state", help="État détaillé en LAN (DPS)")
    p_lstate.add_argument("device_id", help="Device ID ou nom (depuis devices.json)")

    p_lon = sub.add_parser("local-on", help="Allumer en LAN")
    p_lon.add_argument("device_id", help="Device ID ou nom (depuis devices.json)")

    p_loff = sub.add_parser("local-off", help="Éteindre en LAN")
    p_loff.add_argument("device_id", help="Device ID ou nom (depuis devices.json)")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    config = load_config()

    if args.command == "token":
        cloud.cmd_token(config)
    elif args.command == "devices":
        cloud.cmd_devices(config)
    elif args.command == "status":
        cloud.cmd_status(config, args.device_id)
    elif args.command == "state":
        cloud.cmd_state(config, args.device_id)
    elif args.command == "on":
        cloud.cmd_switch(config, args.device_id, True)
    elif args.command == "off":
        cloud.cmd_switch(config, args.device_id, False)
    elif args.command == "rename":
        cloud.cmd_rename(config, args.device_id, args.name)
    elif args.command == "clim":
        cloud.cmd_clim(config, args.device_id, args.mode, args.temp, args.fan)
    elif args.command == "local-scan":
        local.cmd_local_scan(config, args.seconds)
    elif args.command == "local-sync":
        local.cmd_local_sync(
            config,
            args.device_id,
            args.seconds,
            do_scan=not args.no_scan,
            show_keys=args.show_keys,
        )
    elif args.command == "local-devices":
        local.cmd_local_devices(config, args.show_keys)
    elif args.command == "local-status":
        local.cmd_local_status(config, args.device_id)
    elif args.command == "local-state":
        local.cmd_local_state(config, args.device_id)
    elif args.command == "local-on":
        local.cmd_local_switch(config, args.device_id, True)
    elif args.command == "local-off":
        local.cmd_local_switch(config, args.device_id, False)


if __name__ == "__main__":
    main()
