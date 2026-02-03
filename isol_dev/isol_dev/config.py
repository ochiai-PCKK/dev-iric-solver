from __future__ import annotations

from pathlib import Path
import tomllib

DEFAULT_CONFIG_NAME = "isol_dev.toml"


def resolve_config_path(value: str | None) -> Path:
    if value:
        return Path(value)
    return Path.cwd() / DEFAULT_CONFIG_NAME


def load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def get_section(cfg: dict, name: str) -> dict:
    section = cfg.get(name)
    return section if isinstance(section, dict) else {}
