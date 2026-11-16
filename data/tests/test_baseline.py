"""Baseline pulita come test (mitigazione R5): il seed deve riprodurre questi numeri.

Il campione e' committato → questo test gira sempre, anche in CI. Il CSV completo
e' solo locale (drive del cliente): il suo test si salta in CI, ma quello sul
campione resta eseguibile, quindi lo skip non puo' nascondere tutto (lezione T-1).
"""

import os

import pytest
from etl.load_bookings import clean

SAMPLE = dict(rows=5000, valid=3564, room_nights=12696, revenue=1350503.84)
FULL = dict(rows=87396, valid=61777, room_nights=218410, revenue=22976960.13)


def metrics(df):
    df = df.copy()
    df["nights"] = df.stays_in_weekend_nights + df.stays_in_week_nights
    v = df[(df.is_canceled == 0) & (df.nights > 0) & (df.adr > 0)]
    return dict(
        rows=len(df),
        valid=len(v),
        room_nights=int(v.nights.sum()),
        revenue=round(float((v.adr * v.nights).sum()), 2),
    )


def test_baseline_campione():
    assert metrics(clean("data/raw/sample_hotel_bookings.csv")) == SAMPLE


@pytest.mark.skipif(
    not os.path.exists("data/raw/hotel_bookings.csv"),
    reason="CSV completo solo locale (drive del cliente)",
)
def test_baseline_completo():
    assert metrics(clean("data/raw/hotel_bookings.csv")) == FULL
