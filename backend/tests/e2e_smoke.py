#!/usr/bin/env python3
"""
E2E smoke: exercises the full UI data path via real HTTP against a running
uvicorn instance (http://localhost:8000 by default).

Checks (in order):
  1. login (manager demo)
  2. kpis/summary — baseline numbers, auto-detects sample vs full DB
  3. kpis/daily — meta
  4. reviews/summary — pinned per-property counts (762/876, full corpus 1638)
  5. reviews list
  6. bookings list
  7. guest-requests — post-D15: category non-null, status draft, 800 rows
  8. PATCH guest-requests/1: draft→sent, then RESTORE via SQL
     (snapshot before, end-state invariant: 800 draft / 0 sent)
  9. 401 without token
 10. properties open (no auth)

Override base URL:  API_BASE_URL=http://localhost:8000
Override DB URL:    DATABASE_URL=postgresql+psycopg://buby:buby@localhost:5432/buby
CI=true semantics: DB/API unreachable → exit 1 (never skip).

Exit 0: all assertions passed.  Exit 1: any assertion failed.
"""

import os
import sys

import httpx2 as httpx
import sqlalchemy as sa
from sqlalchemy.orm import Session

BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
_DB_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://buby:buby@localhost:5432/buby")

# pinned per-property review counts from the committed corpus (1638 reviews)
_REVIEWS_PINNED = {
    1: {"count": 762, "overall": 3.86},
    2: {"count": 876, "overall": 4.4},
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def step(msg: str) -> None:
    print(f"→ {msg}")


# minimal table handle for the snapshot/restore SQL (no app import: the
# script must run from the repo root without PYTHONPATH)
_GUEST_REQUESTS = sa.table("guest_requests", sa.column("id"), sa.column("status"))


def _snapshot_row1() -> str:
    """Row 1 status via SQL: the API has no single-row GET and the list is
    ordered by received_at, so row 1 is not reliably on page 1."""
    engine = sa.create_engine(_DB_URL)
    try:
        with Session(engine) as session:
            return session.execute(
                sa.select(_GUEST_REQUESTS.c.status).where(_GUEST_REQUESTS.c.id == 1)
            ).scalar_one()
    finally:
        engine.dispose()


def _restore_row1() -> None:
    """SQL restore: row 1 back to draft (sent is terminal via the API)."""
    step("RESTORE row 1 to draft via SQL")
    engine = sa.create_engine(_DB_URL)
    try:
        with Session(engine) as session:
            session.execute(
                sa.update(_GUEST_REQUESTS).where(_GUEST_REQUESTS.c.id == 1).values(status="draft")
            )
            session.commit()
    finally:
        engine.dispose()


try:
    with httpx.Client(base_url=BASE, timeout=30) as c:
        # 1. login (manager demo)
        step("login (manager demo)")
        r = c.post(
            "/api/auth/login",
            json={"email": "manager@buby.travel", "password": "demo"},
        )
        if r.status_code != 200:
            fail(f"login: expected 200, got {r.status_code}: {r.text}")
        h = {"Authorization": f"Bearer {r.json()['access_token']}"}

        # 2. kpis/summary — baseline, auto-detect sample vs full DB
        step("kpis/summary baseline")
        r = c.get("/api/kpis/summary", headers=h)
        if r.status_code != 200:
            fail(f"kpis/summary: expected 200, got {r.status_code}")
        s = r.json()
        if s["valid_bookings"] == 3564:
            # sample DB (data/raw/sample_hotel_bookings.csv, 5000 rows)
            for field, expected in [
                ("room_nights", 12696),
                ("revenue", 1350503.84),
                ("cancellation_rate", 0.2696),
            ]:
                if s[field] != expected:
                    fail(f"summary[{field}]: expected {expected}, got {s[field]}")
            step("  sample DB detected: assertions passed (3564/12696/1350503.84/0.2696)")
        elif s["valid_bookings"] == 61777:
            # full DB (hotel_bookings.csv, 87396 rows, 61777 valid)
            for field, expected in [
                ("revenue", 22976960.13),
                ("room_nights", 218410),
                ("adr", 105.2),
                ("cancellation_rate", 0.2749),
                ("occupancy_avg", 0.6558),
                ("revpar", 68.99),
            ]:
                if s[field] != expected:
                    fail(f"summary[{field}]: expected {expected}, got {s[field]}")
            step(
                "  full DB detected: assertions passed"
                " (61777/22976960.13/218410/105.20/0.2749/0.6558/68.99)"
            )
        else:
            fail(
                f"summary valid_bookings={s['valid_bookings']}: "
                "expected 3564 (sample) or 61777 (full DB)"
            )

        # 3. kpis/daily — meta
        step("kpis/daily meta")
        r = c.get("/api/kpis/daily?page_size=10", headers=h)
        if r.status_code != 200:
            fail(f"kpis/daily: expected 200, got {r.status_code}")
        meta = r.json()["meta"]
        if meta["total"] <= 0:
            fail(f"kpis/daily meta.total: expected >0, got {meta['total']}")
        step(f"  meta.total={meta['total']}, total_pages={meta['total_pages']}")

        # 4. reviews/summary — pinned per-property (full corpus 1638 always seeded)
        step("reviews/summary per-property")
        for pid, pinned in _REVIEWS_PINNED.items():
            r = c.get(f"/api/reviews/summary?property_id={pid}", headers=h)
            if r.status_code != 200:
                fail(f"reviews/summary?property_id={pid}: expected 200, got {r.status_code}")
            body = r.json()
            if body["property_id"] != pid:
                fail(f"reviews/summary property_id: expected {pid}, got {body['property_id']}")
            if body["count"] != pinned["count"]:
                fail(
                    f"reviews/summary[property_id={pid}] count: "
                    f"expected {pinned['count']}, got {body['count']}"
                )
            if body["overall"] != pinned["overall"]:
                fail(
                    f"reviews/summary[property_id={pid}] overall: "
                    f"expected {pinned['overall']}, got {body['overall']}"
                )
            step(f"  property_id={pid} count={body['count']} overall={body['overall']} ✓")

        # 5. reviews list
        step("reviews list")
        r = c.get("/api/reviews?page_size=5", headers=h)
        if r.status_code != 200:
            fail(f"reviews: expected 200, got {r.status_code}")
        if not r.json()["data"]:
            fail("reviews: expected at least 1 row")
        step(f"  meta.total={r.json()['meta']['total']}")

        # 6. bookings list
        step("bookings list")
        r = c.get("/api/bookings?page_size=5", headers=h)
        if r.status_code != 200:
            fail(f"bookings: expected 200, got {r.status_code}")
        if not r.json()["data"]:
            fail("bookings: expected at least 1 row")
        step(f"  meta.total={r.json()['meta']['total']}")

        # 7. guest-requests — post-D15: category non-null, status valid
        step("guest-requests (post-D15)")
        r = c.get("/api/guest-requests?page_size=50", headers=h)
        if r.status_code != 200:
            fail(f"guest-requests: expected 200, got {r.status_code}")
        body = r.json()
        items = body["data"]
        if not items:
            fail("guest-requests: expected at least 1 row")
        if body["meta"]["total"] != 800:
            fail(f"guest-requests meta.total: expected 800, got {body['meta']['total']}")
        for item in items:
            if item["category"] is None:
                fail(f"guest-requests id={item['id']}: category is null (pre-D15 state)")
            if item["status"] != "draft":
                fail(
                    f"guest-requests id={item['id']}: "
                    f"expected status=draft (post-D15), got {item['status']}"
                )
        step(f"  {len(items)} items, all category set + status=draft")

        # 8. PATCH row 1: draft → sent, then RESTORE (snapshot/restore discipline)
        # Sent is a terminal state via the API; restore is done via SQL.
        step("PATCH row 1: draft→sent")
        if _snapshot_row1() != "draft":
            fail("guest_requests row 1: expected status=draft before PATCH (dirty DB?)")
        r = c.patch("/api/guest-requests/1", json={"status": "sent"}, headers=h)
        if r.status_code != 200:
            fail(f"PATCH guest-requests/1 status=sent: expected 200, got {r.status_code}: {r.text}")
        if r.json()["status"] != "sent":
            # restore before failing so the DB isn't left dirty
            _restore_row1()
            fail(f"PATCH guest-requests/1: status not updated, got {r.json()['status']}")
        step("  row 1 → sent ✓")

        _restore_row1()

        # verify: 0 rows in sent state
        r = c.get("/api/guest-requests?status=sent&page_size=1", headers=h)
        if r.status_code != 200:
            fail(f"guest-requests?status=sent: expected 200, got {r.status_code}")
        sent_count = r.json()["meta"]["total"]
        if sent_count != 0:
            fail(f"restore failed: {sent_count} rows still in sent state")
        r = c.get("/api/guest-requests?status=draft&page_size=1", headers=h)
        if r.status_code != 200:
            fail(f"guest-requests?status=draft: expected 200, got {r.status_code}")
        draft_count = r.json()["meta"]["total"]
        if draft_count != 800:
            fail(f"restore failed: expected 800 draft rows, got {draft_count}")
        step("  row 1 restored: 800 draft / 0 sent ✓")

        # 9. 401 without token
        step("401 no-token check")
        r = c.get("/api/kpis/summary")
        if r.status_code != 401:
            fail(f"no-token 401 check: expected 401, got {r.status_code}")
        step("  401 without token ✓")

        # 10. properties open (no auth required)
        step("properties open")
        r = c.get("/api/properties")
        if r.status_code != 200:
            fail(f"properties: expected 200, got {r.status_code}")
        props = r.json()["data"]
        if len(props) != 2:
            fail(f"properties: expected 2, got {len(props)}")
        step(f"  {[p['name'] for p in props]} ✓")

except (httpx.ConnectError, httpx.TimeoutException) as exc:
    print(f"ERROR: cannot reach {BASE}: {exc}", file=sys.stderr)
    sys.exit(1)

print("All E2E assertions passed.")
