#!/usr/bin/env python3
"""
C411 CLI — recherche et téléchargement de torrents via l'API C411 (Torznab).

Usage:
  ./c411.py search <query> [--cat CAT] [--limit N]
  ./c411.py download <torrent_url_or_hash>
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET

CONFIG_PATH = os.environ.get("C411_CONFIG_PATH", "/root/.hermes/c411-config.json")

CATEGORIES = {
    "movies": "2000",
    "tv": "5000",
    "music": "3000",
    "games": "1000",
    "software": "4000",
    "anime": "2060,5070",
    "books": "7000,3030",
    "all": "",
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Config introuvable : {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def api_get(config, params):
    url = f"{config['url'].rstrip('/')}/api?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; Hermes-C411/1.0)"
    })
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code}: {e.read().decode()}")
        sys.exit(1)


def parse_results(xml_text):
    root = ET.fromstring(xml_text)
    results = []
    for item in root.findall(".//item"):
        title = item.findtext("title", "")
        size = item.findtext("size", "0")
        link_el = item.find("link")
        link = link_el.text if link_el is not None else ""
        results.append({
            "title": title,
            "size": int(size),
            "link": link,
        })
    return results


def fmt_size(b):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def cmd_search(config, query, category, limit):
    params = {
        "apikey": config["api_key"],
        "t": "search",
        "q": query,
        "limit": str(limit),
    }
    if category and category != "all":
        params["cat"] = CATEGORIES.get(category, category)

    xml_text = api_get(config, params)
    results = parse_results(xml_text)

    if not results:
        print(f"   Aucun résultat pour « {query} ».")
        return

    cat_label = f" [{category}]" if category and category != "all" else ""
    print(f"🔍 « {query} »{cat_label} — {len(results)} résultat(s) :")
    print()
    for r in results:
        print(f"  📄 {r['title'][:80]}")
        print(f"     {fmt_size(r['size'])}  |  {r['link']}")
        print()


def cmd_download(config, url_or_hash):
    download_path = config.get("download_path", "/home/data/disk1/torrents")
    os.makedirs(download_path, exist_ok=True)

    # If it's a hash (40 hex chars), build the full URL
    if len(url_or_hash) == 40 and all(c in "0123456789abcdefABCDEF" for c in url_or_hash):
        url = f"{config['url'].rstrip('/')}/torrents/{url_or_hash}"
    else:
        url = url_or_hash

    # Build download URL with API key
    parsed = urllib.parse.urlparse(url)
    torrent_id = parsed.path.rstrip("/").split("/")[-1]
    download_url = f"{config['url'].rstrip('/')}/api?apikey={config['api_key']}&t=download&id={torrent_id}"

    print(f"⬇️  Téléchargement : {torrent_id}...")

    req = urllib.request.Request(download_url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; Hermes-C411/1.0)"
    })
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        content = resp.read()

        # Get filename from Content-Disposition header
        filename = None
        cd = resp.getheader("Content-Disposition", "")
        if "filename=" in cd:
            filename = cd.split("filename=")[-1].strip('"').strip("'")

        if not filename:
            filename = f"{torrent_id}.torrent"

        filepath = os.path.join(download_path, filename)
        with open(filepath, "wb") as f:
            f.write(content)

        print(f"✅ Sauvegardé : {filepath} ({fmt_size(len(content))})")
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code}: {e.read().decode()}")


# ─── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="C411 CLI — recherche et téléchargement")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("search", help="Rechercher des torrents")
    p.add_argument("query")
    p.add_argument("--cat", choices=list(CATEGORIES.keys()), default="all", help="Catégorie")
    p.add_argument("--limit", type=int, default=10, help="Nombre de résultats")

    d = sub.add_parser("download", help="Télécharger un .torrent (URL ou hash)")
    d.add_argument("url_or_hash", help="URL complète ou hash de 40 caractères")

    args = parser.parse_args()
    config = load_config()

    if args.command == "search":
        cmd_search(config, args.query, getattr(args, "cat", "all"), args.limit)
    elif args.command == "download":
        cmd_download(config, args.url_or_hash)


if __name__ == "__main__":
    main()