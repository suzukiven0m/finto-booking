"""Contract test WP8: le risposte delle 11 operazioni validate contro openapi.yaml.

Approccio hand-rolled (PyYAML + jsonschema): schemathesis farebbe fuzzing con
PATCH di scrittura sul DB seedato e aggiunge una dipendenza pesante; questa
validazione e' deterministica, copre tutte le 11 operazioni e gira in CI sul
campione. I numeri pinned sul dataset completo si saltano sul campione BY DESIGN
(stesso pattern di test_api.py / test_auth.py).
"""

import math
from datetime import date, datetime
from pathlib import Path

import jsonschema
import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy import Integer, and_, cast, func, select, update
from sqlalchemy.orm import Session

from app.config import DEMO_USERS
from app.main import app
from app.models import Booking, GuestRequest, KpiDaily, Review

ROOT = Path(__file__).resolve().parents[2]
SPEC = yaml.safe_load((ROOT / "openapi.yaml").read_text())

client = TestClient(app)
# password demo dalla config: niente literal nel test (secret scanner CI)
DEMO_PASSWORD = DEMO_USERS["manager@buby.travel"]["password"]


def bearer(email):
    r = client.post("/api/auth/login", json={"email": email, "password": DEMO_PASSWORD})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


HEAD_MANAGER = bearer("manager@buby.travel")
HEAD_ADMIN = bearer("admin@buby.travel")
HEAD_PROPERTY = bearer("property.manager@buby.travel")

ENVELOPE_401 = {"error": {"code": "unauthorized", "message": "Missing or invalid bearer token."}}
ENVELOPE_403 = {
    "error": {"code": "forbidden", "message": "Your role is not allowed to perform this action."}
}
ENVELOPE_404 = {"error": {"code": "not_found", "message": "Resource not found."}}

# regola della baseline (dizionario dati §3), riscritta qui per indipendenza
VALIDA = and_(Booking.is_canceled.is_(False), Booking.nights > 0, Booking.adr > 0)

FORMAT_CHECKER = jsonschema.FormatChecker()


@FORMAT_CHECKER.checks("date-time")
def _date_time(value):
    # jsonschema senza extra non ha il checker date-time: ISO 8601 basta e avanza
    if not isinstance(value, str):
        return True
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def risolvi(nodo):
    # $ref interni inlineati + nullable OpenAPI 3.0 -> type jsonschema
    if isinstance(nodo, dict):
        if "$ref" in nodo:
            target = SPEC
            for parte in nodo["$ref"][2:].split("/"):
                target = target[parte]
            return risolvi(target)
        out = {k: risolvi(v) for k, v in nodo.items() if k != "nullable"}
        if nodo.get("nullable") is True and isinstance(out.get("type"), str):
            out["type"] = [out["type"], "null"]
        return out
    if isinstance(nodo, list):
        return [risolvi(x) for x in nodo]
    return nodo


def valida(body, nome_schema):
    schema = risolvi(SPEC["components"]["schemas"][nome_schema])
    assert isinstance(schema, dict)
    jsonschema.validate(body, schema, format_checker=FORMAT_CHECKER)


def assert_errore(r, status, code):
    assert r.status_code == status
    body = r.json()
    valida(body, "Error")
    assert body["error"]["code"] == code


@pytest.fixture
def db(conn):
    # riusa il fixture conn (skip locale / fail in CI se il DB e' giu'),
    # ma le query passano dall'ORM: tutto bindato. Una sessione per test:
    # un errore non deve avvelenare la transazione dei test successivi.
    with Session(bind=conn) as session:
        yield session
        session.rollback()


def solo_db_pieno(db):
    n = db.execute(select(func.count()).select_from(Booking)).scalar_one()
    if n != 87396:
        pytest.skip("nel db non c'e' il dataset completo da 87396 righe")


# --- operazioni aperte: properties e login ---------------------------------


def test_properties_schema_ed_esempio_pinned(db):
    r = client.get("/api/properties")
    assert r.status_code == 200
    valida(r.json(), "PropertyList")
    esempio = SPEC["paths"]["/api/properties"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["example"]
    assert r.json() == esempio


def test_login_schema():
    r = client.post(
        "/api/auth/login", json={"email": "manager@buby.travel", "password": DEMO_PASSWORD}
    )
    assert r.status_code == 200
    valida(r.json(), "LoginResponse")
    assert r.json()["role"] == "manager"
    assert r.json()["token_type"] == "bearer"


def test_login_401_invalid_credentials():
    r = client.post(
        "/api/auth/login",
        json={"email": "manager@buby.travel", "password": DEMO_PASSWORD + "-sbagliata"},
    )
    assert r.status_code == 401
    assert r.json() == {
        "error": {"code": "invalid_credentials", "message": "Email or password is incorrect."}
    }
    valida(r.json(), "Error")


def test_login_422_senza_password():
    r = client.post("/api/auth/login", json={"email": "manager@buby.travel"})
    assert_errore(r, 422, "validation_error")
    assert "password" in r.json()["error"]["details"]


# --- 401 su tutte le rotte protette -----------------------------------------

ROTTE_PROTETTE = [
    "/api/kpis/summary",
    "/api/kpis/daily",
    "/api/kpis/channels",
    "/api/kpis/seasonality",
    "/api/reviews/summary",
    "/api/reviews",
    "/api/bookings",
    "/api/guest-requests",
]


@pytest.mark.parametrize("path", ROTTE_PROTETTE)
@pytest.mark.parametrize("token_spazzatura", [None, "patacca"])
def test_get_protetti_401(path, token_spazzatura):
    headers = {} if token_spazzatura is None else {"Authorization": f"Bearer {token_spazzatura}"}
    r = client.get(path, headers=headers)
    assert r.status_code == 401
    assert r.json() == ENVELOPE_401
    valida(r.json(), "Error")


# --- KPI: summary e daily (operazioni gia' esistenti, validazione contratto) --


def test_summary_schema(db):
    r = client.get("/api/kpis/summary", headers=HEAD_MANAGER)
    assert r.status_code == 200
    valida(r.json(), "KpiSummary")


def test_summary_esempio_pinned_db_pieno(db):
    solo_db_pieno(db)
    r = client.get("/api/kpis/summary", headers=HEAD_MANAGER)
    assert r.status_code == 200
    # tutti i 10 campi dell'esempio pinned, non solo i 7 numerici
    assert r.json() == SPEC["components"]["schemas"]["KpiSummary"]["example"]


def test_daily_schema_e_meta(db):
    r = client.get("/api/kpis/daily?page_size=10", headers=HEAD_MANAGER)
    assert r.status_code == 200
    body = r.json()
    valida(body, "KpiDailyPage")
    meta = body["meta"]
    assert meta["total_pages"] == math.ceil(meta["total"] / meta["page_size"])
    assert len(body["data"]) <= meta["page_size"]
    date = [p["date"] for p in body["data"]]
    assert date == sorted(date)


# --- KPI: channels -----------------------------------------------------------


def test_channels_schema(db):
    r = client.get("/api/kpis/channels", headers=HEAD_MANAGER)
    assert r.status_code == 200
    valida(r.json(), "ChannelMixList")


def test_channels_share_e_totale_validi(db):
    # share = frazione delle PRENOTAZIONI valide, non del ricavo (schema)
    r = client.get("/api/kpis/channels", headers=HEAD_MANAGER)
    dati = r.json()["data"]
    totale = db.execute(select(func.count()).select_from(Booking).where(VALIDA)).scalar_one()
    ricavo = db.execute(
        select(func.sum(Booking.adr * Booking.nights)).select_from(Booking).where(VALIDA)
    ).scalar_one()
    assert sum(c["bookings"] for c in dati) == totale
    assert round(sum(c["revenue"] for c in dati), 2) == round(float(ricavo), 2)
    for c in dati:
        assert c["share"] == round(c["bookings"] / totale, 4)


def test_channels_numeri_db_pieno(db):
    solo_db_pieno(db)
    r = client.get("/api/kpis/channels", headers=HEAD_MANAGER)
    dati = {c["market_segment"]: c for c in r.json()["data"]}
    # Undefined ha 0 prenotazioni valide: sparisce dalla lista (7 segmenti)
    attesi = {
        "Online TA": (33040, 12973686.94),
        "Offline TA/TO": (11597, 4595718.77),
        "Direct": (9866, 3927104.69),
        "Groups": (3406, 922928.01),
        "Corporate": (3633, 483748.83),
        "Aviation": (178, 68968.36),
        "Complementary": (57, 4804.53),
    }
    assert set(dati) == set(attesi)
    for segmento, (bookings, revenue) in attesi.items():
        assert dati[segmento]["bookings"] == bookings
        assert dati[segmento]["revenue"] == revenue
    assert sum(c["bookings"] for c in dati.values()) == 61777
    assert round(sum(c["revenue"] for c in dati.values()), 2) == 22976960.13


def test_channels_filtri(db):
    r = client.get(
        "/api/kpis/channels?property_id=1&date_from=2016-01-01&date_to=2016-12-31",
        headers=HEAD_MANAGER,
    )
    assert r.status_code == 200
    valida(r.json(), "ChannelMixList")
    atteso = db.execute(
        select(func.count())
        .select_from(Booking)
        .where(
            VALIDA,
            Booking.property_id == 1,
            Booking.arrival_date.between(date(2016, 1, 1), date(2016, 12, 31)),
        )
    ).scalar_one()
    assert sum(c["bookings"] for c in r.json()["data"]) == atteso


def test_channels_finestra_vuota(db):
    r = client.get(
        "/api/kpis/channels?date_from=2014-01-01&date_to=2014-01-31", headers=HEAD_MANAGER
    )
    assert r.status_code == 200
    assert r.json() == {"data": []}
    valida(r.json(), "ChannelMixList")


# --- KPI: seasonality --------------------------------------------------------


def test_seasonality_schema_12_mesi(db):
    r = client.get("/api/kpis/seasonality", headers=HEAD_MANAGER)
    assert r.status_code == 200
    body = r.json()
    valida(body, "SeasonalityList")
    assert [p["month"] for p in body["data"]] == list(range(1, 13))


def test_seasonality_numeri_db_pieno(db):
    solo_db_pieno(db)
    r = client.get("/api/kpis/seasonality", headers=HEAD_MANAGER)
    punti = {p["month"]: p for p in r.json()["data"]}
    # ground truth: entrambi gli hotel, avg_revenue = media delle somme / 2
    gennaio = {"month": 1, "avg_adr": 69.98, "avg_occupancy": 0.3982, "avg_revenue": 6149.95}
    agosto = {"month": 8, "avg_adr": 151.00, "avg_occupancy": 0.7810, "avg_revenue": 25029.60}
    assert punti[1] == gennaio
    assert punti[8] == agosto


def test_seasonality_proprieta_singola(db):
    # singola proprieta': media dell'occupancy SALVATA e del ricavo giornaliero
    r = client.get("/api/kpis/seasonality?property_id=1", headers=HEAD_MANAGER)
    assert r.status_code == 200
    valida(r.json(), "SeasonalityList")
    mese = cast(func.extract("month", KpiDaily.date), Integer)
    righe = db.execute(
        select(mese, func.avg(KpiDaily.occupancy), func.avg(KpiDaily.revenue))
        .where(KpiDaily.property_id == 1)
        .group_by(mese)
    ).all()
    attesi = {m: (round(float(o), 4), round(float(v), 2)) for m, o, v in righe}
    for p in r.json()["data"]:
        occupancy, ricavo = attesi.get(p["month"], (0.0, 0.0))
        assert p["avg_occupancy"] == occupancy
        assert p["avg_revenue"] == ricavo


# --- reviews -----------------------------------------------------------------


@pytest.mark.parametrize("property_id", [1, 2, None])
def test_reviews_summary_schema(db, property_id):
    url = "/api/reviews/summary"
    if property_id is not None:
        url += f"?property_id={property_id}"
    r = client.get(url, headers=HEAD_MANAGER)
    assert r.status_code == 200
    valida(r.json(), "ReviewSummary")
    assert r.json()["property_id"] == property_id


@pytest.mark.parametrize("property_id", [1, 2, None])
def test_reviews_summary_pinned(db, property_id):
    # il corpus TripAdvisor e' lo stesso in CI e sul DB pieno (1638 righe)
    n = db.execute(select(func.count()).select_from(Review)).scalar_one()
    if n != 1638:
        pytest.skip("nel db non c'e' il corpus completo da 1638 recensioni")
    url = "/api/reviews/summary"
    if property_id is not None:
        url += f"?property_id={property_id}"
    body = client.get(url, headers=HEAD_MANAGER).json()
    if property_id is not None:
        # tutti e 7 i campi, uguali agli esempi del contratto (WP8a: corretti
        # pre-freeze alle medie reali del corpus, verificate per esecuzione)
        esempi = SPEC["paths"]["/api/reviews/summary"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["examples"]
        nome = "bubyLago" if property_id == 1 else "bubyMontagna"
        assert body == esempi[nome]["value"]
    else:
        # null = media su TUTTE le righe: ponderata per count, non media
        # delle medie per proprieta'
        assert body == {
            "property_id": None,
            "count": 1638,
            "overall": 4.15,
            "cleanliness": 4.39,
            "value": 3.88,
            "location": 4.54,
            "rooms": 4.05,
            "sleep_quality": 4.17,
        }


def test_reviews_schema_ordine_e_meta(db):
    r = client.get("/api/reviews?page_size=20", headers=HEAD_MANAGER)
    assert r.status_code == 200
    body = r.json()
    valida(body, "ReviewPage")
    date = [p["post_date"] for p in body["data"]]
    assert date == sorted(date, reverse=True)  # newest first by post_date
    meta = body["meta"]
    assert meta["total"] == db.execute(select(func.count()).select_from(Review)).scalar_one()
    assert meta["total_pages"] == math.ceil(meta["total"] / meta["page_size"])
    # niente sentiment/topics (D14): solo i campi del contratto
    campi = set(SPEC["components"]["schemas"]["Review"]["properties"])
    for p in body["data"]:
        assert set(p) == campi


def test_reviews_filtro_proprieta(db):
    r = client.get("/api/reviews?property_id=2&page_size=200", headers=HEAD_MANAGER)
    assert r.status_code == 200
    body = r.json()
    assert all(p["property_id"] == 2 for p in body["data"])
    atteso = db.execute(
        select(func.count()).select_from(Review).where(Review.property_id == 2)
    ).scalar_one()
    assert body["meta"]["total"] == atteso


# --- bookings ----------------------------------------------------------------


def test_bookings_schema_ordine_e_meta(db):
    r = client.get("/api/bookings?page_size=20", headers=HEAD_MANAGER)
    assert r.status_code == 200
    body = r.json()
    valida(body, "BookingPage")
    arrivi = [p["arrival_date"] for p in body["data"]]
    assert arrivi == sorted(arrivi)  # ordered by arrival_date
    assert (
        body["meta"]["total"] == db.execute(select(func.count()).select_from(Booking)).scalar_one()
    )
    campi = set(SPEC["components"]["schemas"]["Booking"]["properties"])
    for p in body["data"]:
        assert set(p) == campi


def test_bookings_filtri(db):
    r = client.get(
        "/api/bookings?property_id=1&is_canceled=true&market_segment=Online TA"
        "&date_from=2016-01-01&date_to=2016-12-31&page_size=200",
        headers=HEAD_MANAGER,
    )
    assert r.status_code == 200
    body = r.json()
    valida(body, "BookingPage")
    for p in body["data"]:
        assert p["property_id"] == 1
        assert p["is_canceled"] is True
        assert p["market_segment"] == "Online TA"
        assert "2016-01-01" <= p["arrival_date"] <= "2016-12-31"
    atteso = db.execute(
        select(func.count())
        .select_from(Booking)
        .where(
            Booking.property_id == 1,
            Booking.is_canceled.is_(True),
            Booking.market_segment == "Online TA",
            Booking.arrival_date.between(date(2016, 1, 1), date(2016, 12, 31)),
        )
    ).scalar_one()
    assert body["meta"]["total"] == atteso


# --- guest-requests: inbox ---------------------------------------------------


def test_guest_requests_schema_ordine_e_meta(db):
    r = client.get("/api/guest-requests?page_size=20", headers=HEAD_MANAGER)
    assert r.status_code == 200
    body = r.json()
    valida(body, "GuestRequestPage")
    ricevuti = [p["received_at"] for p in body["data"]]
    assert ricevuti == sorted(ricevuti, reverse=True)  # newest first by received_at
    assert (
        body["meta"]["total"]
        == db.execute(select(func.count()).select_from(GuestRequest)).scalar_one()
    )
    campi = set(SPEC["components"]["schemas"]["GuestRequest"]["properties"])
    _valid_cats = {
        "availability",
        "cancellation",
        "complaint",
        "special_request",
        "billing",
        "info",
    }
    for p in body["data"]:
        # urgency (0005) non e' nel contratto: mai esposta
        assert set(p) == campi
        # post-D15 (WP10): category e draft_reply sono compilate dal classificatore
        assert p["category"] in _valid_cats
        assert isinstance(p["draft_reply"], str) and p["draft_reply"]


def test_guest_requests_filtro_status(db):
    r = client.get("/api/guest-requests?status=new&page_size=1", headers=HEAD_MANAGER)
    assert r.status_code == 200
    atteso = db.execute(
        select(func.count()).select_from(GuestRequest).where(GuestRequest.status == "new")
    ).scalar_one()
    assert r.json()["meta"]["total"] == atteso
    r = client.get("/api/guest-requests?status=boh", headers=HEAD_MANAGER)
    assert_errore(r, 422, "validation_error")
    assert "status" in r.json()["error"]["details"]


# --- guest-requests: PATCH (HITL) --------------------------------------------


@pytest.fixture
def riga_guest(db):
    # snapshot della riga 1 e ripristino a fine test: il DB seedato deve
    # finire come ha iniziato (accettazione WP8: 0 mutazioni)
    originale = db.execute(
        select(
            GuestRequest.status,
            GuestRequest.draft_reply,
            GuestRequest.category,
            GuestRequest.urgency,
        ).where(GuestRequest.id == 1)
    ).one()
    yield 1
    db.execute(
        update(GuestRequest)
        .where(GuestRequest.id == 1)
        .values(
            status=originale[0],
            draft_reply=originale[1],
            category=originale[2],
            urgency=originale[3],
        )
    )
    db.commit()


@pytest.fixture
def riga_new(db):
    """Forza riga 1 a status='new', ripristina lo stato originale a fine test (P1)."""
    originale = db.execute(
        select(
            GuestRequest.status,
            GuestRequest.draft_reply,
            GuestRequest.category,
            GuestRequest.urgency,
        ).where(GuestRequest.id == 1)
    ).one()
    db.execute(update(GuestRequest).where(GuestRequest.id == 1).values(status="new"))
    db.commit()
    yield 1
    db.execute(
        update(GuestRequest)
        .where(GuestRequest.id == 1)
        .values(
            status=originale[0],
            draft_reply=originale[1],
            category=originale[2],
            urgency=originale[3],
        )
    )
    db.commit()


def test_patch_transizioni_da_new(riga_new):
    """Matrice da status='new': new->new 422, new->sent 422, new->draft 200+schema."""
    url = f"/api/guest-requests/{riga_new}"

    # new->new: ciclo vietato
    r = client.patch(url, json={"status": "new"}, headers=HEAD_MANAGER)
    assert_errore(r, 422, "validation_error")

    # new->sent: salta draft, vietato dal HITL workflow
    r = client.patch(url, json={"status": "sent"}, headers=HEAD_MANAGER)
    assert_errore(r, 422, "validation_error")

    # new->draft: happy path (lo stato e' ancora 'new' perche' i due PATCH sopra fallirono)
    r = client.patch(
        url,
        json={"status": "draft", "draft_reply": "Bozza da new."},
        headers=HEAD_MANAGER,
    )
    assert r.status_code == 200
    valida(r.json(), "GuestRequest")
    assert r.json()["status"] == "draft"
    assert r.json()["draft_reply"] == "Bozza da new."


def test_patch_draft_to_draft_schema(riga_guest):
    r = client.patch(
        f"/api/guest-requests/{riga_guest}",
        json={"status": "draft", "draft_reply": "Bozza di prova."},
        headers=HEAD_MANAGER,
    )
    assert r.status_code == 200
    valida(r.json(), "GuestRequest")
    body = r.json()
    assert body["status"] == "draft"
    assert body["draft_reply"] == "Bozza di prova."
    # post-D15 (WP10): category e' impostata dal classificatore, non scrivibile via PATCH
    _valid_cats = {
        "availability",
        "cancellation",
        "complaint",
        "special_request",
        "billing",
        "info",
    }
    assert body["category"] in _valid_cats


def test_patch_draft_to_sent(riga_guest):
    url = f"/api/guest-requests/{riga_guest}"
    assert client.patch(url, json={"status": "draft"}, headers=HEAD_MANAGER).status_code == 200
    r = client.patch(url, json={"status": "sent"}, headers=HEAD_MANAGER)
    assert r.status_code == 200
    valida(r.json(), "GuestRequest")
    assert r.json()["status"] == "sent"


def test_patch_draft_edit(riga_guest):
    url = f"/api/guest-requests/{riga_guest}"
    client.patch(url, json={"status": "draft", "draft_reply": "prima bozza"}, headers=HEAD_MANAGER)
    r = client.patch(
        url, json={"status": "draft", "draft_reply": "bozza modificata"}, headers=HEAD_MANAGER
    )
    assert r.status_code == 200
    assert r.json()["status"] == "draft"
    assert r.json()["draft_reply"] == "bozza modificata"


def test_patch_solo_draft_reply(riga_guest):
    r = client.patch(
        f"/api/guest-requests/{riga_guest}",
        json={"draft_reply": "solo bozza"},
        headers=HEAD_MANAGER,
    )
    assert r.status_code == 200
    # post-D15 (WP10): lo stato iniziale di riga 1 e' 'draft' (non 'new');
    # PATCH senza status non fa transizione implicita
    assert r.json()["status"] == "draft"  # nessuna transizione implicita
    assert r.json()["draft_reply"] == "solo bozza"


@pytest.mark.parametrize("obbiettivo", ["new"])
def test_patch_da_draft_non_verso_new(riga_guest, obbiettivo):
    # post-D15 (WP10): lo stato iniziale e' 'draft'; draft->new e' una retrogressione vietata.
    # draft->sent e' un passo HITL valido (rimosso dalla parametrize).
    r = client.patch(
        f"/api/guest-requests/{riga_guest}", json={"status": obbiettivo}, headers=HEAD_MANAGER
    )
    assert_errore(r, 422, "validation_error")


def test_patch_indietro_da_draft_422(riga_guest):
    url = f"/api/guest-requests/{riga_guest}"
    client.patch(url, json={"status": "draft"}, headers=HEAD_MANAGER)
    r = client.patch(url, json={"status": "new"}, headers=HEAD_MANAGER)
    assert_errore(r, 422, "validation_error")


@pytest.mark.parametrize("status", ["new", "draft", "sent"])
def test_patch_da_sent_terminale_422(riga_guest, status):
    url = f"/api/guest-requests/{riga_guest}"
    client.patch(url, json={"status": "draft"}, headers=HEAD_MANAGER)
    client.patch(url, json={"status": "sent"}, headers=HEAD_MANAGER)
    r = client.patch(url, json={"status": status}, headers=HEAD_MANAGER)
    assert_errore(r, 422, "validation_error")


def test_patch_solo_draft_reply_su_sent_422(riga_guest):
    url = f"/api/guest-requests/{riga_guest}"
    client.patch(url, json={"status": "draft"}, headers=HEAD_MANAGER)
    client.patch(url, json={"status": "sent"}, headers=HEAD_MANAGER)
    r = client.patch(url, json={"draft_reply": "altra bozza"}, headers=HEAD_MANAGER)
    assert_errore(r, 422, "validation_error")


def test_patch_admin_passa(riga_guest):
    r = client.patch(
        f"/api/guest-requests/{riga_guest}", json={"status": "draft"}, headers=HEAD_ADMIN
    )
    assert r.status_code == 200
    assert r.json()["status"] == "draft"


def test_patch_property_manager_403(riga_guest):
    r = client.patch(
        f"/api/guest-requests/{riga_guest}", json={"status": "draft"}, headers=HEAD_PROPERTY
    )
    assert r.status_code == 403
    assert r.json() == ENVELOPE_403
    valida(r.json(), "Error")


@pytest.mark.parametrize("token_spazzatura", [None, "patacca"])
def test_patch_401(riga_guest, token_spazzatura):
    headers = {} if token_spazzatura is None else {"Authorization": f"Bearer {token_spazzatura}"}
    r = client.patch(f"/api/guest-requests/{riga_guest}", json={"status": "draft"}, headers=headers)
    assert r.status_code == 401
    assert r.json() == ENVELOPE_401
    valida(r.json(), "Error")


def test_patch_id_sconosciuto_404(db):
    id_assente = db.execute(select(func.max(GuestRequest.id) + 1)).scalar_one()
    r = client.patch(
        f"/api/guest-requests/{id_assente}", json={"status": "draft"}, headers=HEAD_MANAGER
    )
    assert r.status_code == 404
    assert r.json() == ENVELOPE_404
    valida(r.json(), "Error")


def test_patch_status_non_valido_422(riga_guest):
    r = client.patch(
        f"/api/guest-requests/{riga_guest}", json={"status": "boh"}, headers=HEAD_MANAGER
    )
    assert_errore(r, 422, "validation_error")
    assert "status" in r.json()["error"]["details"]


@pytest.mark.parametrize("body", [{}, {"status": None}, {"draft_reply": None}])
def test_patch_body_non_valido_422(riga_guest, body):
    # minProperties: 1 e niente null espliciti (schema non nullable)
    r = client.patch(f"/api/guest-requests/{riga_guest}", json=body, headers=HEAD_MANAGER)
    assert_errore(r, 422, "validation_error")


@pytest.mark.parametrize("id_non_valido", ["0", "abc"])
def test_patch_id_non_valido_422(id_non_valido):
    r = client.patch(
        f"/api/guest-requests/{id_non_valido}", json={"status": "draft"}, headers=HEAD_MANAGER
    )
    assert_errore(r, 422, "validation_error")


# --- limiti di paginazione e validazione input -------------------------------

PAGINATE = ["/api/kpis/daily", "/api/reviews", "/api/bookings", "/api/guest-requests"]


@pytest.mark.parametrize("path", PAGINATE)
@pytest.mark.parametrize("query", ["page=0", "page_size=0", "page_size=201", "page_size=abc"])
def test_paginazione_limiti_422(path, query):
    r = client.get(f"{path}?{query}", headers=HEAD_MANAGER)
    assert_errore(r, 422, "validation_error")
    assert query.split("=")[0] in r.json()["error"]["details"]


@pytest.mark.parametrize(
    "path",
    [
        "/api/kpis/channels",
        "/api/kpis/seasonality",
        "/api/reviews/summary",
        "/api/reviews",
        "/api/bookings",
        "/api/guest-requests",
    ],
)
def test_property_id_non_valido_422(path):
    r = client.get(f"{path}?property_id=3", headers=HEAD_MANAGER)
    assert_errore(r, 422, "validation_error")
    assert "property_id" in r.json()["error"]["details"]


@pytest.mark.parametrize("path", ["/api/kpis/channels", "/api/bookings"])
def test_date_al_contrario_422(path):
    r = client.get(f"{path}?date_from=2017-01-01&date_to=2016-01-01", headers=HEAD_MANAGER)
    assert_errore(r, 422, "validation_error")


@pytest.mark.parametrize("path", ["/api/kpis/channels", "/api/bookings"])
def test_data_sbagliata_422(path):
    r = client.get(f"{path}?date_from=ieri", headers=HEAD_MANAGER)
    assert_errore(r, 422, "validation_error")
    assert "date_from" in r.json()["error"]["details"]
