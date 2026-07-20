"""Shared library vs per-workspace credentials for AI-SKILLS.

**Library (shared):** ``~/.ai-skills/<skill>/`` — CLI, action modules, deps.
**Credentials (not shared):** next to the *registered* skill / workspace so each
Cursor project or Hermes profile can use different accounts.

Usage from a skill folder::

    from pathlib import Path
    import sys

    _LIB = Path(__file__).resolve().parent
    _ROOT = _LIB.parent  # AI-SKILLS root (sibling of common/)
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))

    from common.skill_home import SkillHome

    home = SkillHome("c411-torrent", library_home=_LIB)
    env = home.env_path()
"""

from __future__ import annotations

import os
from pathlib import Path


# Relative skill dirs under a tool root or under cwd
_SKILL_SUBDIRS = (
    ".cursor/skills",
    ".claude/skills",
    ".openclaw/skills",
    ".hermes/skills",
    ".hermes/skills/productivity",
)


class SkillHome:
    """Resolve shared library path + per-workspace credential files for one skill."""

    def __init__(self, name: str, library_home: Path | None = None):
        self.name = name.strip().strip("/")
        if not self.name:
            raise ValueError("skill name required")
        self.library_home = (
            Path(library_home).resolve()
            if library_home is not None
            else Path.cwd().resolve()
        )

    # ------------------------------------------------------------------ library

    def get_library_home(self) -> Path:
        return self.library_home

    def display_library_home(self) -> str:
        return display_path(self.library_home)

    # Back-compat aliases used by existing skills
    def get_skill_home(self) -> Path:
        return self.library_home

    def display_skill_home(self) -> str:
        return self.display_library_home()

    # -------------------------------------------------------------- credentials

    def override_var(self, filename: str = ".env") -> str:
        """Env var that overrides the resolved path for *filename*.

        ``.env`` → ``<NAME>_ENV_PATH``; ``config.json`` → ``<NAME>_CONFIG_PATH``;
        any other file → ``<NAME>_<STEM>_PATH`` (stem upper-cased).
        """
        prefix = self.name.upper().replace("-", "_")
        stem = "ENV" if filename == ".env" else Path(filename).stem.upper().replace("-", "_")
        return f"{prefix}_{stem}_PATH"

    def env_override_var(self) -> str:
        """Back-compat: override var for the ``.env`` file (e.g. c411-torrent → C411_TORRENT_ENV_PATH)."""
        return self.override_var(".env")

    def credential_candidates(self, filename: str = ".env") -> list[Path]:
        """Ordered search paths for a credential file (workspace first)."""
        cwd = Path.cwd()
        home = Path.home()
        hermes = Path(os.environ.get("HERMES_HOME") or (home / ".hermes"))
        name = self.name
        out: list[Path] = []

        def add(base: Path, *parts: str) -> None:
            out.append(base.joinpath(*parts))

        # Project / cwd installs
        for sub in _SKILL_SUBDIRS:
            add(cwd, *sub.split("/"), name, filename)
        if filename == ".env":
            add(cwd, ".env")

        # Global tool installs
        for sub in (
            ".cursor/skills",
            ".claude/skills",
            ".openclaw/skills",
        ):
            add(home, *sub.split("/"), name, filename)

        add(hermes, "skills", name, filename)
        add(hermes, "skills", "productivity", name, filename)

        # Tool-level env (jira-style) — only for .env
        if filename == ".env":
            add(home / ".cursor", ".env")
            add(home / ".claude", ".env")
            add(home / ".openclaw", ".env")
            add(hermes, ".env")

        return out

    def preferred_credential_dir(self) -> Path:
        """Directory where a new credential file should be created."""
        cwd = Path.cwd()
        project = cwd / ".cursor" / "skills" / self.name
        if (cwd / ".cursor").is_dir() or project.is_dir():
            return project
        return Path.home() / ".cursor" / "skills" / self.name

    def preferred_env_path(self) -> Path:
        return self.preferred_credential_dir() / ".env"

    def credential_path(self, filename: str = ".env") -> Path:
        """First existing credential/config file, or preferred create path.

        Works for any *filename* (``.env``, ``config.json``, ``devices.json``, …).
        An env override (``<NAME>_ENV_PATH`` / ``<NAME>_CONFIG_PATH`` / …) wins.
        """
        override = os.environ.get(self.override_var(filename), "").strip()
        if override:
            return Path(override).expanduser().resolve()

        for candidate in self.credential_candidates(filename):
            if candidate.is_file():
                return candidate.resolve()

        return (self.preferred_credential_dir() / filename).resolve()

    def env_path(self) -> Path:
        return self.credential_path(".env")

    def config_path(self, filename: str = "config.json") -> Path:
        """Per-workspace config file (default ``config.json``)."""
        return self.credential_path(filename)

    def file_path(self, filename: str) -> Path:
        """Resolve any per-workspace file (e.g. ``devices.json``) with the same search order."""
        return self.credential_path(filename)

    def display_env_path(self) -> str:
        return display_path(self.env_path())

    def display_config_path(self, filename: str = "config.json") -> str:
        return display_path(self.config_path(filename))

    def display_credential_path(self, filename: str = ".env") -> str:
        return display_path(self.credential_path(filename))


def display_path(path: Path) -> str:
    """Return a user-friendly ``~/``-shortened path."""
    try:
        return "~/" + str(path.resolve().relative_to(Path.home()))
    except ValueError:
        return str(path.resolve())


def make_skill_home(name: str, library_file: str | Path) -> SkillHome:
    """Build a ``SkillHome`` from any file inside the skill library folder."""
    return SkillHome(name, library_home=Path(library_file).resolve().parent)
