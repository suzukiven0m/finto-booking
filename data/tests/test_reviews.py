"""Legame recensioni↔proprieta' asserito (ADR 0003): mapping scelto una volta sola."""

from sqlalchemy import func, inspect, select

from app.models import Property, Review

# ta_hotel_id immutabili dopo il SAL 1 (ADR 0003 §1): offering_id recuperati da
# review.txt, perche' l'hotel_id del pickle HF era in realta' l'id della recensione.
MAPPING = [(1, 93618), (2, 2079052)]


def test_properties_hanno_ta_hotel_id_scelto(conn):
    rows = conn.execute(select(Property.id, Property.ta_hotel_id).order_by(Property.id)).all()
    assert [(int(a), int(b)) for a, b in rows] == MAPPING


def test_reviews_coerenti_con_la_proprieta(conn):
    rows = conn.execute(
        select(Review.property_id, Review.ta_hotel_id, Property.ta_hotel_id).join(
            Property, Property.id == Review.property_id
        )
    ).all()
    assert rows
    for pid, rta, pta in rows:
        assert pid in (1, 2)
        assert rta == pta  # ta_hotel_id denormalizzato coerente
    orphan = conn.execute(
        select(func.count()).select_from(Review).where(Review.property_id.is_(None))
    ).scalar()
    assert orphan == 0


def test_reviews_voti_tra_1_e_5(conn):
    bad = conn.execute(
        select(func.count()).select_from(Review).where((Review.overall < 1) | (Review.overall > 5))
    ).scalar()
    assert bad == 0


def test_reviews_niente_output_del_modello(conn):
    # ADR 0003 §3: sentiment/topics sono output D14, non stanno nella sorgente
    cols = {c["name"] for c in inspect(conn).get_columns("reviews")}
    assert "sentiment" not in cols and "topics" not in cols
