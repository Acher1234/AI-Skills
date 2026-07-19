#!/usr/bin/env bash
#
# AI-Skills — minimal shared-env helper. THREE commands only:
#
#   install.sh fetch <git-url> [name]   clone/pull an external skill repo into the shared cache
#   install.sh pip init [dir]           create/reuse the shared Python venv, install <dir> deps into it
#   install.sh npm init [dir]           install <dir> node deps (shared skill dir)
#
# Everything is SHARED once per machine — nothing is re-cloned or re-installed per project:
#
#   ~/.ai-skills/            shared library root ($AI_SKILLS_HOME)
#   ~/.ai-skills/ext/<name>  external skill repos, cloned ONCE (fetch)
#   ~/.ai-skills/.venv       shared Python venv (pip init)
#
# The installer NEVER bulk-installs dependencies. Each skill calls `pip init` /
# `npm init` for ITS OWN deps, on first run, into the shared env.
#
# Registering a skill into a tool is a plain copy (see the copy map in SKILL.md):
#   cp <src>/SKILL.md ~/.cursor/skills/<name>/SKILL.md   (or .claude / .hermes / .openclaw)
#
set -euo pipefail

AI_SKILLS_HOME="${AI_SKILLS_HOME:-$HOME/.ai-skills}"
EXT_DIR="$AI_SKILLS_HOME/ext"
VENV_DIR="$AI_SKILLS_HOME/.venv"

log() { printf '\033[1;36m[ai-skills]\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m[ai-skills] error:\033[0m %s\n' "$*" >&2; }

# fetch <git-url> [name] — clone ONCE into the shared cache, else pull to update.
fetch_repo() {
  local url="${1:?git url required}" name="${2:-}"
  [ -n "$name" ] || name="$(basename "${url%.git}")"
  local dest="$EXT_DIR/$name"
  mkdir -p "$EXT_DIR"
  if [ -d "$dest/.git" ]; then
    log "Updating '$name' (git pull) in shared cache"
    git -C "$dest" pull --ff-only || log "pull failed for $name (keeping existing copy)"
  else
    log "Cloning '$name' → $dest"
    git clone --depth 1 "$url" "$dest"
  fi
  echo "$dest"
}

# pip init [dir] — ensure the shared venv, then install <dir>'s deps into it.
pip_init() {
  local dir="${1:-.}"
  if [ ! -x "$VENV_DIR/bin/python" ]; then
    log "Creating shared Python venv at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip
  fi
  if [ -f "$dir/requirements.txt" ]; then
    log "Installing $dir/requirements.txt into shared venv"
    "$VENV_DIR/bin/pip" install -r "$dir/requirements.txt"
  elif [ -f "$dir/pyproject.toml" ] || [ -f "$dir/setup.py" ]; then
    log "Installing $dir (editable) into shared venv"
    "$VENV_DIR/bin/pip" install -e "$dir"
  else
    log "Shared venv ready ($VENV_DIR) — no requirements found in $dir"
  fi
  log "Shared interpreter: $VENV_DIR/bin/python"
}

# npm init [dir] — install <dir>'s node deps (the skill dir is shared).
npm_init() {
  local dir="${1:-.}"
  command -v npm >/dev/null 2>&1 || { err "npm not found on PATH"; return 1; }
  if [ -f "$dir/package.json" ]; then
    log "npm install in $dir (shared skill dir)"
    ( cd "$dir" && npm install )
  else
    err "no package.json in $dir"; return 1
  fi
}

usage() { sed -n '2,/^set -euo pipefail/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'; }

cmd="${1:-}"; shift || true
case "$cmd" in
  fetch) fetch_repo "$@" ;;
  pip)
    if [ "${1:-}" = init ]; then shift; pip_init "$@"; else err "usage: install.sh pip init [dir]"; exit 2; fi ;;
  npm)
    if [ "${1:-}" = init ]; then shift; npm_init "$@"; else err "usage: install.sh npm init [dir]"; exit 2; fi ;;
  ""|-h|--help|help) usage ;;
  *) err "unknown command: $cmd"; echo; usage; exit 2 ;;
esac
