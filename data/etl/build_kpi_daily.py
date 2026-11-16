"""bookings -> kpi_daily. Legge dal DB, mai dal CSV. Idempotente.

Regola (docs/data-dictionary.md §3): ogni giorno di soggiorno di una prenotazione
valida (is_canceled=0, nights>0, adr>0) conta 1 room-night e adr di ricavo.
Invariante: somma(kpi_daily.revenue) == 22.976.960,13 e somma(room_nights) == 218.410.

Gira col venv del backend:  PYTHONPATH=backend backend/.venv/bin/python data/etl/build_kpi_daily.py
"""

import numpy as np
import pandas as pd
import psycopg
from sqlalchemy import create_engine

from app.config import DATABASE_URL

eng = create_engine(DATABASE_URL)
b = pd.read_sql(
    """SELECT property_id, arrival_date, nights, adr FROM bookings
       WHERE NOT is_canceled AND nights > 0 AND adr > 0""",
    eng,
)
# arrivals come date: senza questa conversione le somme con Timedelta restano
# object e pandas 4 le depreca (oltre a essere lente)
b["arrival_date"] = pd.to_datetime(b["arrival_date"])

rooms = pd.read_sql("SELECT id, room_count FROM properties", eng).set_index("id").room_count

b = b.reset_index(drop=True)
stay = b.loc[b.index.repeat(b.nights)].copy()
stay["date"] = stay.arrival_date + pd.to_timedelta(stay.groupby(level=0).cumcount(), unit="D")
daily = (
    stay.groupby(["property_id", "date"])
    .agg(room_nights=("adr", "size"), revenue=("adr", "sum"))
    .reset_index()
)

# tutto l'intervallo di date per proprieta', compresi i giorni a zero
parts = []
for pid, g in daily.groupby("property_id"):
    idx = pd.date_range(g.date.min(), g.date.max(), freq="D")
    g = g.set_index("date").reindex(idx, fill_value=0).rename_axis("date").reset_index()
    g["property_id"] = pid
    parts.append(g)
daily = pd.concat(parts, ignore_index=True)
daily["occupancy"] = daily.room_nights / daily.property_id.map(rooms)
daily["adr"] = np.where(
    daily.room_nights > 0, daily.revenue / daily.room_nights.replace(0, np.nan), np.nan
)
daily["revenue_per_available_room"] = daily.revenue / daily.property_id.map(rooms)
# ordine esplicito: e' quello della COPY e dell'unpack qui sotto
daily = daily[
    [
        "property_id",
        "date",
        "room_nights",
        "revenue",
        "occupancy",
        "adr",
        "revenue_per_available_room",
    ]
]

url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
with psycopg.connect(url) as conn, conn.cursor() as cur:
    cur.execute("TRUNCATE kpi_daily RESTART IDENTITY")
    with cur.copy(
        "COPY kpi_daily (property_id,date,room_nights,revenue,occupancy,"
        "adr,revenue_per_available_room) FROM STDIN"
    ) as cp:
        for row in daily.itertuples(index=False, name=None):
            pid, day, room_nights, revenue, occupancy, adr, rpar = row
            cp.write_row(
                [
                    pid,
                    day.date(),
                    int(room_nights),
                    float(revenue),
                    float(occupancy),
                    None if pd.isna(adr) else round(float(adr), 2),
                    round(float(rpar), 2),
                ]
            )
    conn.commit()
print(
    f"kpi_daily: {len(daily)} rows, revenue {daily.revenue.sum():.2f}, "
    f"room_nights {int(daily.room_nights.sum())}"
)
# full dataset must print: revenue 22976960.13, room_nights 218410
