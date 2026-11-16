"""CSV -> bookings. Dedup on the 32 colonne originali, poi load. Idempotente.

Gira col venv del backend:  PYTHONPATH=backend backend/.venv/bin/python data/etl/load_bookings.py
Argomento opzionale: path del csv (default data/raw/hotel_bookings.csv).
"""

import sys

import pandas as pd
import psycopg
from psycopg import sql

from app.config import DATABASE_URL  # run with backend/.venv + PYTHONPATH=backend

MONTHS = {
    m: i
    for i, m in enumerate(
        [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
        1,
    )
}

COLS = [
    "property_id",
    "arrival_date",
    "lead_time",
    "stays_in_weekend_nights",
    "stays_in_week_nights",
    "adults",
    "children",
    "babies",
    "country",
    "customer_type",
    "is_repeated_guest",
    "previous_cancellations",
    "previous_bookings_not_canceled",
    "market_segment",
    "distribution_channel",
    "agent",
    "company",
    "meal",
    "reserved_room_type",
    "assigned_room_type",
    "deposit_type",
    "booking_changes",
    "days_in_waiting_list",
    "required_car_parking_spaces",
    "total_of_special_requests",
    "adr",
    "is_canceled",
    "reservation_status_date",
]  # 28 colonne: niente id, niente nights (generata da postgres)


def clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)  # default NA: 'NA' e 'NULL' -> NaN (verificato)
    df = df.drop_duplicates()  # 32 colonne originali. MAI dedup dopo aver aggiunto colonne.
    df["children"] = df.children.fillna(0).astype(int)
    df["babies"] = df.babies.fillna(0).astype(int)
    df["property_id"] = df.hotel.map({"Resort Hotel": 1, "City Hotel": 2})
    df["arrival_date"] = pd.to_datetime(
        pd.DataFrame(
            {
                "year": df.arrival_date_year,
                "month": df.arrival_date_month.map(MONTHS),
                "day": df.arrival_date_day_of_month,
            }
        )
    ).dt.date
    df["reservation_status_date"] = pd.to_datetime(df.reservation_status_date).dt.date
    df["is_canceled"] = df.is_canceled.astype(bool)
    df["is_repeated_guest"] = df.is_repeated_guest.astype(bool)
    for c in ("agent", "company"):  # NaN -> None, altrimenti psycopg manda 'nan'
        df[c] = df[c].astype("Int64")
    return df.loc[:, COLS]


def _pg(v):
    # psycopg non sa adattare gli scalar di numpy: -> tipo python, NaN -> None
    if pd.isna(v):
        return None
    return v.item() if hasattr(v, "item") else v


def load(df: pd.DataFrame) -> None:
    url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE bookings RESTART IDENTITY")
        # sql.Identifier: COLS sono stringhe, senza Identifier psycopg le quota
        # come letterali ('property_id') e la COPY fallisce. Niente nights (generata).
        cols = sql.SQL(",").join(sql.Identifier(c) for c in COLS)
        stmt = sql.SQL("COPY bookings ({}) FROM STDIN").format(cols)
        with cur.copy(stmt) as cp:
            for row in df.itertuples(index=False, name=None):
                cp.write_row([_pg(v) for v in row])
        conn.commit()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/hotel_bookings.csv"
    df = clean(path)
    load(df)
    print(f"loaded {len(df)} rows from {path}")
