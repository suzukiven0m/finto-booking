"""Email sintetiche: anti-leakage (ADR 0003 §6) e allineamento del gold file."""

import csv
from pathlib import Path

from sqlalchemy import func, inspect, select

from app.models import GuestRequest

CATS = {"availability", "cancellation", "complaint", "special_request", "billing", "info"}
GOLD = Path(__file__).resolve().parents[1] / "eval" / "email_gold.csv"


def test_emails_800_senza_label_nel_db(conn):
    assert conn.execute(select(func.count()).select_from(GuestRequest)).scalar() == 800
    leak = conn.execute(
        select(func.count())
        .select_from(GuestRequest)
        .where(GuestRequest.category.is_not(None) | GuestRequest.draft_reply.is_not(None))
    ).scalar()
    assert leak == 0
    not_new = conn.execute(
        select(func.count()).select_from(GuestRequest).where(GuestRequest.status != "new")
    ).scalar()
    assert not_new == 0


def test_gold_allineato_e_mai_nel_db(conn):
    with GOLD.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 800
    assert {r["true_category"] for r in rows} == CATS
    assert {r["true_urgency"] for r in rows} <= {"low", "medium", "high"}
    # gli id combaciano con guest_requests.id (TRUNCATE RESTART IDENTITY, stesso run)
    n = conn.execute(select(func.count()).select_from(GuestRequest)).scalar()
    assert max(int(r["id"]) for r in rows) == n
    # le colonne gold non esistono nel DB
    cols = {c["name"] for c in inspect(conn).get_columns("guest_requests")}
    assert "true_category" not in cols and "true_urgency" not in cols
