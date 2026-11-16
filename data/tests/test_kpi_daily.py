"""kpi_daily deve quadrare con le prenotazioni valide (qualunque dataset caricato).

Invariante del playbook §4.1: Σ revenue e Σ room_nights di kpi_daily uguagliano il
filtro baseline delle prenotazioni. Qui si verifica la relazione, non un numero
fisso, cosi' il test vale sia col campione (CI) sia col completo (locale).
"""

from sqlalchemy import and_, func, inspect, or_, select

from app.models import Booking, KpiDaily


def test_kpi_daily_quadra_con_bookings(conn):
    valid = Booking.is_canceled.is_(False) & (Booking.nights > 0) & (Booking.adr > 0)
    b = conn.execute(
        select(
            func.coalesce(func.sum(Booking.adr * Booking.nights), 0),
            func.coalesce(func.sum(Booking.nights), 0),
        ).where(valid)
    ).one()
    k = conn.execute(
        select(
            func.coalesce(func.sum(KpiDaily.revenue), 0),
            func.coalesce(func.sum(KpiDaily.room_nights), 0),
        )
    ).one()
    assert round(float(k[0]), 2) == round(float(b[0]), 2)
    assert int(k[1]) == int(b[1])


def test_occupancy_precision_4_decimali(conn):
    # migrazione 0004: numeric(5,4), non (5,2) che quantizzava a 1 punto percentuale
    col = {c["name"]: c for c in inspect(conn).get_columns("kpi_daily")}["occupancy"]
    assert (col["type"].precision, col["type"].scale) == (5, 4)


def test_occupancy_rapporto_0_1(conn):
    vals = conn.execute(select(KpiDaily.occupancy)).scalars().all()
    assert vals
    assert all(0 <= float(v) <= 1 for v in vals)


def test_adr_null_solo_nei_giorni_senza_attivita(conn):
    bad = conn.execute(
        select(func.count())
        .select_from(KpiDaily)
        .where(
            or_(
                and_(KpiDaily.room_nights == 0, KpiDaily.adr.is_not(None)),
                and_(KpiDaily.room_nights > 0, KpiDaily.adr.is_(None)),
            )
        )
    ).scalar()
    assert bad == 0
