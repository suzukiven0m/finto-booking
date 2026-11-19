"""WP12: formule dell'analisi domanda su fixture (niente DB) + una integrazione DB.

I numeri delle fixture sono calcolati a mano e verificano le regole congelate
(data-dictionary §3, openapi getKpiSeasonality/getKpiChannels): bucket di
lead-time e occupazione, ADR pooled, medie per mese dell'anno (mai totali),
cancellazioni su tutte le righe post-dedup. Il test DB quadra la baseline
dell'analisi con SQL indipendente: vale sia col campione (CI) sia col completo
(pattern di test_kpi_daily.py, relazione non numero fisso).
"""

import pandas as pd
import pytest
from etl.analyze_demand import (
    analyze,
    baseline_metrics,
    lead_bucket,
    load_frames,
    occupancy_bucket,
    pooled_adr,
)
from sqlalchemy import func, select

from app.models import Booking

BOOKING_COLS = [
    "property_id",
    "arrival_date",
    "lead_time",
    "nights",
    "adr",
    "is_canceled",
    "market_segment",
    "deposit_type",
    "customer_type",
    "is_repeated_guest",
]


@pytest.fixture
def frames():
    """Due proprieta' da 2 camere, 6 prenotazioni, 5 giorni di soggiorno.

    Valide solo b1 (2 notti a 100) e b3 (3 notti a 50): 5 room-night, 350 euro,
    ADR pooled 70. b2/b6 cancellate, b4 nights=0, b5 adr=0: fuori dai KPI ma
    dentro cancellazioni e lead-time.
    """
    bookings = pd.DataFrame(
        [
            (1, "2016-01-10", 5, 2, 100.0, False, "Direct", "No Deposit", "Transient", False),
            (1, "2016-01-20", 40, 1, 200.0, True, "Online TA", "Non Refund", "Transient", False),
            (2, "2016-02-05", 100, 3, 50.0, False, "Online TA", "No Deposit", "Group", True),
            (2, "2016-02-15", 0, 0, 80.0, False, "Direct", "No Deposit", "Transient", False),
            (1, "2016-08-10", 200, 2, 0.0, False, "Direct", "No Deposit", "Transient", False),
            (2, "2016-08-20", 10, 1, 300.0, True, "Groups", "No Deposit", "Group", True),
        ],
        columns=BOOKING_COLS,
    )
    bookings["arrival_date"] = pd.to_datetime(bookings.arrival_date)
    daily = pd.DataFrame(
        [
            (1, "2016-01-10", 1, 100.0),
            (1, "2016-01-11", 1, 100.0),
            (2, "2016-02-05", 1, 50.0),
            (2, "2016-02-06", 1, 50.0),
            (2, "2016-02-07", 1, 50.0),
        ],
        columns=["property_id", "date", "room_nights", "revenue"],
    )
    daily["date"] = pd.to_datetime(daily.date)
    props = pd.DataFrame([(1, "Lago", 2), (2, "Montagna", 2)], columns=["id", "name", "room_count"])
    return bookings, daily, props


@pytest.mark.parametrize(
    ("days", "label"),
    [
        (0, "0-7"),
        (7, "0-7"),
        (8, "8-30"),
        (30, "8-30"),
        (31, "31-90"),
        (90, "31-90"),
        (91, "91-180"),
        (180, "91-180"),
        (181, ">180"),
        (400, ">180"),
    ],
)
def test_lead_bucket_confini(days, label):
    assert lead_bucket(days) == label


@pytest.mark.parametrize(
    ("occ", "label"),
    [
        (0.0, "<0.40"),
        (0.3999, "<0.40"),
        (0.4, "0.40-0.59"),
        (0.5999, "0.40-0.59"),
        (0.6, "0.60-0.79"),
        (0.7999, "0.60-0.79"),
        (0.8, ">=0.80"),
        (1.0, ">=0.80"),
    ],
)
def test_occupancy_bucket_confini(occ, label):
    assert occupancy_bucket(occ) == label


def test_pooled_adr_pesato_sulle_nights():
    df = pd.DataFrame({"adr": [100.0, 200.0], "nights": [1, 3]})
    assert pooled_adr(df) == 175.0  # (100*1 + 200*3) / 4, non la media semplice 150
    assert pooled_adr(pd.DataFrame({"adr": [], "nights": []})) is None


def test_baseline_metrics_filtri_e_cancellazioni(frames):
    bookings, _, _ = frames
    assert baseline_metrics(bookings) == {
        "rows": 6,
        "valid": 2,
        "room_nights": 5,
        "revenue": 350.0,
        "adr": 70.0,
        "median_adr_valid_rows": 75.0,
        "canceled": 2,
        "cancel_rate": 0.3333,  # 2/6 su TUTTE le righe, non sulle valide
    }


def test_stagionalita_medie_per_mese_dell_anno(frames):
    result = analyze(*frames)
    seas = result["seasonality"]
    assert [p["month"] for p in seas["combined"]] == [1, 2]
    gen, feb = seas["combined"]
    # gennaio: 2 giorni osservati, 1 room-night/giorno (media, non totale 2),
    # ricavo medio 100/giorno diviso 2 proprieta', occupazione 1/4 combinata
    assert gen["days_observed"] == 2
    assert gen["years_observed"] == [2016]
    assert gen["avg_room_nights"] == 1.0
    assert gen["avg_revenue"] == 50.0
    assert gen["avg_occupancy"] == 0.25
    assert gen["avg_adr"] == 100.0  # pooled sulla coorte di arrivi (b1)
    assert gen["valid_bookings"] == 1
    assert feb["avg_adr"] == 50.0
    assert feb["avg_occupancy"] == 0.25
    lago = seas["per_property"]["Lago"]
    assert lago[0]["avg_occupancy"] == 0.5  # 1 / 2 camere della proprieta'
    assert lago[0]["avg_revenue"] == 100.0  # per proprieta': nessuna divisione
    assert result["meta"]["capacity_assumed"] == {"Lago": 2, "Montagna": 2, "combined": 4}


def test_lead_buckets_cancellazioni_su_tutte_le_righe(frames):
    buckets = {b["bucket"]: b for b in analyze(*frames)["lead_time"]["buckets"]}
    assert buckets["0-7"]["n"] == 2  # b1 (lead 5) + b4 (lead 0, nights=0: resta nel denominatore)
    assert buckets["0-7"]["canceled"] == 0
    assert buckets["8-30"]["cancel_rate"] == 1.0  # b6 cancellata
    assert buckets["31-90"]["canceled"] == 1  # b2 cancellata
    assert buckets["91-180"]["n"] == 1  # b3
    assert buckets[">180"]["n"] == 1  # b5 (adr=0): esclusa dai KPI, non dalle cancellazioni


def test_canali_share_su_tutte_le_righe_e_kpi_sulle_valide(frames):
    ch = {c["market_segment"]: c for c in analyze(*frames)["channels"]}
    assert ch["Direct"]["bookings"] == 3
    assert ch["Direct"]["share"] == 0.5
    assert ch["Direct"]["valid_bookings"] == 1
    assert ch["Direct"]["revenue"] == 200.0
    assert ch["Direct"]["avg_adr"] == 100.0
    assert ch["Online TA"]["cancel_rate"] == 0.5  # b2 cancellata, b3 valida
    assert ch["Groups"]["revenue"] == 0.0  # solo b6, cancellata
    assert ch["Groups"]["avg_adr"] is None


def test_effetti_ospite_ripetuto_e_deposito(frames):
    effects = analyze(*frames)["guest_effects"]
    rep = {r["is_repeated_guest"]: r for r in effects["is_repeated_guest"]}
    assert rep[True]["n"] == 2
    assert rep[True]["cancel_rate"] == 0.5
    assert rep[False]["cancel_rate"] == 0.25
    dep = {r["deposit_type"]: r for r in effects["deposit_type"]}
    assert dep["Non Refund"]["cancel_rate"] == 1.0
    assert dep["No Deposit"]["n"] == 5


def test_adr_per_livello_occupazione(frames):
    ao = analyze(*frames)["adr_occupancy"]
    assert ao["daily_days_with_guests"] == 5
    bucket = ao["adr_by_occupancy_bucket"][0]
    assert bucket["bucket"] == "<0.40"
    assert bucket["days"] == 5
    assert bucket["adr_mean"] == 70.0  # (100+100+50+50+50) / 5
    assert ao["daily_corr_adr_occupancy"] is None  # occupazione costante: corr indefinita


def test_baseline_analisi_quadra_con_sql(conn):
    """Integrazione DB: baseline dell'analisi == aggregati SQL indipendenti."""
    bookings, daily, props = load_frames(conn)
    b = analyze(bookings, daily, props)["baseline"]
    valid = Booking.is_canceled.is_(False) & (Booking.nights > 0) & (Booking.adr > 0)
    rows, canceled = conn.execute(
        select(func.count(), func.count().filter(Booking.is_canceled))
    ).one()
    n_valid, room_nights, revenue = conn.execute(
        select(
            func.count(),
            func.coalesce(func.sum(Booking.nights), 0),
            func.coalesce(func.sum(Booking.adr * Booking.nights), 0),
        ).where(valid)
    ).one()
    assert b["rows"] == rows
    assert b["valid"] == n_valid
    assert b["room_nights"] == int(room_nights)
    assert b["revenue"] == round(float(revenue), 2)
    assert b["cancel_rate"] == round(canceled / rows, 4)
