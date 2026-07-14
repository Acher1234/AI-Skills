#!/usr/bin/env python3
"""
qBittorrent CLI — gère les torrents via l'API WebUI qBittorrent.

Usage:
  ./qbittorrent.py list [--filter STATUS] [--category CAT]
  ./qbittorrent.py add <magnet_or_url> [--category CAT] [--paused]
  ./qbittorrent.py add-file <path> [--category CAT] [--paused]
  ./qbittorrent.py info <hash>
  ./qbittorrent.py files <hash>
  ./qbittorrent.py pause <hash|all>
  ./qbittorrent.py resume <hash|all>
  ./qbittorrent.py delete <hash> [--files]
  ./qbittorrent.py categories | tags | transfer | version
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
import http.cookiejar
from datetime import timedelta

CONFIG_PATH = os.environ.get(
    "QBITTORRENT_CONFIG_PATH",
    "/root/.hermes/qbittorrent-config.json",
)

STATUS_FILTERS = [
    "all", "downloading", "seeding", "completed", "paused",
    "active", "inactive", "stalled", "errored",
]

STATE_EMOJI = {
    "downloading": "⬇️", "stalledDL": "⏸️", "uploading": "⬆️", "stalledUP": "⏸️",
    "pausedDL": "⏸️", "pausedUP": "⏸️", "queuedDL": "⏳", "queuedUP": "⏳",
    "checkingDL": "🔍", "checkingUP": "🔍", "error": "❌", "missingFiles": "⚠️",
}


# ─── Config & Auth ─────────────────────────────────────────────────────────

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Config introuvable : {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def login(config):
    url = config["url"].rstrip("/")
    data = urllib.parse.urlencode({
        "username": config["username"],
        "password": config["password"],
    }).encode()
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    resp = opener.open(f"{url}/api/v2/auth/login", data=data, timeout=10)
    if resp.read().decode().strip() != "Ok.":
        print("❌ Login échoué.")
        sys.exit(1)
    return url, opener


def api_get(url, opener, endpoint, raw=False):
    req = urllib.request.Request(f"{url}/api/v2{endpoint}")
    resp = opener.open(req, timeout=30)
    if raw:
        return resp.read().decode().strip()
    return json.loads(resp.read().decode())


def api_post(url, opener, endpoint, data=None):
    body = urllib.parse.urlencode(data).encode() if data else b""
    req = urllib.request.Request(f"{url}/api/v2{endpoint}", data=body)
    try:
        resp = opener.open(req, timeout=30)
        resp.read()
        return True
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code}: {e.read().decode()}")
        return False


# ─── Formatters ────────────────────────────────────────────────────────────

def fmt_size(b):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"

def fmt_speed(bps):
    return fmt_size(bps) + "/s"

def fmt_progress(p):
    return f"{p*100:.1f}%"

def fmt_eta(s):
    if s >= 8640000: return "∞"
    return str(timedelta(seconds=s))


# ─── Commands ──────────────────────────────────────────────────────────────

def cmd_list(config, status_filter, category):
    url, op = login(config)
    torrents = api_get(url, op, "/torrents/info")
    if status_filter and status_filter != "all":
        torrents = [t for t in torrents if t["state"].startswith(status_filter.lower().rstrip("s"))]
    if category:
        torrents = [t for t in torrents if t.get("category", "") == category]
    if not torrents:
        print("   Aucun torrent trouvé.")
        return
    print(f"📥 Torrents ({len(torrents)}):")
    print()
    for t in torrents:
        emoji = STATE_EMOJI.get(t["state"], "❓")
        print(f"  {emoji} {t['name'][:60]}")
        print(f"     Hash     : {t['hash'][:16]}...")
        print(f"     Progress : {fmt_progress(t['progress'])}  |  Size: {fmt_size(t['size'])}")
        print(f"     DL: {fmt_speed(t['dlspeed'])}  UP: {fmt_speed(t['upspeed'])}  ETA: {fmt_eta(t['eta'])}")
        if t.get("category"):
            print(f"     Category : {t['category']}")
        print()


def cmd_add(config, magnet, category, paused):
    url, op = login(config)
    data = {"urls": magnet}
    if category: data["category"] = category
    if paused: data["paused"] = "true"
    if api_post(url, op, "/torrents/add", data):
        print(f"✅ Torrent ajouté : {magnet[:60]}...")


def cmd_add_file(config, path, category, paused):
    if not os.path.exists(path):
        print(f"❌ Fichier introuvable : {path}")
        return
    url, op = login(config)
    boundary = "----QBITTORRENTCLI"
    with open(path, "rb") as f:
        file_content = f.read()
    filename = os.path.basename(path)

    # Build form-data manually (stdlib, no extra deps)
    body_parts = [
        f"--{boundary}",
        f'Content-Disposition: form-data; name="torrents"; filename="{filename}"',
        "Content-Type: application/x-bittorrent",
        "",
    ]
    body = "\r\n".join(body_parts).encode() + b"\r\n" + file_content + f"\r\n--{boundary}--\r\n".encode()

    full_url = f"{url}/api/v2/torrents/add"
    req = urllib.request.Request(
        full_url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    try:
        # Build a new opener based on the same cookie jar
        cj_opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(op.__dict__.get("cookiejar", None))
        ) if hasattr(op, "handlers") else op
        resp = cj_opener.open(req, timeout=30)
        resp.read()
        print(f"✅ Fichier ajouté : {path}")
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code}: {e.read().decode()}")
    except Exception as e:
        print(f"❌ Erreur: {e}")


def cmd_info(config, hash_val):
    url, op = login(config)
    info = api_get(url, op, f"/torrents/properties?hash={hash_val}")
    print(f"📋 {hash_val[:16]}...")
    print()
    for k, v in info.items():
        print(f"  {k:20s} : {v}")


def cmd_files(config, hash_val):
    url, op = login(config)
    files = api_get(url, op, f"/torrents/files?hash={hash_val}")
    print("📁 Fichiers :")
    for f in files:
        prog = f["progress"] * 100
        icon = "✅" if prog >= 100 else "⬇️"
        print(f"  {icon} [{fmt_size(f['size'])}] {f['name']}")


def cmd_control(config, action, hash_val, delete_files=False):
    url, op = login(config)
    if action == "delete":
        data = {"hashes": hash_val, "deleteFiles": str(delete_files).lower()}
        ok = api_post(url, op, f"/torrents/{action}", data)
    else:
        ok = api_post(url, op, f"/torrents/{action}", {"hashes": hash_val})
    if ok:
        print(f"✅ {action.capitalize()} : {hash_val}")


def cmd_categories(config):
    url, op = login(config)
    cats = api_get(url, op, "/torrents/categories")
    print("📂 Catégories :")
    for name in (cats if isinstance(cats, dict) else {}):
        print(f"  • {name}")


def cmd_tags(config):
    url, op = login(config)
    tags = api_get(url, op, "/torrents/tags")
    print("🏷️ Tags :")
    for t in (tags if isinstance(tags, list) else []):
        print(f"  • {t}")


def cmd_transfer(config):
    url, op = login(config)
    info = api_get(url, op, "/transfer/info")
    print("📊 Transfert :")
    print(f"  DL: {fmt_speed(info['dl_info_speed'])}  |  UP: {fmt_speed(info['up_info_speed'])}")
    print(f"  Total DL: {fmt_size(info['dl_info_data'])}  |  Total UP: {fmt_size(info['up_info_data'])}")


def cmd_version(config):
    url, op = login(config)
    v = api_get(url, op, "/app/version", raw=True)
    print(f"qBittorrent {v}")


# ─── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="qBittorrent CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List torrents / Lister les torrents")
    p_list.add_argument("--filter", choices=STATUS_FILTERS, default="all")
    p_list.add_argument("--category")

    p_add = sub.add_parser("add", help="Add torrent by magnet/URL / Ajouter par magnet/URL")
    p_add.add_argument("magnet")
    p_add.add_argument("--category")
    p_add.add_argument("--paused", action="store_true")

    p_af = sub.add_parser("add-file", help="Add torrent by .torrent file / Ajouter par fichier .torrent")
    p_af.add_argument("path")
    p_af.add_argument("--category")
    p_af.add_argument("--paused", action="store_true")

    p_info = sub.add_parser("info", help="Torrent properties / Propriétés")
    p_info.add_argument("hash")

    p_files = sub.add_parser("files", help="Torrent files / Fichiers du torrent")
    p_files.add_argument("hash")

    p_pause = sub.add_parser("pause", help="Pause torrent")
    p_pause.add_argument("hash")

    p_resume = sub.add_parser("resume", help="Resume torrent / Reprendre")
    p_resume.add_argument("hash")

    p_del = sub.add_parser("delete", help="Delete torrent / Supprimer")
    p_del.add_argument("hash")
    p_del.add_argument("--files", action="store_true")

    sub.add_parser("categories", help="List categories / Catégories")
    sub.add_parser("tags", help="List tags / Tags")
    sub.add_parser("transfer", help="Transfer info / Infos de transfert")
    sub.add_parser("version", help="qBittorrent version")

    args = parser.parse_args()
    config = load_config()

    cmd = args.command
    if cmd == "list":
        cmd_list(config, args.filter, getattr(args, "category", None))
    elif cmd == "add":
        cmd_add(config, args.magnet, getattr(args, "category", None), getattr(args, "paused", False))
    elif cmd == "add-file":
        cmd_add_file(config, args.path, getattr(args, "category", None), getattr(args, "paused", False))
    elif cmd == "info":
        cmd_info(config, args.hash)
    elif cmd == "files":
        cmd_files(config, args.hash)
    elif cmd == "pause":
        cmd_control(config, "pause", args.hash)
    elif cmd == "resume":
        cmd_control(config, "resume", args.hash)
    elif cmd == "delete":
        cmd_control(config, "delete", args.hash, getattr(args, "files", False))
    elif cmd == "categories":
        cmd_categories(config)
    elif cmd == "tags":
        cmd_tags(config)
    elif cmd == "transfer":
        cmd_transfer(config)
    elif cmd == "version":
        cmd_version(config)


if __name__ == "__main__":
    main()