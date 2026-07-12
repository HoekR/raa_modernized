from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

PERIODS = [
    ("republiek", "Republiek"),
    ("batfra", "Bataafs-Franse Tijd"),
    ("negentiende_eeuw", "Negentiende Eeuw"),
    ("me", "Middeleeuwen"),
]


@lru_cache
def database_url() -> str:
    root = Path(__file__).resolve().parents[3]
    cfg = root / "config.local.toml"
    if cfg.exists():
        try:
            import tomllib

            data = tomllib.loads(cfg.read_text(encoding="utf-8"))
            return data["database"]["url"]
        except Exception:
            pass
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://raa:raa@localhost:5432/raa_modernized",
    )
