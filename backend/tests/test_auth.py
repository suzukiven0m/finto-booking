import asyncio
import json
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import text
from starlette.requests import Request

from app import auth, errors
from app.config import DEMO_USERS, JWT_ALGORITHM, JWT_SECRET
from app.main import app

client = TestClient(app)

ROTTE_PROTETTE = ["/api/kpis/summary", "/api/kpis/daily"]
ENVELOPE_401 = {"error": {"code": "unauthorized", "message": "Missing or invalid bearer token."}}
# password demo letta dalla config: niente literal nel test, il secret scanner
# della CI (GitGuardian) li scambia per segreti veri
DEMO_PASSWORD = DEMO_USERS["manager@buby.travel"]["password"]


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def login_token(email):
    r = client.post("/api/auth/login", json={"email": email, "password": DEMO_PASSWORD})
    assert r.status_code == 200
    return r.json()["access_token"]


def claims_demo(role: object = "manager", ore=1):
    return {
        "sub": "manager@buby.travel",
        "role": role,
        "exp": datetime.now(UTC) + timedelta(hours=ore),
    }


@pytest.mark.parametrize("email", list(DEMO_USERS))
def test_login_emette_jwt_verificabile(email):
    r = client.post("/api/auth/login", json={"email": email, "password": DEMO_PASSWORD})
    assert r.status_code == 200
    body = r.json()
    # shape LoginResponse esatta del contratto
    assert sorted(body.keys()) == ["access_token", "role", "token_type"]
    assert body["token_type"] == "bearer"
    assert body["role"] == DEMO_USERS[email]["role"]
    claims = jwt.decode(body["access_token"], JWT_SECRET, algorithms=[JWT_ALGORITHM])
    assert claims["sub"] == email
    assert claims["role"] == DEMO_USERS[email]["role"]
    # scadenza a 8 ore
    ore = (claims["exp"] - datetime.now(UTC).timestamp()) / 3600
    assert 7.9 < ore <= 8


@pytest.mark.parametrize(
    "body",
    [
        {"email": "manager@buby.travel", "password": DEMO_PASSWORD + "-sbagliata"},
        {"email": "sconosciuto@buby.travel", "password": DEMO_PASSWORD},
    ],
)
def test_login_credenziali_sbagliate_401(body):
    r = client.post("/api/auth/login", json=body)
    assert r.status_code == 401
    # esempio 401 della rotta login nel contratto
    assert r.json() == {
        "error": {"code": "invalid_credentials", "message": "Email or password is incorrect."}
    }


@pytest.mark.parametrize("path", ROTTE_PROTETTE)
def test_senza_token_401(path):
    r = client.get(path)
    assert r.status_code == 401
    assert r.json() == ENVELOPE_401


@pytest.mark.parametrize("path", ROTTE_PROTETTE)
@pytest.mark.parametrize("token", ["patacca", "eyJhbGciOiJIUzI1NiJ9.patacca.patacca"])
def test_token_spazzatura_401(path, token):
    r = client.get(path, headers=bearer(token))
    assert r.status_code == 401
    assert r.json() == ENVELOPE_401


@pytest.mark.parametrize("path", ROTTE_PROTETTE)
def test_token_scaduto_401(path):
    scaduto = jwt.encode(claims_demo(ore=-1), JWT_SECRET, algorithm=JWT_ALGORITHM)
    r = client.get(path, headers=bearer(scaduto))
    assert r.status_code == 401
    assert r.json() == ENVELOPE_401


@pytest.mark.parametrize("path", ROTTE_PROTETTE)
def test_token_firma_o_schema_sbagliati_401(path):
    firma_diversa = jwt.encode(claims_demo(), "secret-diverso", algorithm=JWT_ALGORITHM)
    r = client.get(path, headers=bearer(firma_diversa))
    assert r.status_code == 401
    assert r.json() == ENVELOPE_401
    # schema Basic al posto di Bearer
    r = client.get(path, headers={"Authorization": f"Basic {login_token('manager@buby.travel')}"})
    assert r.status_code == 401
    assert r.json() == ENVELOPE_401


def test_token_valido_summary_baseline(conn):
    # numeri del dataset completo (87396 righe dedup), dizionario dati §3
    n = conn.execute(text("SELECT count(*) FROM bookings")).scalar()
    if n != 87396:
        pytest.skip("nel db non c'e' il dataset completo da 87396 righe")
    token = login_token("manager@buby.travel")
    r = client.get("/api/kpis/summary", headers=bearer(token))
    assert r.status_code == 200
    s = r.json()
    assert s["valid_bookings"] == 61777
    assert s["revenue"] == 22976960.13
    assert s["room_nights"] == 218410
    assert s["adr"] == 105.20
    assert s["cancellation_rate"] == 0.2749
    assert s["occupancy_avg"] == 0.6558
    assert s["revpar"] == 68.99


def test_token_valido_daily_200(conn):
    token = login_token("admin@buby.travel")
    r = client.get("/api/kpis/daily?page_size=10", headers=bearer(token))
    assert r.status_code == 200
    assert sorted(r.json().keys()) == ["data", "meta"]


def test_require_write_role_admin_e_manager_passano():
    for role in ("admin", "manager"):
        claims = claims_demo(role=role)
        assert auth.require_write_role(claims) == claims


def test_require_write_role_property_manager_403_envelope():
    # catena vera: JWT di property_manager -> require_token -> require_write_role
    token = login_token("property.manager@buby.travel")
    request = Request({"type": "http", "headers": [(b"authorization", f"Bearer {token}".encode())]})
    claims = auth.require_token(request)
    with pytest.raises(HTTPException) as exc:
        auth.require_write_role(claims)
    assert exc.value.status_code == 403
    resp = asyncio.run(errors.errore_http(request, exc.value))
    assert json.loads(bytes(resp.body)) == {
        "error": {
            "code": "forbidden",
            "message": "Your role is not allowed to perform this action.",
        }
    }


def test_require_write_role_role_non_stringa_403_envelope():
    # role lista nel JWT (firmato col secret dev): niente TypeError/500, ma 403
    token = jwt.encode(claims_demo(role=["admin"]), JWT_SECRET, algorithm=JWT_ALGORITHM)
    request = Request({"type": "http", "headers": [(b"authorization", f"Bearer {token}".encode())]})
    claims = auth.require_token(request)
    with pytest.raises(HTTPException) as exc:
        auth.require_write_role(claims)
    assert exc.value.status_code == 403
    resp = asyncio.run(errors.errore_http(request, exc.value))
    assert json.loads(bytes(resp.body)) == {
        "error": {
            "code": "forbidden",
            "message": "Your role is not allowed to perform this action.",
        }
    }


def test_rotte_aperte_restano_aperte(conn):
    # security: [] nel contratto: niente token richiesto, e uno spazzatura ignorato
    assert client.get("/api/properties").status_code == 200
    assert client.get("/api/properties", headers=bearer("patacca")).status_code == 200
    r = client.post(
        "/api/auth/login", json={"email": "admin@buby.travel", "password": DEMO_PASSWORD}
    )
    assert r.status_code == 200
