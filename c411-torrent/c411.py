#!/usr/bin/env python3
"""
C411 CLI — recherche de torrents via l'API C411 (Torznab).

Usage:
  ./c411.py search <query> [--cat CAT] [--limit N]
  ./c411.py search tv <query> [--limit N]
  ./c411.py search movie <query> [--limit N]
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

NS = {"torznab": "http://torznab.com/schemas/2015/feed"}


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
    """Parse les résultats XML Torznab en objets simples."""
    root = ET.fromstring(xml_text)
    results = []
    for item in root.findall(".//item"):
        title = item.findtext("title", "")
        size = item.findtext("size", "0")
        guid = item.findtext("guid", "")
        pubdate = item.findtext("pubDate", "")
        link_el = item.find("link")
        link = link_el.text if link_el is not None else ""

        # Extra category
        cats = item.findall("category")
        category = cats[0].text if cats else "inconnu"

        results.append({
            "title": title,
            "size": int(size),
            "link": link,
            "pubdate": pubdate,
            "category": category,
            "guid": guid,
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

    print(f"🔍 Résultats pour « {query} » ({len(results)}):")
    print()
    for r in results:
        print(f"  📄 {r['title'][:80]}")
        print(f"     Taille : {fmt_size(r['size'])}  |  Catégorie : {r['category']}")
        if r["link"]:
            print(f"     Lien   : {r['link'][:80]}")
        print()


def cmd_search_tv(config, query, limit):
    params = {
        "apikey": config["api_key"],
        "t": "tvsearch",
        "q": query,
        "limit": str(limit),
    }
    xml_text = api_get(config, params)
    results = parse_results(xml_text)

    if not results:
        print(f"   Aucun résultat TV pour « {query} ».")
        return

    print(f"📺 TV « {query} » ({len(results)}):")
    print()
    for r in results:
        print(f"  📄 {r['title'][:80]}")
        print(f"     Taille : {fmt_size(r['size'])}")
        if r["link"]:
            print(f"     Lien   : {r['link'][:80]}")
        print()


def cmd_search_movie(config, query, limit):
    params = {
        "apikey": config["api_key"],
        "t": "movie",
        "q": query,
        "limit": str(limit),
    }
    xml_text = api_get(config, params)
    results = parse_results(xml_text)

    if not results:
        print(f"   Aucun résultat Movie pour « {query} ».")
        return

    print(f"🎬 Films « {query} » ({len(results)}):")
    print()
    for r in results:
        print(f"  📄 {r['title'][:80]}")
        print(f"     Taille : {fmt_size(r['size'])}")
        if r["link"]:
            print(f"     Lien   : {r['link'][:80]}")
        print()


# ─── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="C411 CLI — recherche de torrents")
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="Recherche générale")
    p_search.add_argument("query")
    p_search.add_argument("--cat", choices=list(CATEGORIES.keys()), default="all")
    p_search.add_argument("--limit", type=int, default=10)

    p_tv = sub.add_parser("tv", help="Recherche TV")
    p_tv.add_argument("query")
    p_tv.add_argument("--limit", type=int, default=10)

    p_movie = sub.add_parser("movie", help="Recherche Film")
    p_movie.add_argument("query")
    p_movie.add_argument("--limit", type=int, default=10)

    args = parser.parse_args()
    config = load_config()

    if args.command == "search":
        cmd_search(config, args.query, getattr(args, "cat", "all"), args.limit)
    elif args.command == "tv":
        cmd_search_tv(config, args.query, args.limit)
    elif args.command == "movie":
        cmd_search_movie(config, args.query, args.limit)


if __name__ == "__main__":
    main()