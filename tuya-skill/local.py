#!/usr/bin/env python3
"""
Commandes locales (LAN via tinytuya) pour le CLI Tuya.

- local-scan    : scan LAN → ip + device_id + version (pas de local key)
- local-sync    : récupère les local keys via le Cloud → devices.json
- local-devices : liste les appareils depuis devices.json

Le scan LAN seul ne fournit JAMAIS les local keys : elles sont récupérées
via l'API Cloud (tinytuya.Cloud.getdevices), comme le fait le `wizard`.
"""

import json
import os
import sys


def _load_tinytuya():
    try:
        import tinytuya  # noqa: WPS433 (import tardif volontaire)
        return tinytuya
    except ImportError:
        print("❌ tinytuya n'est pas installé.")
        print("   Installez-le : pip install tinytuya")
        sys.exit(1)


def _skill_dir():
    return os.path.dirname(os.path.abspath(__file__))


def _resolve_path(path, default):
    path = path or default
    if not os.path.isabs(path):
        path = os.path.join(_skill_dir(), path)
    return path


def _devices_file_path(config):
    return _resolve_path(
        os.environ.get("TUYA_DEVICES_PATH") or config.get("local_devices_file"),
        "devices.json",
    )


def _scan_file_path(config):
    return _resolve_path(os.environ.get("TUYA_SCAN_PATH"), "tuya-scan.json")


def _mask_key(key):
    if not key:
        return "-"
    return f"{key[:4]}…{key[-2:]}" if len(key) > 6 else "•••"


def _scan_lan(tinytuya, seconds):
    """Scan LAN → dict {device_id: {ip, version, product_key}}."""
    found = tinytuya.deviceScan(False, seconds)
    result = {}
    for entry in found.values():
        did = entry.get("gwId") or entry.get("id")
        if did:
            result[did] = {
                "ip": entry.get("ip"),
                "version": entry.get("version"),
                "product_key": entry.get("productKey"),
            }
    return result


def _read_devices(config):
    path = _devices_file_path(config)
    if not os.path.exists(path):
        print(f"❌ {path} introuvable. Lancez d'abord : ./tuya.py local-sync")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def _resolve_address(entry, devices):
    """IP de l'appareil, sinon celle d'un autre partageant la même local key, sinon 'Auto'."""
    if entry.get("ip"):
        return entry["ip"]
    key = entry.get("key")
    if key:
        for d in devices:
            if d is not entry and d.get("key") == key and d.get("ip"):
                return d["ip"]
    return "Auto"


def _device_handle(tinytuya, config, device_id):
    """Construit un tinytuya.Device depuis devices.json (recherche par id ou nom)."""
    devices = _read_devices(config)
    entry = next(
        (
            d
            for d in devices
            if d.get("id") == device_id or d.get("name") == device_id
        ),
        None,
    )
    if not entry:
        print(f"❌ Appareil « {device_id} » introuvable dans {_devices_file_path(config)}.")
        print("   Lancez d'abord : ./tuya.py local-sync")
        sys.exit(1)
    key = entry.get("key")
    if not key:
        print(f"❌ Local key manquante pour « {device_id} ». Relancez : ./tuya.py local-sync")
        sys.exit(1)
    address = _resolve_address(entry, devices)
    try:
        version = float(entry.get("version") or 3.3)
    except (TypeError, ValueError):
        version = 3.3
    dev = tinytuya.Device(entry["id"], address=address, local_key=key, version=version)
    return entry, dev


def cmd_local_scan(config, seconds):
    tinytuya = _load_tinytuya()
    print(f"🔍 Scan du réseau local ({seconds}s)…  (UDP 6666/6667/7000)")
    scan_map = _scan_lan(tinytuya, seconds)
    out_path = _scan_file_path(config)
    with open(out_path, "w") as f:
        json.dump(scan_map, f, indent=2)
    print(f"✅ {len(scan_map)} appareil(s) trouvé(s) → {out_path}")
    print()
    for did, info in scan_map.items():
        print(f"  • {did}")
        print(f"    IP       : {info.get('ip', '-')}")
        print(f"    Version  : {info.get('version', '-')}")
    if not scan_map:
        print("   Aucun appareil trouvé (vérifiez que vous êtes sur le même LAN,")
        print("   que le pare-feu autorise UDP 6666/6667/7000, et l'app fermée).")


def cmd_local_sync(config, device_id, seconds, do_scan, show_keys):
    tinytuya = _load_tinytuya()
    region = config.get("region", "eu")

    scan_map = {}
    if do_scan:
        print(f"🔍 Scan du réseau local ({seconds}s)…")
        scan_map = _scan_lan(tinytuya, seconds)
        print(f"   {len(scan_map)} appareil(s) vus sur le LAN.")
        if not device_id and scan_map:
            device_id = next(iter(scan_map))

    if not device_id:
        print("❌ Aucun device_id disponible pour interroger le Cloud.")
        print("   Fournissez --device-id <id> ou laissez le scan activé sur le LAN.")
        sys.exit(1)

    print(f"☁️  Récupération des local keys via le Cloud (region={region})…")
    cloud = tinytuya.Cloud(
        apiRegion=region,
        apiKey=config["access_id"],
        apiSecret=config["access_secret"],
        apiDeviceID=device_id,
    )
    devices = cloud.getdevices(verbose=False)
    if isinstance(devices, dict) and devices.get("Error"):
        print(f"❌ Erreur Cloud : {devices}")
        sys.exit(1)

    for d in devices:
        did = d.get("id")
        if did in scan_map:
            if scan_map[did].get("ip"):
                d["ip"] = scan_map[did]["ip"]
            if scan_map[did].get("version"):
                d["version"] = scan_map[did]["version"]

    out_path = _devices_file_path(config)
    with open(out_path, "w") as f:
        json.dump(devices, f, indent=2)

    print(f"✅ {len(devices)} appareil(s) avec local key → {out_path}")
    print()
    for d in devices:
        key = d.get("key", "")
        shown = key if show_keys else _mask_key(key)
        print(f"  • {d.get('name', '-')}")
        print(f"    ID        : {d.get('id', '-')}")
        print(f"    Local key : {shown}")
        print(f"    IP        : {d.get('ip', '-')}")
        print(f"    Version   : {d.get('version', '-')}")


def cmd_local_devices(config, show_keys):
    devices = _read_devices(config)
    print(f"📱 Appareils locaux ({len(devices)}) — {_devices_file_path(config)}")
    print()
    for d in devices:
        key = d.get("key", "")
        shown = key if show_keys else _mask_key(key)
        print(f"  • {d.get('name', '-')}")
        print(f"    ID        : {d.get('id', '-')}")
        print(f"    Local key : {shown}")
        print(f"    IP        : {d.get('ip', '-')}")
        print(f"    Version   : {d.get('version', '-')}")
        print()


def cmd_local_status(config, device_id):
    tinytuya = _load_tinytuya()
    entry, dev = _device_handle(tinytuya, config, device_id)
    name = entry.get("name", device_id)
    data = dev.status()
    reachable = isinstance(data, dict) and not data.get("Error") and "dps" in data
    status_str = "🟢 ONLINE (LAN)" if reachable else "🔴 UNREACHABLE (LAN)"
    print(f"{status_str}  |  {name}")
    print(f"   ID       : {entry.get('id', '-')}")
    print(f"   IP       : {entry.get('ip', 'Auto')}")
    print(f"   Version  : {entry.get('version', '-')}")
    if not reachable:
        print(f"   Détail   : {data}")


def cmd_local_state(config, device_id):
    tinytuya = _load_tinytuya()
    entry, dev = _device_handle(tinytuya, config, device_id)
    name = entry.get("name", device_id)
    data = dev.status()
    if isinstance(data, dict) and data.get("Error"):
        print(f"❌ {name} : {data}")
        return
    dps = data.get("dps", {}) if isinstance(data, dict) else {}
    print(f"📊 État local de « {name} » (id={entry.get('id')}, ip={entry.get('ip', 'Auto')}) :")
    print()
    if not dps:
        print("   Aucune donnée DPS renvoyée.")
        return
    for code, value in dps.items():
        if value is True:
            shown = "🟢 ON"
        elif value is False:
            shown = "🔴 OFF"
        else:
            shown = value
        print(f"  DPS {code:>3} : {shown}")


def cmd_local_switch(config, device_id, value):
    tinytuya = _load_tinytuya()
    entry, dev = _device_handle(tinytuya, config, device_id)
    name = entry.get("name", device_id)
    result = dev.turn_on() if value else dev.turn_off()
    if isinstance(result, dict) and result.get("Error"):
        print(f"❌ {name} : {result}")
        return
    print(f"✅ {'🟢 ON' if value else '🔴 OFF'}  |  {name} (LAN)")
