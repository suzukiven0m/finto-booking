from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import auth
from app.database import engine
from app.kpis import FINE, INIZIO
from app.models import Booking

router = APIRouter(dependencies=[Depends(auth.require_token)])


@router.get("/api/bookings")
def list_bookings(
    property_id: Annotated[int | None, Query(ge=1, le=2)] = None,  # 1 o 2, vuoto = tutti e due
    date_from: date = INIZIO,
    date_to: date = FINE,
    is_canceled: bool | None = None,  # vuoto = cancellate e non
    market_segment: str | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,  # massimo 200 come da contratto
):
    if date_from > date_to:
        raise HTTPException(422, "date_from must be before date_to.")

    # una riga per prenotazione deduplicata, cancellate comprese (D19).
    # solo i 15 campi dello schema Booking: agent/company ecc. restano fuori
    stmt = (
        select(
            Booking.id,
            Booking.property_id,
            Booking.arrival_date,
            Booking.nights,
            Booking.adr,
            Booking.is_canceled,
            Booking.adults,
            Booking.children,
            Booking.babies,
            Booking.country,
            Booking.customer_type,
            Booking.market_segment,
            Booking.distribution_channel,
            Booking.deposit_type,
            Booking.lead_time,
        )
        .where(Booking.arrival_date.between(date_from, date_to))
        .order_by(Booking.arrival_date, Booking.id)
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    stmt_totale = (
        select(func.count())
        .select_from(Booking)
        .where(Booking.arrival_date.between(date_from, date_to))
    )
    if property_id is not None:
        stmt = stmt.where(Booking.property_id == property_id)
        stmt_totale = stmt_totale.where(Booking.property_id == property_id)
    if is_canceled is not None:
        stmt = stmt.where(Booking.is_canceled.is_(is_canceled))
        stmt_totale = stmt_totale.where(Booking.is_canceled.is_(is_canceled))
    if market_segment is not None:
        stmt = stmt.where(Booking.market_segment == market_segment)
        stmt_totale = stmt_totale.where(Booking.market_segment == market_segment)

    with Session(engine) as session:
        righe = session.execute(stmt).all()
        totale = session.execute(stmt_totale).scalar_one()

    dati = []
    for r in righe:
        dati.append(
            {
                "id": r.id,
                "property_id": r.property_id,
                "arrival_date": r.arrival_date,
                "nights": r.nights,
                "adr": float(r.adr),
                "is_canceled": r.is_canceled,
                "adults": r.adults,
                "children": r.children,
                "babies": r.babies,
                "country": r.country,
                "customer_type": r.customer_type,
                "market_segment": r.market_segment,
                "distribution_channel": r.distribution_channel,
                "deposit_type": r.deposit_type,
                "lead_time": r.lead_time,
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
