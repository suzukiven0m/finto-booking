from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import auth
from app.database import engine
from app.models import Review

router = APIRouter(dependencies=[Depends(auth.require_token)])

# voti reali degli ospiti (weak labels), NON output del modello (D14)
DIMENSIONI = ["overall", "cleanliness", "value", "location", "rooms", "sleep_quality"]


@router.get("/api/reviews/summary")
def review_summary(
    property_id: Annotated[int | None, Query(ge=1, le=2)] = None,  # 1 o 2, vuoto = tutti e due
):
    stmt = select(
        func.count(),
        func.avg(Review.overall),
        func.avg(Review.cleanliness),
        func.avg(Review.value),
        func.avg(Review.location),
        func.avg(Review.rooms),
        func.avg(Review.sleep_quality),
    )
    if property_id is not None:
        stmt = stmt.where(Review.property_id == property_id)
    with Session(engine) as session:
        riga = session.execute(stmt).one()

    # con tutti e due gli hotel la media e' su tutte le righe: ponderata per count
    return {
        "property_id": property_id,
        "count": riga[0],
        **{
            nome: round(float(voto), 2) if voto is not None else 0.0
            for nome, voto in zip(DIMENSIONI, riga[1:], strict=True)
        },
    }


@router.get("/api/reviews")
def list_reviews(
    property_id: Annotated[int | None, Query(ge=1, le=2)] = None,  # 1 o 2, vuoto = tutti e due
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,  # massimo 200 come da contratto
):
    filtri = []
    if property_id is not None:
        filtri.append(Review.property_id == property_id)

    # niente sentiment/topics: sono output del modello (D14), non del contratto
    stmt = (
        select(Review)
        .where(*filtri)
        .order_by(Review.post_date.desc(), Review.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    stmt_totale = select(func.count()).select_from(Review).where(*filtri)
    with Session(engine) as session:
        righe = session.execute(stmt).scalars().all()
        totale = session.execute(stmt_totale).scalar_one()

    dati = []
    for r in righe:
        dati.append(
            {
                "id": r.id,
                "property_id": r.property_id,
                "ta_hotel_id": r.ta_hotel_id,
                "post_date": r.post_date,
                "stay_year": r.stay_year,
                **{
                    nome: float(getattr(r, nome)) if getattr(r, nome) is not None else None
                    for nome in DIMENSIONI
                },
                "title": r.title,
                "body": r.body,
                "lang": r.lang,
            }
        )

    pagine = (totale + page_size - 1) // page_size
    return {
        "data": dati,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": totale,
            "total_pages": pagine,
        },
    }
