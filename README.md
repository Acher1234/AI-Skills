# 🧰 Hermes Scripts

> Collection de scripts CLI (shell / python / node) qu'Hermes Agent utilise sur hermes.
> Chaque commande a son propre dossier avec un README dédié et un fichier de dépendances.

## 📁 Structure

```
hermes-script/
├── README.md               ← Ce fichier
├── SKILL.md                ← Prompt d’install Cursor / Hermes (défaut)
├── SKILL_TEMPLATE.md       ← Guide pour créer un nouveau skill
├── AI-PRO-SKILLS/          ← Submodule (coolify, zscaler, agent-browser, sf, google-workspace, powerpoint, …)
├── pc-daily-report/
├── tuya-skill/
├── qbittorrent-scripts/
├── c411-torrent/
└── …
```

> **Cursor :** colle le [prompt d’installation](#-prompt-dinstallation-cursor-ou-hermes) dans Agent, ou suis [`SKILL.md`](SKILL.md). Cibles : `~/.cursor/skills`, `~/.hermes/skills`, ou `$HERMES_HOME/skills`.

## 🔒 Sécurité — hooks git

Un hook `pre-commit` (dans `.githooks/`) lance **gitleaks** pour empêcher qu'une clé ou un token soit commité par erreur. Active-le une fois après le clone :

```bash
./setup.sh
```

> `git` n'applique pas `core.hooksPath` automatiquement au clone (sécurité), d'où cette étape unique. `setup.sh` fait `git config core.hooksPath .githooks` et vérifie que `gitleaks` est installé.

Détails et installation de `gitleaks` : voir [`dependencies.md`](dependencies.md).

## 📋 Commandes actuelles

| Commande | Description | Langage |
|----------|------------|---------|
| `pc-daily-report` | Rapport monitoring CPU/RAM/disk, livré tous les matins à 7h | bash |
| `qbittorrent` | CLI gestion de torrents via l'API WebUI qBittorrent | python |
| `tuya-skill` | CLI Tuya IoT (cloud + LAN) | python |
| `c411-torrent` | Recherche / download torrents C411 (Torznab) | python |

## 🪄 Prompt d’installation (Cursor ou Hermes)

Colle ce prompt dans un chat **Agent** (Cursor ou Hermes). Le skill racine [`SKILL.md`](SKILL.md) (`/ai-skills`) contient le **même** flux.

> L’IA doit demander : **1)** Cursor / Hermes / both → **2)** si Hermes : tous les profils vs ce profil → **3)** quels skills (racine + submodule `AI-PRO-SKILLS`).

| Cible | Dossier d’install |
|-------|-------------------|
| Cursor | `~/.cursor/skills/<skill>/SKILL.md` |
| Hermes — tous les profils | `~/.hermes/skills/<skill>/SKILL.md` |
| Hermes — ce profil | `${HERMES_HOME}/skills/<skill>/SKILL.md` |

```
Take the project at url: https://github.com/Acher1234/AI-Skills.git
Install it under ~ as .ai-skills (pull + submodule update if it already exists).

Ask: Cursor vs Hermes vs both.
If Hermes: all profiles (~/.hermes/skills) vs this profile ($HERMES_HOME/skills).
List every skill (root + AI-PRO-SKILLS submodule: coolify, zscaler, agent-browser, sf, google-workspace, powerpoint) and ask which to install.
Copy only chosen skills (+ always ai-skills) into each selected destination.
For google-workspace / powerpoint: copy the full folder; Hermes → productivity/<skill>/.
For sf: copy meta-skill only; then run /sf to sync forcedotcom/sf-skills (list by theme).
```

| Étape | Action |
|-------|--------|
| 1 | Clone / pull `~/.ai-skills` + submodule |
| 2 | Demander **Cursor / Hermes / both** |
| 3 | Si Hermes : **all** (`~/.hermes/skills`) ou **ce profil** (`$HERMES_HOME/skills`) |
| 4 | Lister skills et demander lesquels |
| 5 | Copier vers le(s) dossier(s) choisi(s) |
| 6 | Recharger Cursor et/ou Hermes |

Repo : [github.com/Acher1234/AI-Skills](https://github.com/Acher1234/AI-Skills.git)

## 📂 Working directory des skills

Chaque `SKILL.md` indique le répertoire d’exécution sous **`~/.ai-skills/`** :

```
~/.ai-skills/<skill-dir>
```

| Skill | Working directory |
|-------|-------------------|
| `c411-torrent` | `~/.ai-skills/c411-torrent` |
| `qbittorrent` | `~/.ai-skills/qbittorrent-scripts` |
| `tuya` | `~/.ai-skills/tuya-skill` |
| `pc-daily-report` | `~/.ai-skills/pc-daily-report` |
| `coolify` | `~/.ai-skills/AI-PRO-SKILLS/coolify` |
| `zscaler` | `~/.ai-skills/AI-PRO-SKILLS/zscaler` |
| `agent-browser` | `~/.ai-skills/AI-PRO-SKILLS/agent-browser` |
| `sf` | meta: `~/.ai-skills/AI-PRO-SKILLS/SF` · SF trees: `~/.ai-skills/sf-skills/skills/{skills_dir}` |
| `google-workspace` | `~/.ai-skills/AI-PRO-SKILLS/google-workspace` |
| `powerpoint` | `~/.ai-skills/AI-PRO-SKILLS/powerpoint` |

L’agent doit `cd` dans ce chemin avant d’exécuter les commandes CLI du skill.

## 🧩 Créer un nouveau skill

Voir **[`SKILL_TEMPLATE.md`](SKILL_TEMPLATE.md)** pour le guide complet (structure, `SKILL.md`, slash `/{skill}_{command}`, conventions, sécurité).

## 🎯 Enregistrer les skills (Cursor / Hermes)

Les `SKILL.md` sources sont dans `~/.ai-skills`. Selon la cible choisie :

| Cible | Destination |
|-------|-------------|
| Cursor | `~/.cursor/skills/<skill>/SKILL.md` |
| Hermes all | `~/.hermes/skills/<skill>/SKILL.md` |
| Hermes profile | `$HERMES_HOME/skills/<skill>/SKILL.md` |

Utilise le **[prompt d’installation](#-prompt-dinstallation-cursor-ou-hermes)** ou `/ai-skills`.

| Skill | Source sous `~/.ai-skills/` |
|-------|----------------------------|
| `ai-skills` | `SKILL.md` |
| `c411-torrent` | `c411-torrent/SKILL.md` |
| `qbittorrent` | `qbittorrent-scripts/SKILL.md` |
| `tuya` | `tuya-skill/SKILL.md` |
| `pc-daily-report` | `pc-daily-report/SKILL.md` |
| `coolify` | `AI-PRO-SKILLS/coolify/SKILL.md` |
| `zscaler` | `AI-PRO-SKILLS/zscaler/SKILL.md` |
| `agent-browser` | `AI-PRO-SKILLS/agent-browser/SKILL.md` (+ `npm i -g agent-browser`) |
| `sf` | `AI-PRO-SKILLS/SF/SKILL.md` (puis `/sf` → `~/.ai-skills/sf-skills`, listing **par thème**) |
| `google-workspace` | `AI-PRO-SKILLS/google-workspace/` (full tree → Cursor flat / Hermes `productivity/`) |
| `powerpoint` | `AI-PRO-SKILLS/powerpoint/` (full tree → Cursor flat / Hermes `productivity/`) |

Puis recharger Cursor et/ou Hermes. Détail : **[`SKILL.md`](SKILL.md)**.

## 🚀 Utilisation

Chaque sous-projet contient :
- Un **SKILL.md** (EN) — agent skill + actions `/{skill-name}_{command}`
- Un **README.md** (EN) et un **README.fr.md** / **README-FR.md** (FR)
- Un **dependencies.md** listant les dépendances système requises
- Un **config.example.json** template (les vrais secrets sont gitignorés)
- Le **script** exécutable

Les scripts sont conçus pour être appelés :
- Via Cursor Agent : `/skill-name` puis l’action documentée (ex. `/qbittorrent` → `/qbittorrent_list`)
- Manuellement en CLI
- Via un cron job Hermes (`cronjob` action)
- Ou directement en shell

> **Important :** copier les `SKILL.md` vers Cursor et/ou Hermes selon le choix (voir le [prompt d’installation](#-prompt-dinstallation-cursor-ou-hermes)).

Voir **[`SKILL_TEMPLATE.md`](SKILL_TEMPLATE.md)** et **[`SKILL.md`](SKILL.md)** pour la convention complète.

---

*Mis à jour par Hermes Agent — chaque nouvelle commande atterrit ici.*
