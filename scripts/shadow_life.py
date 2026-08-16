#!/usr/bin/env python3
"""CLI helper: enrich persoon rows with EDTF + shadow life-date columns."""

from __future__ import annotations

import argparse
import pickle
from pathlib import Path

import pandas as pd

from raa_life_dates.shadow import enrich_persoon_life_dates


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich persoon frame with life-date columns")
    parser.add_argument("--pickle", type=Path, required=True, help="Path to extab.pkl")
    parser.add_argument("--out", type=Path, help="Optional output pickle with enriched persoon")
    args = parser.parse_args()

    with args.pickle.open("rb") as handle:
        extab = pickle.load(handle)
    persoon = enrich_persoon_life_dates(extab["persoon"], extab["aanstelling"])
    shadow_starts = (persoon["life_start_source"] == "shadow").sum()
    shadow_ends = (persoon["life_end_source"] == "shadow").sum()
    print(f"Enriched {len(persoon)} persons; shadow starts={shadow_starts}, ends={shadow_ends}")
    if args.out:
        extab = dict(extab)
        extab["persoon"] = persoon
        with args.out.open("wb") as handle:
            pickle.dump(extab, handle)
        print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
