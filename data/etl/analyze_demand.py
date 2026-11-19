"""Domanda e prezzi: analisi descrittiva su bookings + kpi_daily (R2, WP12).

Risponde all'obiettivo del caso «Prevedere la domanda e supportare le decisioni
sui prezzi» AL LIVELLO ANALITICO: stagionalita', lead-time, canali, relazione
ADR-occupazione, effetti di deposito/tipo cliente/ospite ripetuto sulle
cancellazioni. La meta' previsionale e' decisione del cliente al SAL 1 (HA-14):
vedi docs/analysis/demand-pricing.md, sezione «Decisione sulla previsione».

SOLA LETTURA sul DB: tre SELECT (sotto), nessuna scrittura, nessun cambio schema.
Ogni numero del JSON e' ricalcolabile eseguendo questo script sulle query citate.
Formule congelate: docs/data-dictionary.md §3 + openapi.yaml (getKpiSeasonality,
getKpiChannels). Filtro KPI = baseline (is_canceled=false, nights>0, adr>0);
cancellazioni e lead-time su TUTTE le righe post-dedup (Assunzione 4: la dedup
e' gia' avvenuta nel loader, il DB contiene 87.396 righe sul dataset completo).

Gira col venv del backend:  PYTHONPATH=backend python data/etl/analyze_demand.py
Sidecar (host->container TCP bloccato): docker run --rm -i --network container:buby-postgres
  -v "$PWD":/repo:ro -v "$PWD/data/eval":/repo/data/eval -w /repo
  -e PYTHONPATH=/repo/.venv/lib/python3.12/site-packages:/repo/backend:/repo/data
  python:3.12-slim python data/etl/analyze_demand.py
Output: data/eval/demand_analysis.json + tabelle stampate (stessi numeri arrotondati).
"""

# stub pandas: chiavi groupby (Hashable) e indexing booleano (DataFrame|Series)
# sono rumore statico; la verifica vera e' nei test e nell'assert baseline.
# pyright: reportArgumentType=false, reportAttributeAccessIssue=false

import json
from pathlib import Path

import pandas as pd  # pyright: ignore[reportMissingImports]
import psycopg  # pyright: ignore[reportMissingImports]

from app.config import DATABASE_URL

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "eval" / "demand_analysis.json"

# baseline pulita (data-dictionary §3): se questi numeri non tornano sul dataset
# completo, e' il codice a essere sbagliato. Mai aggiustare il baseline.
BASELINE = dict(
    rows=87396, valid=61777, room_nights=218410, revenue=22976960.13, cancel_rate=0.2749
)

QUERIES = {
    "bookings": """SELECT property_id, arrival_date, lead_time, nights, adr, is_canceled,
       market_segment, deposit_type, customer_type, is_repeated_guest
FROM bookings""",
    "kpi_daily": "SELECT property_id, date, room_nights, revenue FROM kpi_daily",
    "properties": "SELECT id, name, room_count FROM properties",
}

LEAD_BUCKETS = [("0-7", 0, 7), ("8-30", 8, 30), ("31-90", 31, 90), ("91-180", 91, 180)]
OCC_BUCKETS = [("<0.40", 0.0, 0.4), ("0.40-0.59", 0.4, 0.6), ("0.60-0.79", 0.6, 0.8)]


def lead_bucket(days: int) -> str:
    """Bucket di lead-time in giorni: 0-7 / 8-30 / 31-90 / 91-180 / >180."""
    for label, lo, hi in LEAD_BUCKETS:
        if lo <= days <= hi:
            return label
    return ">180"


def occupancy_bucket(occ: float) -> str:
    """Bucket di occupazione giornaliera (rapporto 0-1, capacita' assunta)."""
    for label, lo, hi in OCC_BUCKETS:
        if lo <= occ < hi:
            return label
    return ">=0.80"


def _r(x, ndigits: int):
    """Arrotonda per JSON/tabelle; None/NaN restano null (mai inventare numeri)."""
    return None if x is None or pd.isna(x) else round(float(x), ndigits)


def pooled_adr(df: pd.DataFrame):
    """ADR pooled = somma(adr*nights)/somma(nights), non media degli adr di riga."""
    nights = int(df.nights.sum())
    if not nights:
        return None
    return _r((df.adr * df.nights).sum() / nights, 2)


def cancel_stats(df: pd.DataFrame) -> dict:
    n = len(df)
    canceled = int(df.is_canceled.sum())
    return {"n": n, "canceled": canceled, "cancel_rate": _r(canceled / n, 4) if n else None}


def baseline_metrics(bookings: pd.DataFrame) -> dict:
    valid = bookings[~bookings.is_canceled & (bookings.nights > 0) & (bookings.adr > 0)]
    rn = int(valid.nights.sum())
    rev = float((valid.adr * valid.nights).sum())
    return {
        "rows": len(bookings),
        "valid": len(valid),
        "room_nights": rn,
        "revenue": _r(rev, 2),
        "adr": _r(rev / rn, 2) if rn else None,
        "median_adr_valid_rows": _r(valid.adr.median(), 2),
        "canceled": int(bookings.is_canceled.sum()),
        "cancel_rate": _r(bookings.is_canceled.mean(), 4),
    }


def _adr_by_month(valid: pd.DataFrame) -> dict:
    return {
        int(m): {"avg_adr": pooled_adr(g), "valid_bookings": len(g)}
        for m, g in valid.groupby("month")
    }


def _seasonality_points(daily: pd.DataFrame, adr_by_month: dict, n_props: int) -> list:
    """Medie per mese dell'anno (mai totali grezzi: 2015 e 2017 sono parziali).

    avg_revenue = media del revenue giornaliero sommato divisa per n_props
    (media per proprieta', formula congelata getKpiSeasonality con property null).
    """
    g = daily.groupby("month")
    monthly = g.agg(
        days_observed=("date", "size"),
        avg_room_nights=("room_nights", "mean"),
        avg_revenue_total=("revenue", "mean"),
        avg_occupancy=("occupancy", "mean"),
    )
    monthly["years"] = g["year"].unique()
    points = []
    for m, row in monthly.iterrows():
        adr = adr_by_month.get(int(m), {"avg_adr": None, "valid_bookings": 0})
        points.append(
            {
                "month": int(m),
                "days_observed": int(row.days_observed),
                "years_observed": sorted(int(y) for y in row.years),
                "avg_room_nights": _r(row.avg_room_nights, 1),
                "avg_revenue": _r(row.avg_revenue_total / n_props, 2),
                "avg_occupancy": _r(row.avg_occupancy, 4),
                "avg_adr": adr["avg_adr"],
                "valid_bookings": adr["valid_bookings"],
            }
        )
    return points


def _corr(x, y):
    """Pearson via pandas; None se meno di 3 punti o serie costante (NaN)."""
    s = pd.DataFrame({"x": list(x), "y": list(y)}).dropna()
    if len(s) < 3:
        return None
    return _r(s.x.corr(s.y), 4)


def seasonality(valid: pd.DataFrame, daily: pd.DataFrame, rooms: dict, names: dict) -> dict:
    combined = daily.groupby("date", as_index=False).agg(
        room_nights=("room_nights", "sum"), revenue=("revenue", "sum")
    )
    capacity = sum(rooms.values())
    combined["occupancy"] = combined.room_nights / capacity
    combined["month"] = combined.date.dt.month
    combined["year"] = combined.date.dt.year
    out = {
        "combined": _seasonality_points(combined, _adr_by_month(valid), len(rooms)),
        "per_property": {},
        "_combined_daily": combined,
    }
    for pid, name in names.items():
        d = daily[daily.property_id == pid].copy()
        d["occupancy"] = d.room_nights / rooms[pid]
        d["month"] = d.date.dt.month
        d["year"] = d.date.dt.year
        v = valid[valid.property_id == pid]
        out["per_property"][name] = _seasonality_points(d, _adr_by_month(v), 1)
    return out


def lead_time_analysis(bookings: pd.DataFrame) -> dict:
    def stats(g):
        return {
            "n": len(g),
            "mean_lead_time": _r(g.lead_time.mean(), 1),
            "median_lead_time": _r(g.lead_time.median(), 1),
        }

    by_month = [{"month": int(m), **stats(g)} for m, g in bookings.groupby("month")]
    by_segment = [
        {"market_segment": s, **stats(g)} for s, g in bookings.groupby("market_segment")
    ]
    by_segment.sort(key=lambda r: -r["n"])
    buckets = []
    for label, _, _ in [*LEAD_BUCKETS, (">180", 0, 0)]:
        g = bookings[bookings.lead_bucket == label]
        buckets.append(
            {"bucket": label, **cancel_stats(g), "mean_lead_time": _r(g.lead_time.mean(), 1)}
        )
    corr = _corr(bookings.lead_time, bookings.is_canceled.astype(int))
    return {
        "by_month": by_month,
        "by_segment": by_segment,
        "buckets": buckets,
        "corr_lead_cancel": corr,
    }


def channels(bookings: pd.DataFrame, valid: pd.DataFrame) -> list:
    total_rev = float((valid.adr * valid.nights).sum())
    rows = []
    for seg, g in bookings.groupby("market_segment"):
        gv = valid[valid.market_segment == seg]
        rev = float((gv.adr * gv.nights).sum())
        rows.append(
            {
                "market_segment": seg,
                "bookings": len(g),
                "share": _r(len(g) / len(bookings), 4),
                **{k: v for k, v in cancel_stats(g).items() if k != "n"},
                "valid_bookings": len(gv),
                "room_nights": int(gv.nights.sum()),
                "revenue": _r(rev, 2),
                "revenue_share": _r(rev / total_rev, 4) if total_rev else None,
                "avg_adr": pooled_adr(gv),
            }
        )
    rows.sort(key=lambda r: -r["bookings"])
    return rows


def adr_occupancy(valid: pd.DataFrame, combined_daily: pd.DataFrame, seas: dict) -> dict:
    nz = combined_daily[combined_daily.room_nights > 0].copy()
    nz["adr"] = nz.revenue / nz.room_nights
    occ_by_month = {p["month"]: p["avg_occupancy"] for p in seas["combined"]}

    monthly = {
        "combined": _corr(
            [p["avg_adr"] for p in seas["combined"]],
            [p["avg_occupancy"] for p in seas["combined"]],
        )
    }
    for name, points in seas["per_property"].items():
        monthly[name] = _corr([p["avg_adr"] for p in points], [p["avg_occupancy"] for p in points])

    by_segment = []
    for seg, g in valid.groupby("market_segment"):
        pairs = [
            (pooled_adr(gg), occ_by_month[int(m)])
            for m, gg in g.groupby("month")
            if int(m) in occ_by_month
        ]
        by_segment.append(
            {
                "market_segment": seg,
                "n_months": len(pairs),
                "corr_adr_occupancy": _corr([a for a, _ in pairs], [o for _, o in pairs]),
            }
        )
    by_segment.sort(key=lambda r: -r["n_months"])

    nz["occ_bucket"] = nz.occupancy.map(occupancy_bucket)
    by_level = []
    for label, _, _ in [*OCC_BUCKETS, (">=0.80", 0.0, 0.0)]:
        g = nz[nz.occ_bucket == label]
        by_level.append(
            {
                "bucket": label,
                "days": len(g),
                "adr_mean": _r(g.adr.mean(), 2),
                "adr_median": _r(g.adr.median(), 2),
                "adr_p25": _r(g.adr.quantile(0.25), 2),
                "adr_p75": _r(g.adr.quantile(0.75), 2),
            }
        )
    return {
        "daily_corr_adr_occupancy": _corr(nz.adr, nz.occupancy),
        "daily_days_with_guests": len(nz),
        "daily_zero_days": int((combined_daily.room_nights == 0).sum()),
        "monthly_corr_adr_occupancy": monthly,
        "segment_monthly_corr": by_segment,
        "adr_by_occupancy_bucket": by_level,
    }


def guest_effects(bookings: pd.DataFrame) -> dict:
    def grouped(col):
        return [
            {col: bool(k) if col == "is_repeated_guest" else k, **cancel_stats(g)}
            for k, g in bookings.groupby(col)
        ]

    return {
        "is_repeated_guest": grouped("is_repeated_guest"),
        "deposit_type": grouped("deposit_type"),
        "customer_type": grouped("customer_type"),
    }


def analyze(bookings: pd.DataFrame, daily: pd.DataFrame, props: pd.DataFrame) -> dict:
    """Analisi pura (niente DB): testabile su fixture, stessi numeri del JSON."""
    rooms = props.set_index("id").room_count.to_dict()
    names = props.set_index("id")["name"].to_dict()
    valid = bookings[~bookings.is_canceled & (bookings.nights > 0) & (bookings.adr > 0)].copy()
    valid["month"] = valid.arrival_date.dt.month
    b = bookings.copy()
    b["month"] = b.arrival_date.dt.month
    b["lead_bucket"] = b.lead_time.map(lead_bucket)

    seas = seasonality(valid, daily, rooms, names)
    combined_daily = seas.pop("_combined_daily")
    return {
        "meta": {
            "script": "data/etl/analyze_demand.py",
            "report": "docs/analysis/demand-pricing.md",
            "read_only": True,
            "filters": {
                "kpi": "is_canceled=false AND nights>0 AND adr>0 (baseline, data-dictionary §3)",
                "cancellazioni_e_lead_time": "tutte le righe post-dedup (Assunzione 4)",
            },
            "capacity_assumed": {names[pid]: n for pid, n in rooms.items()}
            | {"combined": sum(rooms.values())},
            "formulas": {
                "avg_adr": "pooled arrivi mese: sum(adr*nights)/sum(nights) (getKpiSeasonality)",
                "avg_occupancy": "media daily stay-day su capacita' assunta (getKpiSeasonality)",
                "avg_revenue": "media revenue daily sommato / n proprieta' (getKpiSeasonality)",
                "avg_room_nights": "media room-nights giornalieri sommati (stay-day, kpi_daily)",
                "cancel_rate": "cancellate / righe post-dedup, per gruppo (data-dictionary §3)",
            },
            "queries": QUERIES,
        },
        "baseline": baseline_metrics(bookings),
        "seasonality": seas,
        "lead_time": lead_time_analysis(b),
        "channels": channels(b, valid),
        "adr_occupancy": adr_occupancy(valid, combined_daily, seas),
        "guest_effects": guest_effects(b),
    }


def load_frames(conn):
    """Tre SELECT, nient'altro. Accetta connessione psycopg o SQLAlchemy (test)."""
    bookings = pd.read_sql(QUERIES["bookings"], conn)
    daily = pd.read_sql(QUERIES["kpi_daily"], conn)
    props = pd.read_sql(QUERIES["properties"], conn)
    # numeric Postgres -> Decimal: senza cast le somme restano object
    bookings["adr"] = bookings.adr.astype(float)
    bookings["arrival_date"] = pd.to_datetime(bookings.arrival_date)
    daily["revenue"] = daily.revenue.astype(float)
    daily["date"] = pd.to_datetime(daily.date)
    return bookings, daily, props


def print_tables(result: dict) -> None:
    def show(title, rows):
        print(f"\n== {title} ==")
        print(pd.DataFrame(rows).to_string(index=False))

    show("baseline", [result["baseline"]])
    show("stagionalita' (combined)", result["seasonality"]["combined"])
    for name, points in result["seasonality"]["per_property"].items():
        show(f"stagionalita' {name}", points)
    show("lead-time per mese", result["lead_time"]["by_month"])
    show("lead-time per segmento", result["lead_time"]["by_segment"])
    show("cancellazioni per bucket lead-time", result["lead_time"]["buckets"])
    print(f"corr(lead_time, cancellazione) = {result['lead_time']['corr_lead_cancel']}")
    show("canali (market_segment)", result["channels"])
    ao = result["adr_occupancy"]
    print(f"\n== ADR vs occupazione ==\ncorr giornaliera = {ao['daily_corr_adr_occupancy']}")
    print(f"corr mensile = {ao['monthly_corr_adr_occupancy']}")
    show("corr mensile ADR-segmento vs occupazione", ao["segment_monthly_corr"])
    show("ADR per livello di occupazione", ao["adr_by_occupancy_bucket"])
    for col, rows in result["guest_effects"].items():
        show(f"cancellazioni per {col}", rows)


def main() -> None:
    url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(url) as conn:
        bookings, daily, props = load_frames(conn)
    result = analyze(bookings, daily, props)
    b = result["baseline"]
    if b["rows"] == BASELINE["rows"]:
        for key, expected in BASELINE.items():
            assert b[key] == expected, f"baseline {key}: {b[key]} != {expected}"
        print("baseline completa verificata (87396/61777/218410/22976960.13/0.2749)")
    else:
        print(f"dataset ridotto ({b['rows']} righe): baseline completa non applicabile")
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print_tables(result)
    print(f"\nJSON scritto: {OUT}")


if __name__ == "__main__":
    main()