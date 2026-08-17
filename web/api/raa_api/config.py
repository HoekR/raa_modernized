from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

CORPUS_DATES = "1428–1861"

# Official RAA sub-period boundaries (inleiding / Huygens RAA).
PERIOD_DEFINITIONS: list[tuple[str, str, str]] = [
    ("me", "Middeleeuwen", "1428–1588"),
    ("republiek", "Republiek", "1588–1795"),
    ("batfra", "Bataafs-Franse tijd", "1795–1813"),
    ("negentiende_eeuw", "Negentiende eeuw", "1813–1861"),
]

PERIODS = [(key, f"{label} ({dates})") for key, label, dates in PERIOD_DEFINITIONS]
ALL_PERIODS_LABEL = f"Alle perioden ({CORPUS_DATES})"

_CONFIG_ROOT = Path(__file__).resolve().parents[3]
_CONFIG_FILE = _CONFIG_ROOT / "config.local.toml"


def _load_toml() -> dict:
    if not _CONFIG_FILE.exists():
        return {}
    try:
        import tomllib

        return tomllib.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


@dataclass(frozen=True)
class EditorialSettings:
    enabled: bool
    api_key: str
    editor_id: str
    cors_origins: tuple[str, ...]


@lru_cache
def editorial_settings() -> EditorialSettings:
    data = _load_toml().get("editorial", {})
    api_key = str(data.get("api_key") or "").strip()
    enabled = bool(data.get("enabled", False)) or bool(api_key)
    origins_raw = data.get("cors_origins")
    if isinstance(origins_raw, list):
        origins = tuple(str(o).strip() for o in origins_raw if str(o).strip())
    else:
        origins = ("http://localhost:5174", "http://127.0.0.1:5174")
    return EditorialSettings(
        enabled=enabled,
        api_key=api_key,
        editor_id=str(data.get("editor_id") or "editor").strip() or "editor",
        cors_origins=origins,
    )


@lru_cache
def database_url() -> str:
    data = _load_toml()
    if data.get("database", {}).get("url"):
        return str(data["database"]["url"])
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://raa:raa@localhost:5432/raa_modernized",
    )
