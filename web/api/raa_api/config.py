from __future__ import annotations

import os
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
