#!/usr/bin/env python3
"""Scan raa.persoon for likely duplicate persons.

Criteria (all required):
  - compatible life years (exact, or ±1; or start-only / end-only)
  - matching geslachtsnaam (exact, tussenvoegsel subset, or typo d≤2)
  - matching voornaam (exact, initials↔full, token prefix, or typo)

Writes:
  output/persoon_duplicate_suspects.json
  output/persoon_duplicate_suspects.md

  uv run python scripts/scan_persoon_duplicates.py
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from sqlalchemy import create_engine, text


def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://raa:raa@localhost:5432/raa_modernized",
    )


def fold(s: str | None) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower().replace("ĳ", "ij").replace("ij", "y")
    return re.sub(r"[^a-z0-9]+", "", s)


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if abs(len(a) - len(b)) > 3:
        return 99
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


TITLE_RE = re.compile(
    r"\b(mr|meester|dr|prof|jonkheer|jonkvrouw|ridder|heer|vrijheer|"
    r"baron|barones|graaf|gravin|hertog|prins|mevr|mej)\b\.?",
    re.I,
)


def strip_titles(s: str) -> str:
    s = TITLE_RE.sub(" ", s or "")
    return re.sub(r"\s+", " ", s).strip(" ,.")


def name_tokens(voornaam: str) -> list[str]:
    return re.findall(r"[A-Za-zÀ-ÿ]+", strip_titles(voornaam or ""))


def initials_of(tokens: list[str]) -> str:
    return "".join(t[0].lower() for t in tokens if t)


def voornaam_match(a: str, b: str) -> tuple[bool, str]:
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta and not tb:
        return True, "both-empty-voornaam"
    if not ta or not tb:
        return False, ""

    fa = [fold(t) for t in ta]
    fb = [fold(t) for t in tb]
    if fa == fb:
        return True, "exact-voornaam"

    ia, ib = initials_of(ta), initials_of(tb)
    a_all_init = all(len(t) == 1 for t in fa)
    b_all_init = all(len(t) == 1 for t in fb)
    if a_all_init and not b_all_init and ia == ib:
        return True, "initials-vs-full"
    if b_all_init and not a_all_init and ia == ib:
        return True, "initials-vs-full"
    if a_all_init and b_all_init and ia == ib:
        return True, "same-initials"

    if len(fa) == len(fb):
        ok = True
        methods: list[str] = []
        for x, y in zip(fa, fb):
            if x == y:
                continue
            if (len(x) == 1 and y.startswith(x)) or (len(y) == 1 and x.startswith(y)):
                methods.append("initial-token")
                continue
            if min(len(x), len(y)) >= 4 and levenshtein(x, y) <= 2:
                methods.append("typo-token")
                continue
            ok = False
            break
        if ok:
            return True, "+".join(methods) or "token-align"

    if len(fa) < len(fb) and fa == fb[: len(fa)] and len(fa) >= 1:
        return True, "prefix-tokens"
    if len(fb) < len(fa) and fb == fa[: len(fb)] and len(fb) >= 1:
        return True, "prefix-tokens"

    ca, cb = "".join(fa), "".join(fb)
    if ca and cb and min(len(ca), len(cb)) >= 4:
        d = levenshtein(ca, cb)
        if d <= 2 and abs(len(ca) - len(cb)) <= 2:
            return True, f"typo-voornaam(d={d})"
        if SequenceMatcher(None, ca, cb).ratio() >= 0.88 and d <= 3:
            return True, f"similar-voornaam(d={d})"

    return False, ""


def years_compatible(a: dict, b: dict, tol: int = 1) -> tuple[bool, str]:
    as_ = a["life_start_year"] if a["life_start_year"] is not None else a.get("geboorte_year")
    ae = a["life_end_year"] if a["life_end_year"] is not None else a.get("overlijden_year")
    bs = b["life_start_year"] if b["life_start_year"] is not None else b.get("geboorte_year")
    be = b["life_end_year"] if b["life_end_year"] is not None else b.get("overlijden_year")

    def close(x, y):
        if x is None or y is None:
            return None
        return abs(int(x) - int(y)) <= tol

    if as_ is not None and ae is not None and bs is not None and be is not None:
        if close(as_, bs) and close(ae, be):
            if int(as_) == int(bs) and int(ae) == int(be):
                return True, "exact-years"
            return True, f"years-±{tol}"
        return False, ""

    sc, ec = close(as_, bs), close(ae, be)
    if sc is True and ec is True:
        return True, "partial-both"
    if sc is True and (ae is None or be is None):
        return True, "start-only"
    if ec is True and (as_ is None or bs is None):
        return True, "end-only"
    return False, ""


def surname_key(r: dict) -> str:
    g = fold(r["geslachtsnaam"])
    if g:
        return g
    return fold((r.get("listing_naam") or "").split(",")[0]) or ""


def surname_match(a: dict, b: dict) -> tuple[bool, str]:
    ga, gb = fold(a["geslachtsnaam"]), fold(b["geslachtsnaam"])
    ta, tb = fold(a["tussenvoegsel"]), fold(b["tussenvoegsel"])
    if not ga and not gb:
        return False, ""
    if ga == gb:
        if ta == tb or not ta or not tb:
            return True, "exact-geslacht"
        if ta in tb or tb in ta:
            return True, "tussenvoegsel-subset"
        return True, "geslacht-same-tv-diff"
    if ga and gb and min(len(ga), len(gb)) >= 4:
        d = levenshtein(ga, gb)
        if d <= 2 and abs(len(ga) - len(gb)) <= 2:
            return True, f"typo-geslacht(d={d})"
    return False, ""


def load_rows(engine):
    with engine.connect() as conn:
        return [
            dict(r)
            for r in conn.execute(
                text(
                    """
                    SELECT p.id, p.voornaam, p.tussenvoegsel, p.geslachtsnaam, p.listing_naam,
                           p.life_start_year, p.life_end_year,
                           p.geboorte_year, p.overlijden_year,
                           p.geboorteplaats, p.overlijdensplaats,
                           (SELECT COUNT(*) FROM raa.aanstelling a
                            WHERE a.persoon_id = p.id) AS n_aanst
                    FROM raa.persoon p
                    WHERE COALESCE(p.mark_for_delete, 0) = 0
                    """
                )
            ).mappings()
        ]


def scan(rows: list[dict]) -> list[dict]:
    exact_buckets: dict[str, list] = defaultdict(list)
    for r in rows:
        sk = surname_key(r)
        if sk:
            exact_buckets[sk].append(r)

    by_years: dict[tuple, list] = defaultdict(list)
    for r in rows:
        ys = r["life_start_year"] if r["life_start_year"] is not None else r["geboorte_year"]
        ye = r["life_end_year"] if r["life_end_year"] is not None else r["overlijden_year"]
        if ys is None and ye is None:
            continue
        by_years[(None if ys is None else int(ys), None if ye is None else int(ye))].append(r)

    seen_pairs: set[tuple[int, int]] = set()
    suspects: list[dict] = []

    def consider(a: dict, b: dict) -> None:
        i, j = (a["id"], b["id"]) if a["id"] < b["id"] else (b["id"], a["id"])
        if (i, j) in seen_pairs:
            return
        seen_pairs.add((i, j))
        sm, smethod = surname_match(a, b)
        if not sm:
            return
        ym, ymethod = years_compatible(a, b)
        if not ym:
            return
        vm, vmethod = voornaam_match(a["voornaam"] or "", b["voornaam"] or "")
        if not vm:
            return
        conf = "high"
        if ymethod in ("start-only", "end-only") or vmethod in (
            "prefix-tokens",
            "both-empty-voornaam",
        ):
            conf = "medium"
        if "typo" in smethod or "typo" in vmethod or ymethod.startswith("years-"):
            conf = "medium" if conf == "high" else conf
        if smethod == "geslacht-same-tv-diff":
            conf = "medium"
        if vmethod == "both-empty-voornaam" and "typo" in smethod:
            conf = "low"
        suspects.append(
            {
                "id_a": int(a["id"]),
                "id_b": int(b["id"]),
                "listing_a": a["listing_naam"],
                "listing_b": b["listing_naam"],
                "voornaam_a": a["voornaam"],
                "voornaam_b": b["voornaam"],
                "tussenvoegsel_a": a["tussenvoegsel"] or "",
                "tussenvoegsel_b": b["tussenvoegsel"] or "",
                "geslacht_a": a["geslachtsnaam"],
                "geslacht_b": b["geslachtsnaam"],
                "years_a": [
                    None if a["life_start_year"] is None else int(a["life_start_year"]),
                    None if a["life_end_year"] is None else int(a["life_end_year"]),
                ],
                "years_b": [
                    None if b["life_start_year"] is None else int(b["life_start_year"]),
                    None if b["life_end_year"] is None else int(b["life_end_year"]),
                ],
                "n_aanst_a": int(a["n_aanst"]),
                "n_aanst_b": int(b["n_aanst"]),
                "plaats_a": [a["geboorteplaats"], a["overlijdensplaats"]],
                "plaats_b": [b["geboorteplaats"], b["overlijdensplaats"]],
                "surname_method": smethod,
                "year_method": ymethod,
                "voornaam_method": vmethod,
                "confidence": conf,
            }
        )

    for members in exact_buckets.values():
        if len(members) < 2:
            continue
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                consider(members[i], members[j])

    for members in by_years.values():
        if len(members) < 2 or len(members) > 80:
            continue
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                a, b = members[i], members[j]
                if fold(a["geslachtsnaam"]) == fold(b["geslachtsnaam"]):
                    continue
                consider(a, b)

    order = {"high": 0, "medium": 1, "low": 2}
    suspects.sort(
        key=lambda s: (order[s["confidence"]], fold(s["geslacht_a"] or ""), s["id_a"], s["id_b"])
    )
    return suspects


def write_outputs(suspects: list[dict], out_dir: Path) -> None:
    out_dir.mkdir(exist_ok=True)
    (out_dir / "persoon_duplicate_suspects.json").write_text(
        json.dumps(suspects, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    def row(s: dict) -> str:
        ya = s["years_a"]
        ystr = f"{ya[0] or '?'}-{ya[1] or '?'}"
        methods = f"{s['surname_method']}; {s['voornaam_method']}; {s['year_method']}"
        return (
            f"| {s['id_a']} / {s['id_b']} | "
            f"{s['listing_a']} ({s['n_aanst_a']}) | {s['listing_b']} ({s['n_aanst_b']}) | "
            f"{ystr} | `{methods}` |"
        )

    lines = [
        "# Persoon duplicate suspects",
        "",
        "Criteria: compatible life years (exact or ±1) **and** matching geslachtsnaam "
        "(exact or typo d≤2) **and** matching voornaam (exact, initials↔full, prefix, or typo).",
        "",
        f"Total suspects: **{len(suspects)}** "
        f"(high={sum(1 for s in suspects if s['confidence']=='high')}, "
        f"medium={sum(1 for s in suspects if s['confidence']=='medium')}, "
        f"low={sum(1 for s in suspects if s['confidence']=='low')}).",
        "",
        "Re-run: `uv run python scripts/scan_persoon_duplicates.py`",
        "",
        "Machine-readable: `output/persoon_duplicate_suspects.json`",
        "",
        "## High confidence",
        "",
        "| IDs | A (n) | B (n) | Years | Match |",
        "|-----|-------|-------|-------|-------|",
    ]
    lines += [row(s) for s in suspects if s["confidence"] == "high"]
    lines += [
        "",
        "## Medium confidence",
        "",
        "| IDs | A (n) | B (n) | Years | Match |",
        "|-----|-------|-------|-------|-------|",
    ]
    lines += [row(s) for s in suspects if s["confidence"] == "medium"]
    lows = [s for s in suspects if s["confidence"] == "low"]
    if lows:
        lines += [
            "",
            "## Low confidence",
            "",
            "| IDs | A (n) | B (n) | Years | Match |",
            "|-----|-------|-------|-------|-------|",
        ]
        lines += [row(s) for s in lows]

    (out_dir / "persoon_duplicate_suspects.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    engine = create_engine(database_url())
    rows = load_rows(engine)
    print(f"Loaded {len(rows)} personen")
    suspects = scan(rows)
    write_outputs(suspects, Path("output"))
    print(f"Wrote {len(suspects)} suspects → output/persoon_duplicate_suspects.{{json,md}}")
    print(Counter(s["confidence"] for s in suspects))
    print("voornaam:", Counter(s["voornaam_method"] for s in suspects).most_common(10))
    print("geslacht:", Counter(s["surname_method"] for s in suspects).most_common(8))


if __name__ == "__main__":
    main()
