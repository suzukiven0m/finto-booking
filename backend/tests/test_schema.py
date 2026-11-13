from datetime import UTC, datetime

import pytest
from sqlalchemy import func, insert, inspect, select
from sqlalchemy.exc import IntegrityError

from app.models import Booking, GuestRequest, Property


def test_ci_sono_tutte_le_tabelle(conn):
    tabelle = inspect(conn).get_table_names()
    for nome in ["properties", "bookings", "reviews", "guest_requests", "kpi_daily"]:
        assert nome in tabelle, f"manca la tabella {nome}"


def test_ci_sono_i_due_hotel(conn):
    # i due hotel li inserisce la 0001 con bulk_insert
    righe = conn.execute(
        select(
            Property.name, Property.hotel_type, Property.location_type, Property.room_count
        ).order_by(Property.id)
    ).all()
    assert [tuple(r) for r in righe] == [
        ("Buby Lago", "Resort Hotel", "lake", 190),
        ("Buby Montagna", "City Hotel", "mountain", 230),
    ]


def test_colonne_principali(conn):
    attese = {
        "bookings": ["property_id", "arrival_date", "nights", "adr", "is_canceled"],
        "reviews": [
            "property_id",
            "ta_hotel_id",
            "post_date",
            "stay_year",
            "overall",
            "cleanliness",
            "value",
            "location",
            "rooms",
            "sleep_quality",
            "title",
            "body",
            "lang",
        ],
        "guest_requests": [
            "property_id",
            "received_at",
            "body",
            "category",
            "draft_reply",
            "status",
        ],
        "kpi_daily": ["property_id", "date", "room_nights", "revenue", "occupancy"],
    }
    for tabella, colonne_attese in attese.items():
        colonne = [c["name"] for c in inspect(conn).get_columns(tabella)]
        for nome in colonne_attese:
            assert nome in colonne, f"in {tabella} manca la colonna {nome}"


def test_nights_calcolata_da_postgres(conn):
    sbagliate = conn.execute(
        select(func.count())
        .select_from(Booking)
        .where(Booking.nights != Booking.stays_in_weekend_nights + Booking.stays_in_week_nights)
    ).scalar()
    assert sbagliate == 0


def test_kpi_daily_una_riga_per_hotel_e_giorno(conn):
    vincoli = inspect(conn).get_unique_constraints("kpi_daily")
    assert any(v["column_names"] == ["property_id", "date"] for v in vincoli)


def test_reviews_legano_per_proprieta_non_per_prenotazione(conn):
    # ADR 0003 §3: "nessuna chiave esterna verso bookings"
    fk = inspect(conn).get_foreign_keys("reviews")
    assert [f["referred_table"] for f in fk] == ["properties"]


def test_reviews_non_contiene_output_del_modello(conn):
    # sentiment e topics sono output di D14, non dati di TripAdvisor: stanno
    # in una tabella derivata, non nella sorgente
    colonne = {c["name"] for c in inspect(conn).get_columns("reviews")}
    assert not colonne & {"sentiment", "topics", "booking_id", "reviewer_nationality"}


def test_properties_ha_ta_hotel_id(conn):
    # ADR 0003 §1: serve per la tabella di mappatura proprietà
    colonne = {c["name"] for c in inspect(conn).get_columns("properties")}
    assert "ta_hotel_id" in colonne


def test_ogni_foreign_key_ha_un_indice(conn):
    # Postgres non indicizza le FK da solo: senza indice i filtri per hotel
    # vanno in seq-scan. Un indice unico sulla colonna conta come copertura.
    insp = inspect(conn)
    mancanti = []
    for tabella in insp.get_table_names():
        if tabella == "alembic_version":
            continue
        coperte = {tuple(i["column_names"][:1]) for i in insp.get_indexes(tabella)}
        coperte |= {tuple(u["column_names"][:1]) for u in insp.get_unique_constraints(tabella)}
        for fk in insp.get_foreign_keys(tabella):
            prima = tuple(fk["constrained_columns"][:1])
            if prima not in coperte:
                mancanti.append(f"{tabella}.{fk['constrained_columns'][0]}")
    assert mancanti == [], f"foreign key senza indice: {mancanti}"


@pytest.mark.parametrize(
    "tabella, valori",
    [
        # i CHECK li crea la 0003: qui proviamo che rifiutino davvero.
        # room_count c'e' perche' e' NOT NULL: senza, l'errore sarebbe il NOT NULL
        # e non il CHECK che vogliamo testare.
        (
            Property,
            {
                "name": "X",
                "hotel_type": "City Hotel",
                "location_type": "deserto",
                "room_count": 10,
            },
        ),
        (
            GuestRequest,
            {"property_id": 1, "received_at": datetime.now(UTC), "body": "x", "status": "boh"},
        ),
    ],
    ids=["location_type", "status"],
)
def test_i_vocabolari_chiusi_rifiutano_spazzatura(conn, tabella, valori):
    with pytest.raises(IntegrityError):
        conn.execute(insert(tabella).values(**valori))
    conn.rollback()
