import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app

# chiama l'app senza accendere il server
client = TestClient(app)


def test_properties(conn):
    r = client.get("/api/properties")
    assert r.status_code == 200
    hotels = r.json()["data"]
    assert len(hotels) == 2
    assert hotels[0]["name"] == "Buby Lago"
    assert hotels[1]["name"] == "Buby Montagna"
    assert hotels[0]["room_count"] == 190
    assert hotels[1]["room_count"] == 230
    # solo i campi del contratto
    campi = ["hotel_type", "id", "location_type", "name", "room_count", "ta_hotel_id"]
    assert sorted(hotels[0].keys()) == campi


def test_errore_404():
    r = client.get("/api/non-esiste")
    assert r.status_code == 404
    assert r.json() == {"error": {"code": "not_found", "message": "Resource not found."}}


def test_summary_campi(conn):
    r = client.get("/api/kpis/summary")
    assert r.status_code == 200
    campi = [
        "adr",
        "cancellation_rate",
        "date_from",
        "date_to",
        "occupancy_avg",
        "property_id",
        "revenue",
        "revpar",
        "room_nights",
        "valid_bookings",
    ]
    assert sorted(r.json().keys()) == campi


def test_summary_baseline_campione(conn):
    # numeri del campione da 5000 righe, scritti nel dizionario dei dati
    n = conn.execute(text("SELECT count(*) FROM bookings")).scalar()
    if n != 5000:
        pytest.skip("nel db non c'e' il campione da 5000 righe")
    s = client.get("/api/kpis/summary").json()
    assert s["valid_bookings"] == 3564
    assert s["room_nights"] == 12696
    assert s["revenue"] == 1350503.84
    assert s["cancellation_rate"] == 0.2696


def test_summary_lago_piu_montagna(conn):
    tutti = client.get("/api/kpis/summary").json()
    lago = client.get("/api/kpis/summary?property_id=1").json()
    montagna = client.get("/api/kpis/summary?property_id=2").json()
    assert lago["valid_bookings"] + montagna["valid_bookings"] == tutti["valid_bookings"]
    assert lago["room_nights"] + montagna["room_nights"] == tutti["room_nights"]
    assert round(lago["revenue"] + montagna["revenue"], 2) == tutti["revenue"]


def test_summary_periodo_vuoto(conn):
    # nessuna prenotazione nel 2014: deve dare 0, non andare in errore
    s = client.get("/api/kpis/summary?date_from=2014-01-01&date_to=2014-01-31").json()
    assert s["valid_bookings"] == 0
    assert s["adr"] == 0
    assert s["occupancy_avg"] == 0


def test_summary_hotel_che_non_esiste():
    r = client.get("/api/kpis/summary?property_id=3")
    assert r.status_code == 422
    assert "property_id" in r.json()["error"]["details"]


def test_summary_hotel_non_numero():
    r = client.get("/api/kpis/summary?property_id=abc")
    assert r.status_code == 422
    assert "property_id" in r.json()["error"]["details"]


def test_summary_data_sbagliata():
    r = client.get("/api/kpis/summary?date_from=ieri")
    assert r.status_code == 422
    assert "date_from" in r.json()["error"]["details"]


def test_summary_date_al_contrario():
    r = client.get("/api/kpis/summary?date_from=2017-01-01&date_to=2016-01-01")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_login_finto():
    r = client.post("/api/auth/login", json={"email": "manager@buby.travel", "password": "x"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert "access_token" in r.json()
    assert "role" in r.json()


def test_login_senza_password():
    r = client.post("/api/auth/login", json={"email": "manager@buby.travel"})
    assert r.status_code == 422
    assert "password" in r.json()["error"]["details"]


def test_daily_campi_e_pagine(conn):
    r = client.get("/api/kpis/daily?property_id=1&page_size=10")
    assert r.status_code == 200
    body = r.json()
    assert sorted(body.keys()) == ["data", "meta"]
    assert sorted(body["meta"].keys()) == ["page", "page_size", "total", "total_pages"]
    assert len(body["data"]) <= 10
    if body["data"]:
        campi = ["adr", "date", "occupancy", "revenue", "revenue_per_available_room", "room_nights"]
        assert sorted(body["data"][0].keys()) == campi


def test_daily_un_giorno_per_riga(conn):
    # anche con tutti e due gli hotel deve esserci una sola riga per giorno
    giorni = [p["date"] for p in client.get("/api/kpis/daily?page_size=200").json()["data"]]
    assert len(giorni) == len(set(giorni))
    assert giorni == sorted(giorni)


def test_daily_tutti_e_due_somma_i_due_hotel(conn):
    tutti = client.get("/api/kpis/daily?page_size=200").json()["data"]
    lago = client.get("/api/kpis/daily?property_id=1&page_size=200").json()["data"]
    montagna = client.get("/api/kpis/daily?property_id=2&page_size=200").json()["data"]
    notti = {}
    for p in lago + montagna:
        notti[p["date"]] = notti.get(p["date"], 0) + p["room_nights"]
    for p in tutti:
        if p["date"] in notti:
            assert p["room_nights"] == notti[p["date"]]


def test_daily_page_size_troppo_grande():
    r = client.get("/api/kpis/daily?page_size=500")
    assert r.status_code == 422
    assert "page_size" in r.json()["error"]["details"]


def test_daily_pagina_zero():
    r = client.get("/api/kpis/daily?page=0")
    assert r.status_code == 422
    assert "page" in r.json()["error"]["details"]
