<div align="center">

<img src="assets/logo.png" alt="AI-Skills" width="640" />

# AI-Skills

**Une librairie partagée de _skills_ CLI pour agents IA — installables sur Cursor, Claude, Hermes & OpenClaw.**

*by Hermes* · [github.com/Acher1234/AI-Skills](https://github.com/Acher1234/AI-Skills.git)

</div>

---

## 🧭 C'est quoi ?

**AI-Skills** est une collection de _skills_ (scripts CLI shell / python / node) que les agents IA
peuvent utiliser, plus un **méta-installeur** qui les enregistre dans n'importe quel outil.

L'idée clé : **une seule librairie partagée + un seul environnement Python/npm** sur la machine.
On **ne re-clone pas** et on **ne réinstalle pas** les dépendances à chaque projet — le lourd vit
une fois, chaque outil ne reçoit que le `SKILL.md`.

| | |
|---|---|
| 🎯 **Multi-cibles** | Cursor · Claude · Hermes · OpenClaw *(Claude & OpenClaw en cours)* |
| 🌐 **Skills externes** | Installe **n'importe quel** repo git de skill, pas seulement ceux d'ici |
| ♻️ **Env partagé** | Un venv Python (`~/.ai-skills/.venv`) + npm global ; **chaque skill y installe ses propres deps** (une fois, pas par projet) |
| 📦 **Cache partagé** | Repos externes clonés **une fois** dans `~/.ai-skills/ext/` |

## 🏛️ Architecture

Le lourd est mutualisé sous `~/.ai-skills` ; chaque outil ne reçoit que le `SKILL.md`.

```
~/.ai-skills/                       librairie partagée ($AI_SKILLS_HOME)
├── install.sh                      le méta-installeur (piloté par /ai-skills)
├── ext/<repo>/                     skills git externes, clonés UNE FOIS
├── .venv/                          venv Python partagé (tous les skills python)
├── qbittorrent-scripts/ …          skills intégrés
└── AI-PRO-SKILLS/                  submodule pro (coolify, zscaler, sf, jira, …)

npm i -g <pkg>                      CLIs node globaux partagés (agent-browser, …)

        │ on ne copie QUE le SKILL.md vers chaque outil ↓
~/.cursor/skills/<name>/SKILL.md     ~/.claude/skills/<name>/SKILL.md
~/.hermes/skills/<name>/SKILL.md     ~/.openclaw/skills/<name>/SKILL.md
```

Chaque `SKILL.md` pointe vers son working dir sous `~/.ai-skills/…` : l'agent y `cd` et exécute
le code / le venv installé **une seule fois**.

## 🚀 Installation

### 1. Cloner la librairie partagée (une fois)

```bash
git clone --recurse-submodules https://github.com/Acher1234/AI-Skills.git ~/.ai-skills
cd ~/.ai-skills && ./setup.sh          # active le hook pre-commit (gitleaks)
```

### 2. Préparer l'environnement partagé

```bash
cd ~/.ai-skills
./install.sh --help     # rappelle les 3 commandes : fetch, pip init, npm init
```

### 3. Installer des skills

Colle le prompt d'installation dans un chat **Agent**, ou lance `/ai-skills`.
Le flux : **1)** choisir l'outil (Cursor / Claude / Hermes / OpenClaw) → **2)** la portée
(global / projet / profil) → **3)** ce qu'on installe (URL git externe, skill intégré, ou chemin local).

## 🪄 Méta-skills (installeurs)

| Méta-skill | Slash | Rôle |
|-----------|-------|------|
| `ai-skills` | `/ai-skills` | **L'installeur** : installe n'importe quel skill (git externe / intégré / local) sur **Cursor / Claude / Hermes / OpenClaw**, avec env Python/npm **partagé**. Voir [`SKILL.md`](SKILL.md) + [`install.sh`](install.sh). |
| `ai-pro-skills` | `/ai-pro-skills` | Installe les skills **pro** du submodule. Voir [`AI-PRO-SKILLS/SKILL.md`](AI-PRO-SKILLS/SKILL.md). |

### `/ai-skills` — l'installeur

`install.sh` a **3 commandes** : `fetch`, `pip init`, `npm init`. Enregistrer un skill dans un
outil = un simple `cp` du `SKILL.md`.

```bash
cd ~/.ai-skills

# skill git externe → cloné UNE FOIS dans le cache partagé
SRC=$(./install.sh fetch https://github.com/some/cool-skill.git cool-skill)

# enregistrer = cp du SKILL.md vers l'outil (ici Claude global, puis Cursor projet)
mkdir -p ~/.claude/skills/cool-skill && cp "$SRC/SKILL.md" ~/.claude/skills/cool-skill/SKILL.md
mkdir -p ./.cursor/skills/cool-skill && cp "$SRC/SKILL.md" ./.cursor/skills/cool-skill/SKILL.md

# le skill installe SES deps tout seul (1re exécution) dans le venv partagé
./install.sh pip init "$SRC"                    # ou, depuis le dossier du skill : ./install.sh pip init .
```

> L'installeur **ne fait pas** de `pip install` pour toi : `fetch` (clone) + `cp` (register).
> Chaque skill installe **ses propres** dépendances via `pip init` / `npm init`, à son premier run,
> dans le venv partagé (`~/.ai-skills/.venv`) — une fois par machine, réutilisé par tous les projets.

| Cible (`tool` / `scope`) | Dossier d'install |
|--------------------------|-------------------|
| `cursor` / `global` | `~/.cursor/skills/<name>/` |
| `cursor` / `project` | `./.cursor/skills/<name>/` |
| `claude` / `global` | `~/.claude/skills/<name>/` *(WIP)* |
| `claude` / `project` | `./.claude/skills/<name>/` *(WIP)* |
| `hermes` / `all` | `~/.hermes/skills/<name>/` |
| `hermes` / `profile` | `${HERMES_HOME}/skills/<name>/` |
| `openclaw` / `global` | `~/.openclaw/skills/<name>/` *(WIP)* |
| `openclaw` / `project` | `./.openclaw/skills/<name>/` *(WIP)* |

> **Claude** et **OpenClaw** sont **en cours d'implémentation** : les chemins ci-dessus sont les
> valeurs par défaut de [`install.sh`](install.sh) (fonction `target()`) et pourront être ajustés
> quand les conventions de ces outils seront figées.

## 📦 Skills intégrés

**Racine (AI-Skills)**

| Skill | Description | Langage |
|-------|-------------|---------|
| `pc-daily-report` | Rapport monitoring CPU/RAM/disk (livré chaque matin) | bash |
| `qbittorrent` | CLI gestion de torrents via l'API WebUI qBittorrent | python |
| `tuya` | CLI Tuya IoT (cloud + LAN) | python |
| `c411-torrent` | Recherche / download torrents C411 (Torznab) | python |

**Submodule [`AI-PRO-SKILLS/`](AI-PRO-SKILLS/README.md)** (`git submodule update --init --recursive`)

| Skill | Description |
|-------|-------------|
| `coolify` | Coolify : deploy / status / restart |
| `zscaler` | Zscaler ZPA / ZIA / ZIdentity |
| `agent-browser` | Automation navigateur (CLI npm) |
| `sf` | Installe les skills Salesforce ([forcedotcom/sf-skills](https://github.com/forcedotcom/sf-skills.git)) |
| `jira` | Installe **tous** les skills JIRA Assistant + CLI `jira-as` |
| `google-workspace` | Gmail / Calendar / Drive / Docs / Sheets |
| `powerpoint` | Créer / éditer des `.pptx` |

## 🔒 Sécurité — hooks git

Un hook `pre-commit` (`.githooks/`) lance **gitleaks** pour bloquer tout commit contenant une clé ou
un token. Active-le une fois après le clone :

```bash
./setup.sh
```

> `git` n'applique pas `core.hooksPath` automatiquement au clone (sécurité), d'où cette étape unique.
> `setup.sh` fait `git config core.hooksPath .githooks` et vérifie que `gitleaks` est installé.
> Détails : [`dependencies.md`](dependencies.md).

Les secrets vivent dans le `.env` de l'outil (`~/.cursor/.env`, `~/.claude/.env`, `$HERMES_HOME/.env`,
`~/.openclaw/.env`) — **jamais** dans un skill.

## 🧩 Créer un nouveau skill

Voir **[`SKILL_TEMPLATE.md`](SKILL_TEMPLATE.md)** (structure, `SKILL.md`, slash `/{skill}_{command}`,
conventions, sécurité). Chaque sous-projet contient :

- un **`SKILL.md`** (EN) — agent skill + actions `/{skill}_{command}` ;
- un **`README.md`** / **`README.fr.md`** ;
- un **`dependencies.md`** ;
- un **`config.example.json`** (les vrais secrets sont gitignorés) ;
- le **script** exécutable.

Un skill Python doit cibler l'interpréteur **partagé** `~/.ai-skills/.venv/bin/python` plutôt qu'un
venv par projet.

---

*Maintenu par Hermes Agent — chaque nouveau skill atterrit ici et s'installe via `/ai-skills`.*
