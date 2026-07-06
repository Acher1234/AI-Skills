#!/usr/bin/env python3
"""
Coolify CLI — interroge l'état des déploiements sur une ou plusieurs instances Coolify.

Usage:
  ./coolify.py instances                          # Liste les instances configurées
  ./coolify.py projects <instance>                # Liste tous les projets
  ./coolify.py apps <instance> <projet>           # Liste les apps d'un projet
  ./coolify.py discover <instance> <projet>       # Découvre les apps and update config
  ./coolify.py status <instance> <app_name>       # État actuel d'une app
  ./coolify.py deployments <instance> <app_name>  # Derniers déploiements (5 par défaut)
  ./coolify.py deployments <instance> <app_name> -n 10  # 10 derniers déploiements
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone


# ─── Config ────────────────────────────────────────────────────────────────

CONFIG_PATH = os.environ.get(
    "COOLIFY_CONFIG_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"),
)


def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"❌ Fichier config introuvable : {CONFIG_PATH}")
        print(f"   Copiez config.example.json → config.json et remplissez vos données.")
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


def get_instances(data):
    return {inst["name"]: inst for inst in data.get("instances", [])}


def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    print(f"   ✅ Config mise à jour : {CONFIG_PATH}")


def resolve_instance(data, instance_name=None):
    """Trouve une instance par nom, ou prend l'unique si un seul existant."""
    instances = get_instances(data)
    if instance_name:
        inst = instances.get(instance_name)
        if not inst:
            print(f"❌ Instance '{instance_name}' inconnue.")
            print(f"   Disponibles : {', '.join(instances.keys())}")
            sys.exit(1)
        return inst
    if len(instances) == 1:
        return list(instances.values())[0]
    if len(instances) == 0:
        print("❌ Aucune instance configurée.")
        sys.exit(1)
    print(f"❌ Plusieurs instances disponibles, précisez-en une : {', '.join(instances.keys())}")
    sys.exit(1)


def find_project_uuid(inst, name_or_uuid):
    """Cherche un projet par nom ou UUID, retourne son UUID."""
    projects = api_get(inst, "/projects")
    for p in projects:
        if p["uuid"] == name_or_uuid or p["name"] == name_or_uuid:
            return p["uuid"], p["name"]
    print(f"❌ Projet '{name_or_uuid}' introuvable.")
    print(f"   Utilisez « projects {inst['name']} » pour lister les projets.")
    sys.exit(1)


# ─── API ───────────────────────────────────────────────────────────────────

def api_get(instance, path, optional=False):
    url = f"{instance['url'].rstrip('/')}/api/v1{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {instance['token']}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if optional and e.code == 404:
            return None
        body = e.read().decode()
        print(f"❌ HTTP {e.code} sur {url}")
        if body:
            try:
                detail = json.loads(body)
                print(f"   {json.dumps(detail, indent=2)}")
            except json.JSONDecodeError:
                print(f"   {body}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ Erreur réseau : {e.reason}")
        sys.exit(1)


def get_all_applications(inst, project_uuid):
    """Récupère toutes les applications d'un projet (parcourt ses environnements)."""
    project = api_get(inst, f"/projects/{project_uuid}")
    apps = []
    for env in project.get("environments", []):
        env_uuid = env["uuid"]
        env_apps = api_get(inst, f"/applications?environment_uuid={env_uuid}", optional=True)
        if env_apps:
            if isinstance(env_apps, list):
                apps.extend(env_apps)
            elif isinstance(env_apps, dict):
                apps.append(env_apps)
    return apps


# ─── Formatters ────────────────────────────────────────────────────────────

def fmt_time(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return iso_str or "-"


def fmt_status(status):
    icons = {
        "success": "✅",
        "failed": "❌",
        "running": "🔄",
        "queued": "⏳",
        "cancelled": "🚫",
        "in_progress": "🔄",
    }
    icon = icons.get(status.lower(), "❓") if status else "❓"
    return f"{icon} {status or 'inconnu'}"


def fmt_duration(start, end):
    if not start or not end:
        return "-"
    try:
        s = datetime.fromisoformat(start.replace("Z", "+00:00"))
        e = datetime.fromisoformat(end.replace("Z", "+00:00"))
        secs = int((e - s).total_seconds())
        if secs < 60:
            return f"{secs}s"
        return f"{secs // 60}m {secs % 60}s"
    except Exception:
        return "-"


# ─── Commands ──────────────────────────────────────────────────────────────

def cmd_instances(data):
    """Liste les instances Coolify configurées"""
    instances = get_instances(data)
    if not instances:
        print("Aucune instance configurée.")
        return
    for name, inst in instances.items():
        app_count = len(inst.get("applications", {}))
        apps_list = ", ".join(inst.get("applications", {}).keys()) or "aucune"
        print(f"  📦 {name}")
        print(f"     URL      : {inst['url']}")
        print(f"     Apps     : {app_count} — {apps_list}")
        print()


def cmd_projects(data, instance_name):
    """Liste tous les projets d'une instance"""
    inst = resolve_instance(data, instance_name)
    projects = api_get(inst, "/projects")

    if not projects:
        print("   Aucun projet trouvé.")
        return

    inst_name = inst["name"]
    print(f"📁 Projets sur « {inst_name} »")
    print()
    for p in projects:
        envs = p.get("environments", [])
        print(f"  📂 {p['name']}")
        print(f"     UUID     : {p['uuid']}")
        print(f"     Envs     : {len(envs)}")
        for env in envs:
            print(f"       • {env['name']} ({env['uuid']})")
        print()


def cmd_apps(data, instance_name, project_ref):
    """Liste toutes les applications d'un projet"""
    inst = resolve_instance(data, instance_name)
    inst_name = inst["name"]
    project_uuid, project_name = find_project_uuid(inst, project_ref)
    apps = get_all_applications(inst, project_uuid)

    if not apps:
        print(f"   Aucune application trouvée dans « {project_name} ».")
        return

    print(f"📱 Applications de « {project_name} » sur « {inst_name} »")
    print()
    for a in apps:
        print(f"  • {a.get('name', '-')}")
        print(f"    UUID     : {a.get('uuid', '-')}")
        print(f"    Status   : {fmt_status(a.get('status', 'unknown'))}")
        print(f"    Type     : {a.get('build_pack', '-')}")
        print()


def cmd_discover(data, instance_name, project_ref):
    """Découvre les applications d'un projet et met à jour la config"""
    inst = resolve_instance(data, instance_name)
    inst_name = inst["name"]
    project_uuid, project_name = find_project_uuid(inst, project_ref)
    apps = get_all_applications(inst, project_uuid)

    if not apps:
        print(f"   Aucune application trouvée dans « {project_name} ».")
        return

    print(f"🔍 Découverte des apps de « {project_name} » sur « {inst_name} »")
    print()

    # Build new apps dict
    new_apps = {}
    for a in apps:
        name = a.get("name", "").strip()
        uuid = a.get("uuid", "")
        # Make a safe key name
        key = name.lower().replace(" ", "-").replace("_", "-")
        new_apps[key] = uuid
        print(f"  ✅ {name} → {key} : {uuid}")

    # Update config
    for inst_cfg in data["instances"]:
        if inst_cfg["name"] == instance_name:
            existing = inst_cfg.get("applications", {})
            merged = {**existing, **new_apps}
            inst_cfg["applications"] = merged
            save_config(data)
            print()
            print(f"   {len(new_apps)} app(s) ajoutée(s)/mise(s) à jour dans la config.")
            print(f"   Total : {len(merged)} app(s) configurée(s).")
            return

    print("❌ Instance non trouvée dans la config (inattendu).")


def cmd_status(data, instance_name, app_name):
    """Statut actuel d'une application"""
    inst = resolve_instance(data, instance_name)
    app_uuid = inst.get("applications", {}).get(app_name)
    if not app_uuid:
        print(f"❌ App '{app_name}' inconnue sur '{instance_name}'.")
        print(f"   Disponibles : {', '.join(inst.get('applications', {}).keys())}")
        return

    inst_name = inst["name"]
    print(f"📊 Statut de « {app_name} » sur « {inst_name} »")
    print(f"   UUID : {app_uuid}")
    print()

    app = api_get(inst, f"/applications/{app_uuid}")
    deploys = api_get(inst, f"/applications/{app_uuid}/deployments?per_page=5", optional=True)
    if deploys is None:
        deploys = api_get(inst, f"/deployments?per_page=5&application_uuid={app_uuid}", optional=True)
    if deploys is None:
        deploys = []

    print(f"   🔤 Nom          : {app.get('name', '-')}")
    print(f"   🌐 Domaine      : {app.get('fqdn', '-')}")
    print(f"   📦 Type         : {app.get('build_pack', '-')}")
    print(f"   📍 Statut       : {fmt_status(app.get('status', 'unknown'))}")
    print(f"   🕐 Créée le     : {fmt_time(app.get('created_at'))}")
    print()

    if deploys:
        last = deploys[0]
        print(f"   🔄 Dernier déploiement :")
        print(f"      Commit       : {last.get('commit', '-')[:12] or '-'}")
        print(f"      Statut       : {fmt_status(last.get('status', 'unknown'))}")
        print(f"      Début        : {fmt_time(last.get('created_at'))}")
        print(f"      Fin          : {fmt_time(last.get('finished_at'))}")
        print(f"      Durée        : {fmt_duration(last.get('created_at'), last.get('finished_at'))}")
    else:
        print("   Aucun déploiement trouvé.")
    print()


def cmd_deployments(data, instance_name, app_name, count):
    """Liste les N derniers déploiements d'une application"""
    inst = resolve_instance(data, instance_name)
    app_uuid = inst.get("applications", {}).get(app_name)
    if not app_uuid:
        print(f"❌ App '{app_name}' inconnue sur '{instance_name}'.")
        print(f"   Disponibles : {', '.join(inst.get('applications', {}).keys())}")
        return

    deploys = api_get(inst, f"/applications/{app_uuid}/deployments?per_page={count}", optional=True)
    if deploys is None:
        deploys = api_get(inst, f"/deployments?per_page={count}&application_uuid={app_uuid}", optional=True)
    if deploys is None:
        deploys = []

    if not deploys:
        print("   Aucun déploiement trouvé.")
        return

    inst_name = inst["name"]
    print(f"📋 Derniers {len(deploys)} déploiements de « {app_name} » sur « {inst_name} »")
    print()

    for d in deploys:
        commit = (d.get("commit") or "?")[:12]
        print(f"  {fmt_status(d.get('status', ''))}  "
              f"Commit: {commit}  "
              f"| {fmt_time(d.get('created_at'))}  "
              f"| Durée: {fmt_duration(d.get('created_at'), d.get('finished_at'))}")
        print(f"     ID: {d.get('deployment_uuid', '-')}")
        print()


# ─── CLI ───────────────────────────────────────────────────────────────────

def main():
    data = load_config()

    parser = argparse.ArgumentParser(description="Coolify CLI — statut des déploiements")
    sub = parser.add_subparsers(dest="command", required=True)

    # instances
    sub.add_parser("instances", help="Liste les instances Coolify configurées")

    # projects
    p_projects = sub.add_parser("projects", help="Liste tous les projets")
    p_projects.add_argument("instance", nargs="?", default=None, help="Nom de l'instance (optionnel si une seule)")

    # apps
    p_apps = sub.add_parser("apps", help="Liste les applications d'un projet")
    p_apps.add_argument("project", help="Nom ou UUID du projet")
    p_apps.add_argument("instance", nargs="?", default=None, help="Nom de l'instance (optionnel si une seule)")

    # discover
    p_disc = sub.add_parser("discover", help="Découvre les apps d'un projet and update config")
    p_disc.add_argument("project", help="Nom ou UUID du projet")
    p_disc.add_argument("instance", nargs="?", default=None, help="Nom de l'instance (optionnel si une seule)")

    # status
    p_status = sub.add_parser("status", help="Statut actuel d'une application")
    p_status.add_argument("app", help="Nom de l'application (clé dans la config)")
    p_status.add_argument("instance", nargs="?", default=None, help="Nom de l'instance (optionnel si une seule)")

    # deployments
    p_deploy = sub.add_parser("deployments", help="Derniers déploiements d'une application")
    p_deploy.add_argument("app", help="Nom de l'application")
    p_deploy.add_argument("instance", nargs="?", default=None, help="Nom de l'instance (optionnel si une seule)")
    p_deploy.add_argument("-n", "--count", type=int, default=5, help="Nombre de déploiements (défaut: 5)")

    args = parser.parse_args()

    if args.command == "instances":
        cmd_instances(data)
    elif args.command == "projects":
        cmd_projects(data, args.instance)
    elif args.command == "apps":
        cmd_apps(data, args.instance, args.project)
    elif args.command == "discover":
        cmd_discover(data, args.instance, args.project)
    elif args.command == "status":
        cmd_status(data, args.instance, args.app)
    elif args.command == "deployments":
        cmd_deployments(data, args.instance, args.app, args.count)


if __name__ == "__main__":
    main()
