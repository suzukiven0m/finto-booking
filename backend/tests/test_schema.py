import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from app.database import engine


@pytest.fixture(scope="module")
def conn():
    try:
        with engine.connect() as c:
            yield c
    except OperationalError:
        pytest.skip("db spento")


def test_ci_sono_tutte_le_tabelle(conn):
    tabelle = inspect(conn).get_table_names()
    for nome in ["properties", "bookings", "reviews", "guest_requests", "kpi_daily"]:
        assert nome in tabelle, f"manca la tabella {nome}"


def test_ci_sono_i_due_hotel(conn):
    nomi = conn.execute(text("SELECT name FROM properties ORDER BY id")).scalars().all()
    assert nomi == ["Buby Lago", "Buby Montagna"]


def test_colonne_principali(conn):
    attese = {
        "bookings": ["property_id", "arrival_date", "nights", "adr", "is_canceled"],
        "reviews": ["property_id", "booking_id", "score", "text", "sentiment", "topics"],
        "guest_requests": ["property_id", "received_at", "body", "category", "draft_reply", "status"],
        "kpi_daily": ["property_id", "date", "room_nights", "revenue", "occupancy"],
    }
    for tabella, colonne_attese in attese.items():
        colonne = [c["name"] for c in inspect(conn).get_columns(tabella)]
        for nome in colonne_attese:
            assert nome in colonne, f"in {tabella} manca la colonna {nome}"


def test_nights_calcolata_da_postgres(conn):
    sbagliate = conn.execute(text(
        "SELECT COUNT(*) FROM bookings "
        "WHERE nights <> stays_in_weekend_nights + stays_in_week_nights"
    )).scalar()
    assert sbagliate == 0


def test_kpi_daily_una_riga_per_hotel_e_giorno(conn):
    vincoli = inspect(conn).get_unique_constraints("kpi_daily")
    assert any(v["column_names"] == ["property_id", "date"] for v in vincoli)
