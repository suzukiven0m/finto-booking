"""Email sintetiche: semantica post-D15 (ADR 0003 §6) — anti-leakage e allineamento gold.

Dopo --persist (D15, WP10), category/urgency/draft_reply sono compilate per tutte le
800 email e status=draft. Questa suite verifica la semantica post-D15:

  (a) pipeline non legge email_gold.csv (import-graph statico)
  (b) predizioni nel DB == ri-esecuzione del classificatore (riproducibilita')
  (c) gold file invariato: 800 righe, categorie valide, non nel DB

Transizione pre-D15 -> post-D15 (legittima, non un indebolimento):
  - prima: category/urgency/draft_reply NULL, status='new' — il classificatore non era
    ancora stato eseguito (atteso).
  - dopo --persist: category/urgency/draft_reply non-NULL, status='draft' — D15 ha
    classificato le email e creato le bozze; le etichette restano predette (non gold),
    le colonne gold non sono nel DB (anti-leakage invariato, vedi (a) e (c)).

Vedi docs/analysis/email-assistant.md per metriche F1 e confusion matrix.
"""

import csv
from pathlib import Path

from etl.email_nlp import classify_category, classify_urgency
from sqlalchemy import func, inspect, select

from app.models import GuestRequest

CATS = {"availability", "cancellation", "complaint", "special_request", "billing", "info"}
GOLD = Path(__file__).resolve().parents[1] / "eval" / "email_gold.csv"


def test_d15_persistence_nel_db(conn):
    """Post-D15: tutte le 800 email hanno category/urgency/draft_reply e status=draft (HITL)."""
    assert conn.execute(select(func.count()).select_from(GuestRequest)).scalar() == 800

    n_compilate = conn.execute(
        select(func.count())
        .select_from(GuestRequest)
        .where(
            GuestRequest.category.is_not(None)
            & GuestRequest.urgency.is_not(None)
            & GuestRequest.draft_reply.is_not(None)
        )
    ).scalar()
    assert n_compilate == 800, (
        "Dopo --persist tutte le 800 email devono avere category/urgency/draft_reply. "
        "Eseguire: docker run ... python data/etl/classify_emails.py --persist"
    )

    n_draft = conn.execute(
        select(func.count()).select_from(GuestRequest).where(GuestRequest.status == "draft")
    ).scalar()
    assert n_draft == 800, "Dopo --persist tutte le 800 email devono essere in status=draft (HITL)"

    n_sent = conn.execute(
        select(func.count()).select_from(GuestRequest).where(GuestRequest.status == "sent")
    ).scalar()
    assert n_sent == 0, "HITL: nessuna email auto-inviata (status='sent' deve essere 0)"


def test_pipeline_non_legge_gold():
    """(a) Anti-leakage: email_nlp.py non referenzia email_gold.csv.

    Verifica statica sull'import-graph: il modulo classificatore non legge ne'
    importa il file gold. L'anti-leakage e' garantito dalla separazione tra
    email_nlp.py (nessuna lettura gold) e classify_emails.py (legge gold solo
    per l'eval, non per le funzioni di classificazione).
    """
    nlp_path = Path(__file__).resolve().parents[1] / "etl" / "email_nlp.py"
    source = nlp_path.read_text()
    assert "email_gold" not in source, "email_nlp.py referenzia email_gold — anti-leakage violato"
    assert "gold.csv" not in source, "email_nlp.py referenzia gold.csv — anti-leakage violato"


def test_d15_reproducibile(conn):
    """(b) Riproducibilita': le predizioni nel DB corrispondono al classificatore rieseguito.

    Verifica che category e urgency nel DB siano deterministicamente derivati dal corpo
    dell'email tramite le stesse funzioni di email_nlp.py. Garantisce che --persist non
    abbia scritto valori gold (che sarebbero diversi per le email mal classificate).
    """
    rows = conn.execute(
        select(
            GuestRequest.id, GuestRequest.body, GuestRequest.category, GuestRequest.urgency
        ).order_by(GuestRequest.id)
    ).all()
    n_checked = 0
    for id_, body, db_cat, db_urg in rows:
        expected_cat = classify_category(body)
        expected_urg = classify_urgency(body, expected_cat)
        assert db_cat == expected_cat, (
            f"id={id_}: DB categoria='{db_cat}', atteso='{expected_cat}' — non riproducibile"
        )
        assert db_urg == expected_urg, (
            f"id={id_}: DB urgenza='{db_urg}', atteso='{expected_urg}' — non riproducibile"
        )
        n_checked += 1
    assert n_checked == 800


def test_gold_allineato_e_mai_nel_db(conn):
    """(c) Gold invariato: 800 righe, categorie valide, colonne gold non nel DB."""
    with GOLD.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 800
    assert {r["true_category"] for r in rows} == CATS
    assert {r["true_urgency"] for r in rows} <= {"low", "medium", "high"}
    # gli id combaciano con guest_requests.id (TRUNCATE RESTART IDENTITY, stesso run)
    n = conn.execute(select(func.count()).select_from(GuestRequest)).scalar()
    assert max(int(r["id"]) for r in rows) == n
    # le colonne gold non esistono nel DB (anti-leakage schema-level)
    cols = {c["name"] for c in inspect(conn).get_columns("guest_requests")}
    assert "true_category" not in cols and "true_urgency" not in cols
