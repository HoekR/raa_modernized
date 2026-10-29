#!/usr/bin/env python3
"""Enrich persoon duplicate suspects with field diffs + SURF links.

For every suspect pair, indicate whether life dates match and list other
differences — input for a defensible merge policy.

Reads:  output/persoon_duplicate_suspects.json
Writes:
  output/persoon_duplicate_suspects_enriched.json
  output/persoon_duplicate_suspects_compare.xlsx   (all pairs, diff-first)
  output/persoon_duplicate_suspects_uncertain.xlsx (medium/low + fuzzy high)

  uv run python scripts/enrich_persoon_duplicate_suspects.py --all
  uv run python scripts/enrich_persoon_duplicate_suspects.py --base-url http://145.38.193.71
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

DEFAULT_BASE = "http://145.38.193.71"
CACHE_PATH = Path("output/.persoon_detail_cache.json")

PERIOD_KEYS = (
    ("me", "ME"),
    ("republiek", "Republiek"),
    ("republiek_friezen", "Friezen"),
    ("batfra", "BatFra"),
    ("negentiende_eeuw", "19e"),
    ("divperioden", "div"),
)

# Scalar persoon fields to diff (API keys → label)
SCALAR_FIELDS = (
    ("voornaam", "voornaam"),
    ("tussenvoegsel", "tussenvoegsel"),
    ("geslachtsnaam", "geslachtsnaam"),
    ("listing_naam", "listing_naam"),
    ("heerlijkheid", "heerlijkheid"),
    ("adelspredikaat", "adelspredikaat"),
    ("adel", "adel"),
    ("geboorteplaats", "geboorteplaats"),
    ("overlijdensplaats", "overlijdensplaats"),
    ("geboortedatum_als_bekend", "geboorte_als_bekend"),
    ("overlijdensdatum_als_bekend", "overlijden_als_bekend"),
    ("opmerkingen", "opmerkingen"),
)


def person_url(base: str, person_id: int) -> str:
    return f"{base.rstrip('/')}/personen/{person_id}"


def api_url(base: str, person_id: int) -> str:
    return f"{base.rstrip('/')}/api/personen/{person_id}"


def fetch_json(url: str, timeout: float = 30.0) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")


def norm_text(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v).strip()


def year_int(v) -> int | None:
    if v is None or v == "":
        return None
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def period_flags(detail: dict) -> str:
    return ", ".join(label for key, label in PERIOD_KEYS if detail.get(key))


def aanst_key(a: dict) -> tuple:
    return (
        norm_text(a.get("functie")),
        norm_text(a.get("instelling")),
        norm_text(a.get("van_als_bekend")),
        norm_text(a.get("tot_als_bekend")),
        norm_text(a.get("provincie")),
    )


def format_aanst_key(k: tuple) -> str:
    fn, inst, van, tot, prov = k
    base = f"{van or '?'}–{tot or '?'}: {fn or '?'} @ {inst or '?'}"
    return f"{base} [{prov}]" if prov else base


def format_aanstellingen(detail: dict, limit: int = 12) -> str:
    rows = detail.get("aanstellingen") or []
    lines = [format_aanst_key(aanst_key(a)) for a in rows[:limit]]
    if len(rows) > limit:
        lines.append(f"… +{len(rows) - limit} meer")
    return "\n".join(lines)


def life_dates_comparison(a: dict, b: dict) -> dict:
    """Compare life years and textual birth/death dates."""
    as_, ae = year_int(a.get("life_start_year")), year_int(a.get("life_end_year"))
    bs, be = year_int(b.get("life_start_year")), year_int(b.get("life_end_year"))
    ga = norm_text(a.get("geboortedatum_als_bekend"))
    gb = norm_text(b.get("geboortedatum_als_bekend"))
    oa = norm_text(a.get("overlijdensdatum_als_bekend"))
    ob = norm_text(b.get("overlijdensdatum_als_bekend"))

    years_same = as_ == bs and ae == be and (as_ is not None or ae is not None)
    # both completely empty years
    if as_ is None and ae is None and bs is None and be is None:
        years_same = False
        years_status = "both-missing"
        years_note = "geen life_start/end op beide"
    elif as_ == bs and ae == be:
        years_same = True
        years_status = "same"
        years_note = f"{as_ or '?'}–{ae or '?'}"
    elif as_ is not None and bs is not None and ae is not None and be is not None:
        if abs(as_ - bs) <= 1 and abs(ae - be) <= 1:
            years_same = False
            years_status = "near"
            years_note = f"A={as_}–{ae} vs B={bs}–{be} (±1)"
        else:
            years_same = False
            years_status = "differ"
            years_note = f"A={as_}–{ae} vs B={bs}–{be}"
    elif (as_ == bs and as_ is not None) and (ae is None or be is None):
        years_same = False
        years_status = "start-only-match"
        years_note = f"start={as_}; end A={ae} B={be}"
    elif (ae == be and ae is not None) and (as_ is None or bs is None):
        years_same = False
        years_status = "end-only-match"
        years_note = f"end={ae}; start A={as_} B={bs}"
    else:
        years_same = False
        years_status = "partial-or-differ"
        years_note = f"A={as_}–{ae} vs B={bs}–{be}"

    text_birth_same = ga == gb
    text_death_same = oa == ob
    text_same = text_birth_same and text_death_same
    text_notes = []
    if not text_birth_same:
        text_notes.append(f"geboorte_als_bekend: '{ga}' vs '{gb}'")
    if not text_death_same:
        text_notes.append(f"overlijden_als_bekend: '{oa}' vs '{ob}'")

    return {
        "life_years_same": years_same,
        "life_years_status": years_status,
        "life_years_note": years_note,
        "life_dates_text_same": text_same,
        "life_dates_text_note": "; ".join(text_notes) if text_notes else "same",
        "years_a": f"{as_ or '?'}-{ae or '?'}",
        "years_b": f"{bs or '?'}-{be or '?'}",
    }


def diff_pair(a: dict, b: dict) -> dict:
    """Field-level differences between two persoon API payloads."""
    life = life_dates_comparison(a, b)
    differing: list[str] = []
    details: list[str] = []

    if not life["life_years_same"]:
        differing.append("life_years")
        details.append(f"life_years: {life['life_years_note']}")
    if not life["life_dates_text_same"]:
        differing.append("life_dates_text")
        details.append(life["life_dates_text_note"])

    for key, label in SCALAR_FIELDS:
        if key in ("geboortedatum_als_bekend", "overlijdensdatum_als_bekend"):
            continue  # covered above
        va, vb = norm_text(a.get(key)), norm_text(b.get(key))
        if va != vb:
            differing.append(label)
            # truncate long opmerkingen in detail
            da, db_ = va, vb
            if label == "opmerkingen":
                da = (da[:120] + "…") if len(da) > 120 else da
                db_ = (db_[:120] + "…") if len(db_) > 120 else db_
            details.append(f"{label}: '{da}' vs '{db_}'")

    pa = {label for key, label in PERIOD_KEYS if a.get(key)}
    pb = {label for key, label in PERIOD_KEYS if b.get(key)}
    if pa != pb:
        differing.append("periodes")
        only_a = ", ".join(sorted(pa - pb)) or "—"
        only_b = ", ".join(sorted(pb - pa)) or "—"
        details.append(f"periodes: only_A=[{only_a}] only_B=[{only_b}] both=[{', '.join(sorted(pa & pb)) or '—'}]")

    ka = {aanst_key(x) for x in (a.get("aanstellingen") or [])}
    kb = {aanst_key(x) for x in (b.get("aanstellingen") or [])}
    shared = ka & kb
    only_a_k = ka - kb
    only_b_k = kb - ka
    if only_a_k or only_b_k:
        differing.append("aanstellingen")
        details.append(
            f"aanstellingen: shared={len(shared)} only_A={len(only_a_k)} only_B={len(only_b_k)}"
        )

    # Suggested merge bucket for policy design.
    # Primary signals: life_years_same + core name identity (ignore listing_naam noise).
    core_name = {"voornaam", "tussenvoegsel", "geslachtsnaam"}
    name_diff = bool(core_name & set(differing))
    years_ok = life["life_years_same"] or life["life_years_status"] == "near"
    soft = {
        "periodes",
        "aanstellingen",
        "life_dates_text",
        "geboorteplaats",
        "overlijdensplaats",
        "opmerkingen",
        "heerlijkheid",
        "adel",
        "adelspredikaat",
        "listing_naam",
    }
    hard = set(differing) - soft

    if not differing:
        merge_class = "identical"
    elif years_ok and not name_diff and not hard:
        # Same person identity; corpus/period split or annotation drift
        merge_class = "same-identity-mergeable"
    elif years_ok and name_diff and not ({"life_years"} & set(differing)):
        merge_class = "name-variant-same-years"
    elif (not years_ok) and not name_diff:
        merge_class = "same-name-year-mismatch"
    elif name_diff and not years_ok:
        merge_class = "name-and-year-differ"
    else:
        merge_class = "other-field-diff"

    return {
        **life,
        "differences": "; ".join(differing) if differing else "(none)",
        "diff_count": len(differing),
        "diff_detail": " | ".join(details) if details else "(geen verschillen)",
        "aanst_shared": len(shared),
        "aanst_only_a": len(only_a_k),
        "aanst_only_b": len(only_b_k),
        "aanst_only_a_sample": "\n".join(format_aanst_key(k) for k in sorted(only_a_k)[:8]),
        "aanst_only_b_sample": "\n".join(format_aanst_key(k) for k in sorted(only_b_k)[:8]),
        "periodes_a": period_flags(a),
        "periodes_b": period_flags(b),
        "merge_class": merge_class,
    }


def is_uncertain(s: dict) -> bool:
    if s.get("confidence") != "high":
        return True
    return not (
        s.get("voornaam_method") == "exact-voornaam"
        and s.get("surname_method") == "exact-geslacht"
        and s.get("year_method") == "exact-years"
    )


def get_detail(person_id: int, base: str, cache: dict) -> dict:
    key = str(person_id)
    if key in cache:
        return cache[key]
    detail = fetch_json(api_url(base, person_id))
    cache[key] = detail
    return detail


def enrich_pair(s: dict, base: str, cache: dict) -> dict:
    a = get_detail(s["id_a"], base, cache)
    b = get_detail(s["id_b"], base, cache)
    diff = diff_pair(a, b)
    out = dict(s)
    out["url_a"] = person_url(base, int(s["id_a"]))
    out["url_b"] = person_url(base, int(s["id_b"]))
    out["listing_a"] = a.get("listing_naam") or s.get("listing_a")
    out["listing_b"] = b.get("listing_naam") or s.get("listing_b")
    out["geboorte_als_bekend_a"] = norm_text(a.get("geboortedatum_als_bekend"))
    out["geboorte_als_bekend_b"] = norm_text(b.get("geboortedatum_als_bekend"))
    out["overlijden_als_bekend_a"] = norm_text(a.get("overlijdensdatum_als_bekend"))
    out["overlijden_als_bekend_b"] = norm_text(b.get("overlijdensdatum_als_bekend"))
    out["geboorteplaats_a"] = norm_text(a.get("geboorteplaats"))
    out["geboorteplaats_b"] = norm_text(b.get("geboorteplaats"))
    out["overlijdensplaats_a"] = norm_text(a.get("overlijdensplaats"))
    out["overlijdensplaats_b"] = norm_text(b.get("overlijdensplaats"))
    out["heerlijkheid_a"] = norm_text(a.get("heerlijkheid"))
    out["heerlijkheid_b"] = norm_text(b.get("heerlijkheid"))
    out["opmerkingen_a"] = norm_text(a.get("opmerkingen"))
    out["opmerkingen_b"] = norm_text(b.get("opmerkingen"))
    out["aanstellingen_a"] = format_aanstellingen(a)
    out["aanstellingen_b"] = format_aanstellingen(b)
    out["n_aanst_a"] = len(a.get("aanstellingen") or [])
    out["n_aanst_b"] = len(b.get("aanstellingen") or [])
    out["years_a_str"] = diff["years_a"]
    out["years_b_str"] = diff["years_b"]
    out.update(diff)
    out["match"] = f"{s.get('surname_method')}; {s.get('voornaam_method')}; {s.get('year_method')}"
    return out


COMPARE_COLUMNS = [
    "confidence",
    "merge_class",
    "life_years_same",
    "life_years_status",
    "life_years_note",
    "life_dates_text_same",
    "life_dates_text_note",
    "differences",
    "diff_count",
    "diff_detail",
    "aanst_shared",
    "aanst_only_a",
    "aanst_only_b",
    "aanst_only_a_sample",
    "aanst_only_b_sample",
    "id_a",
    "listing_a",
    "url_a",
    "years_a_str",
    "periodes_a",
    "n_aanst_a",
    "geboorte_als_bekend_a",
    "overlijden_als_bekend_a",
    "geboorteplaats_a",
    "overlijdensplaats_a",
    "opmerkingen_a",
    "aanstellingen_a",
    "id_b",
    "listing_b",
    "url_b",
    "years_b_str",
    "periodes_b",
    "n_aanst_b",
    "geboorte_als_bekend_b",
    "overlijden_als_bekend_b",
    "geboorteplaats_b",
    "overlijdensplaats_b",
    "opmerkingen_b",
    "aanstellingen_b",
    "match",
    "surname_method",
    "voornaam_method",
    "year_method",
]


def _hyperlink_urls(ws) -> None:
    url_cols = {
        cell.value: idx + 1
        for idx, cell in enumerate(ws[1])
        if cell.value in ("url_a", "url_b")
    }
    for row_i in range(2, ws.max_row + 1):
        for col_i in url_cols.values():
            cell = ws.cell(row=row_i, column=col_i)
            if cell.value:
                cell.hyperlink = str(cell.value)
                cell.style = "Hyperlink"


def write_excel(rows: list[dict], path: Path, sheet: str, columns: list[str]) -> None:
    records = [{c: r.get(c) for c in columns} for r in rows]
    # Excel-friendly booleans
    for rec in records:
        for k in ("life_years_same", "life_dates_text_same"):
            if k in rec and isinstance(rec[k], bool):
                rec[k] = "yes" if rec[k] else "no"
    df = pd.DataFrame(records, columns=columns)
    path.parent.mkdir(exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet)
        ws = writer.sheets[sheet]
        _hyperlink_urls(ws)
        ws.auto_filter.ref = ws.dimensions
        ws.freeze_panes = "A2"
    print(f"Wrote {path} ({len(rows)} rows)")


def write_summary_md(rows: list[dict], path: Path) -> None:
    from collections import Counter

    life = Counter(r["life_years_status"] for r in rows)
    mclass = Counter(r["merge_class"] for r in rows)
    conf = Counter(r["confidence"] for r in rows)
    lines = [
        "# Persoon duplicate comparison summary",
        "",
        f"Total pairs: **{len(rows)}** ({dict(conf)})",
        "",
        "## Life years",
        "",
        "| Status | n |",
        "|--------|--:|",
    ]
    for k, n in life.most_common():
        lines.append(f"| {k} | {n} |")
    lines += ["", "## Merge class (suggested buckets)", "", "| Class | n |", "|-------|--:|"]
    for k, n in mclass.most_common():
        lines.append(f"| `{k}` | {n} |")
    lines += [
        "",
        "## Difference fields (how often each appears)",
        "",
        "| Field | pairs |",
        "|-------|------:|",
    ]
    field_c: Counter[str] = Counter()
    for r in rows:
        diffs = r.get("differences") or ""
        if diffs == "(none)":
            field_c["(none)"] += 1
        else:
            for f in diffs.split("; "):
                field_c[f] += 1
    for k, n in field_c.most_common():
        lines.append(f"| {k} | {n} |")
    lines += [
        "",
        "Excel: `output/persoon_duplicate_suspects_compare.xlsx`",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("output/persoon_duplicate_suspects.json"),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        default=True,
        help="Enrich all pairs (default). Use --uncertain-only to restrict.",
    )
    parser.add_argument(
        "--uncertain-only",
        action="store_true",
        help="Only medium/low + fuzzy high",
    )
    parser.add_argument("--sleep", type=float, default=0.03)
    args = parser.parse_args()

    suspects = json.loads(args.input.read_text(encoding="utf-8"))
    selected = (
        [s for s in suspects if is_uncertain(s)] if args.uncertain_only else suspects
    )
    print(f"Enriching {len(selected)} / {len(suspects)} pairs from {args.base_url}")

    cache = load_cache()
    ids = sorted({s["id_a"] for s in selected} | {s["id_b"] for s in selected})
    for i, pid in enumerate(ids, 1):
        try:
            get_detail(pid, args.base_url, cache)
        except urllib.error.HTTPError as exc:
            print(f"  WARN id={pid}: HTTP {exc.code}")
        except Exception as exc:  # noqa: BLE001
            print(f"  WARN id={pid}: {exc}")
        if i % 100 == 0:
            save_cache(cache)
            print(f"  fetched {i}/{len(ids)}")
        time.sleep(args.sleep)
    save_cache(cache)

    enriched: list[dict] = []
    for s in selected:
        try:
            enriched.append(enrich_pair(s, args.base_url, cache))
        except Exception as exc:  # noqa: BLE001
            print(f"  skip pair {s['id_a']}/{s['id_b']}: {exc}")

    # Sort: identical first, then by merge_class / confidence
    order_class = {
        "identical": 0,
        "same-identity-mergeable": 1,
        "name-variant-same-years": 2,
        "same-name-year-mismatch": 3,
        "other-field-diff": 4,
        "name-and-year-differ": 5,
    }
    order_conf = {"high": 0, "medium": 1, "low": 2}
    enriched.sort(
        key=lambda r: (
            order_class.get(r.get("merge_class", ""), 9),
            order_conf.get(r.get("confidence", ""), 9),
            r.get("diff_count", 99),
            r.get("id_a", 0),
        )
    )

    out_json = Path("output/persoon_duplicate_suspects_enriched.json")
    out_json.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_json}")

    write_excel(
        enriched,
        Path("output/persoon_duplicate_suspects_compare.xlsx"),
        "compare",
        COMPARE_COLUMNS,
    )
    write_summary_md(enriched, Path("output/persoon_duplicate_suspects_compare.md"))

    uncertain = [r for r in enriched if is_uncertain(r)]
    write_excel(
        uncertain,
        Path("output/persoon_duplicate_suspects_uncertain.xlsx"),
        "uncertain",
        COMPARE_COLUMNS,
    )


if __name__ == "__main__":
    main()
