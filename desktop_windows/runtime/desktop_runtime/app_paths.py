"""Runtime and bundled-resource path helpers for DataDiagnostics."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


APP_DIR_NAME = "DataDiagnostics"
INSTALL_DIR_ENV = "DATADIAGNOSTICS_INSTALL_DIR"
USER_DATA_DIR_ENV = "DATADIAGNOSTICS_USER_DATA_DIR"
PROJECT_ROOT_ENV = "DATADIAGNOSTICS_PROJECT_ROOT"

_RUNTIME_TOP_LEVELS = {"configs", "data", "outputs"}
_RUNTIME_DIRS = (
    "data",
    "data/raw_excel",
    "data/raw_dcs",
    "data/processed",
    "data/samples",
    "data/demo",
    "outputs",
    "outputs/models",
    "outputs/reports",
    "outputs/logs",
    "outputs/figures",
    "configs",
)

_INITIALIZED = False


def _desktop_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _project_root() -> Path:
    override = os.environ.get(PROJECT_ROOT_ENV)
    if override:
        return Path(override).expanduser().resolve()
    if _is_frozen():
        return get_bundle_dir()
    return _desktop_root().parent


def _as_relative(path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return Path(*p.parts) if p.parts else Path(".")


def _first_part(path: str | Path) -> str:
    p = Path(path)
    return p.parts[0] if p.parts else ""


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def get_install_dir() -> Path:
    """Return the application install directory, or project root in development."""
    override = os.environ.get(INSTALL_DIR_ENV)
    if override:
        return Path(override).expanduser().resolve()
    if _is_frozen():
        return Path(sys.executable).resolve().parent
    return _project_root()


def get_bundle_dir() -> Path:
    """Return the PyInstaller resource directory, or install dir in development."""
    override = os.environ.get(INSTALL_DIR_ENV)
    if override:
        return Path(override).expanduser().resolve()
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass).resolve()
    return _desktop_root()


def get_user_data_dir() -> Path:
    """Return the per-user writable data directory."""
    override = os.environ.get(USER_DATA_DIR_ENV)
    if override:
        return Path(override).expanduser().resolve()

    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / APP_DIR_NAME
        return Path.home() / "AppData" / "Local" / APP_DIR_NAME

    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / APP_DIR_NAME


def _resource_roots() -> list[Path]:
    roots: list[Path] = []
    for root in (get_bundle_dir(), _desktop_root(), _project_root(), get_install_dir()):
        if root not in roots:
            roots.append(root)
    return roots


def get_resource_path(relative_path: str | Path = ".") -> Path:
    """Resolve a read-only bundled resource path."""
    rel = _as_relative(relative_path)
    if rel.is_absolute():
        return rel
    for root in _resource_roots():
        candidate = root / rel
        if candidate.exists():
            return candidate
    return _resource_roots()[0] / rel


def initialize_user_data(force: bool = False) -> Path:
    """Create the writable runtime tree and copy default configs on first run."""
    global _INITIALIZED
    user_dir = get_user_data_dir()
    if _INITIALIZED and not force:
        return user_dir

    for relative in _RUNTIME_DIRS:
        (user_dir / relative).mkdir(parents=True, exist_ok=True)

    _copy_default_configs(user_dir)
    _INITIALIZED = True
    return user_dir


def _copy_default_configs(user_dir: Path) -> None:
    source_dir = get_resource_path("configs")
    target_dir = user_dir / "configs"
    if not source_dir.exists():
        return

    for source in source_dir.rglob("*"):
        if not source.is_file():
            continue
        relative = source.relative_to(source_dir)
        target = target_dir / relative
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def resolve_path(path: str | Path, *, for_write: bool = False) -> Path:
    """Resolve app paths across development, PyInstaller, and user data modes."""
    p = Path(path)
    if p.is_absolute():
        return p

    first = _first_part(p)
    if for_write and first in _RUNTIME_TOP_LEVELS:
        return initialize_user_data() / p

    if first in _RUNTIME_TOP_LEVELS:
        user_candidate = initialize_user_data() / p
        if user_candidate.exists():
            return user_candidate
        resource_candidate = get_resource_path(p)
        if resource_candidate.exists():
            return resource_candidate
        return user_candidate

    return get_resource_path(p)


def ensure_directory(path: str | Path) -> Path:
    """Resolve a writable directory and create it."""
    directory = resolve_path(path, for_write=True)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def display_path(path: str | Path) -> str:
    """Return a short, UI-friendly path label."""
    p = Path(path)
    for prefix, label in (
        (get_user_data_dir(), "user-data"),
        (get_install_dir(), "install"),
        (get_bundle_dir(), "bundle"),
    ):
        try:
            return f"{label}/{p.resolve().relative_to(prefix.resolve()).as_posix()}"
        except ValueError:
            continue
    return p.name if p.name else str(p)
