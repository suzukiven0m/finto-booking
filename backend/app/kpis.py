from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Integer, Numeric, and_, cast, func, select
from sqlalchemy.orm import Session

from app import auth
from app.database import engine
from app.models import Booking, KpiDaily, Property

# tutte le rotte KPI sono protette dal bearer JWT (D11)
router = APIRouter(dependencies=[Depends(auth.require_token)])

# se non passano le date uso tutto il dataset
INIZIO = date(2015, 7, 1)
FINE = date(2017, 8, 31)

# filtro della baseline pulita (dizionario dati §3): non cancellata,
# almeno una notte, prezzo > 0. Bindato dall'ORM, niente SQL concatenato.
VALIDA = and_(Booking.is_canceled.is_(False), Booking.nights > 0, Booking.adr > 0)


@router.get("/api/kpis/summary")
def kpi_summary(
    property_id: Annotated[int | None, Query(ge=1, le=2)] = None,  # 1 o 2, vuoto = tutti e due
    date_from: date = INIZIO,
    date_to: date = FINE,
):
    if date_from > date_to:
        raise HTTPException(422, "date_from must be before date_to.")

    stmt = select(
        func.count().filter(VALIDA),
        func.sum(Booking.adr * Booking.nights).filter(VALIDA),
        func.sum(Booking.nights).filter(VALIDA),
        func.count(),
        func.count().filter(Booking.is_canceled.is_(True)),
    ).where(Booking.arrival_date.between(date_from, date_to))
    stmt_camere = select(func.sum(Property.room_count))

    # se scelgono un hotel filtro anche per quello
    if property_id is not None:
        stmt = stmt.where(Booking.property_id == property_id)
        stmt_camere = stmt_camere.where(Property.id == property_id)

    with Session(engine) as session:
        valide, incassi, notti, totali, cancellate = session.execute(stmt).one()
        camere = session.execute(stmt_camere).scalar_one()

    # se non ci sono prenotazioni sum() da None
    if incassi is None:
        incassi = 0
    if notti is None:
        notti = 0
    incassi = float(incassi)

    # camere disponibili nel periodo (190 lago, 230 montagna, ipotizzate)
    giorni = (date_to - date_from).days + 1
    disponibili = camere * giorni

    # niente divisioni per zero
    adr = 0.0
    if notti > 0:
        adr = incassi / notti
    tasso_cancellazioni = 0.0
    if totali > 0:
        tasso_cancellazioni = cancellate / totali

    return {
        "property_id": property_id,
        "date_from": date_from,
        "date_to": date_to,
        "valid_bookings": valide,
        "revenue": round(incassi, 2),
        "room_nights": notti,
        "adr": round(adr, 2),
        "cancellation_rate": round(tasso_cancellazioni, 4),
        "occupancy_avg": round(notti / disponibili, 4),
        "revpar": round(incassi / disponibili, 2),
    }


@router.get("/api/kpis/daily")
def kpi_daily(
    property_id: Annotated[int | None, Query(ge=1, le=2)] = None,  # 1 o 2, vuoto = tutti e due
    date_from: date = INIZIO,
    date_to: date = FINE,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,  # massimo 200 come da contratto
):
    if date_from > date_to:
        raise HTTPException(422, "date_from must be before date_to.")

    # una riga per giorno: con tutti e due gli hotel sommo lago + montagna
    stmt = (
        select(KpiDaily.date, func.sum(KpiDaily.room_nights), func.sum(KpiDaily.revenue))
        .where(KpiDaily.date.between(date_from, date_to))
        .group_by(KpiDaily.date)
        .order_by(KpiDaily.date)
        .limit(page_size)
        .offset((page - 1) * page_size)  # pagina 1 = righe 0-49, pagina 2 = 50-99, ...
    )
    stmt_totale = select(func.count(func.distinct(KpiDaily.date))).where(
        KpiDaily.date.between(date_from, date_to)
    )
    stmt_camere = select(func.sum(Property.room_count))

    if property_id is not None:
        stmt = stmt.where(KpiDaily.property_id == property_id)
        stmt_totale = stmt_totale.where(KpiDaily.property_id == property_id)
        stmt_camere = stmt_camere.where(Property.id == property_id)

    with Session(engine) as session:
        righe = session.execute(stmt).all()
        totale = session.execute(stmt_totale).scalar_one()
        camere = session.execute(stmt_camere).scalar_one()

    giorni = []
    for giorno, notti, incassi in righe:
        incassi = float(incassi)
        # nei giorni senza ospiti l'adr non esiste
        adr = None
        if notti > 0:
            adr = round(incassi / notti, 2)
        giorni.append(
            {
                "date": giorno,
                "room_nights": notti,
                "revenue": round(incassi, 2),
                "occupancy": round(notti / camere, 4),
                "adr": adr,
                "revenue_per_available_room": round(incassi / camere, 2),
            }
        )

    # quante pagine servono, arrotondando per eccesso
    pagine = (totale + page_size - 1) // page_size

    return {
        "data": giorni,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": totale,
            "total_pages": pagine,
        },
    }


@router.get("/api/kpis/channels")
def kpi_channels(
    property_id: Annotated[int | None, Query(ge=1, le=2)] = None,  # 1 o 2, vuoto = tutti e due
    date_from: date = INIZIO,
    date_to: date = FINE,
):
    if date_from > date_to:
        raise HTTPException(422, "date_from must be before date_to.")

    # stessa coorte di arrivi del summary, solo prenotazioni valide
    stmt = (
        select(Booking.market_segment, func.count(), func.sum(Booking.adr * Booking.nights))
        .where(VALIDA, Booking.arrival_date.between(date_from, date_to))
        .group_by(Booking.market_segment)
        .order_by(func.count().desc())
    )
    if property_id is not None:
        stmt = stmt.where(Booking.property_id == property_id)

    with Session(engine) as session:
        righe = session.execute(stmt).all()

    # i segmenti senza prenotazioni valide (es. Undefined) non hanno righe:
    # niente divisione per zero, la lista resta vuota se la finestra e' vuota
    totale = sum(r[1] for r in righe)
    canali = []
    for segmento, prenotazioni, incassi in righe:
        canali.append(
            {
                "market_segment": segmento,
                "bookings": prenotazioni,
                "revenue": round(float(incassi), 2),
                # quota delle PRENOTAZIONI valide, non del ricavo (ChannelMixItem)
                "share": round(prenotazioni / totale, 4),
            }
        )
    return {"data": canali}


@router.get("/api/kpis/seasonality")
def kpi_seasonality(
    property_id: Annotated[int | None, Query(ge=1, le=2)] = None,  # 1 o 2, vuoto = tutti e due
):
    # medie per mese dell'anno, mai totali mensili grezzi (dizionario dati §3:
    # 2015 e 2017 sono anni parziali)
    mese_arrivo = cast(func.extract("month", Booking.arrival_date), Integer)
    # avg_adr: ADR pooled sulle valide che ARRIVANO in quel mese (coorte arrivi)
    stmt_adr = (
        select(mese_arrivo, func.sum(Booking.adr * Booking.nights) / func.sum(Booking.nights))
        .where(VALIDA)
        .group_by(mese_arrivo)
    )
    if property_id is not None:
        stmt_adr = stmt_adr.where(Booking.property_id == property_id)
        # singola proprieta': occupancy salvata e ricavo giornaliero da kpi_daily
        mese_soggiorno = cast(func.extract("month", KpiDaily.date), Integer)
        stmt_giorni = (
            select(mese_soggiorno, func.avg(KpiDaily.occupancy), func.avg(KpiDaily.revenue))
            .where(KpiDaily.property_id == property_id)
            .group_by(mese_soggiorno)
        )
    else:
        # entrambi: somme per data (come il daily), capacita' combinata e
        # avg_revenue = media del ricavo giornaliero sommato / 2 (per proprieta')
        per_data = (
            select(
                KpiDaily.date,
                func.sum(KpiDaily.room_nights).label("notti"),
                func.sum(KpiDaily.revenue).label("incassi"),
            )
            .group_by(KpiDaily.date)
            .cte("per_data")
        )
        capacita = select(func.sum(Property.room_count)).scalar_subquery()
        mese = cast(func.extract("month", per_data.c.date), Integer)
        stmt_giorni = select(
            mese,
            func.avg(cast(per_data.c.notti, Numeric) / capacita),
            func.avg(per_data.c.incassi) / 2,
        ).group_by(mese)

    with Session(engine) as session:
        adr_per_mese = dict(session.execute(stmt_adr).all())
        giorni_per_mese = {m: (occ, rev) for m, occ, rev in session.execute(stmt_giorni).all()}

    # sempre 12 punti (SeasonalityList): i mesi senza dati valgono 0
    punti = []
    for mese in range(1, 13):
        adr = adr_per_mese.get(mese)
        occupancy, ricavo = giorni_per_mese.get(mese, (None, None))
        punti.append(
            {
                "month": mese,
                "avg_adr": round(float(adr), 2) if adr is not None else 0.0,
                "avg_occupancy": round(float(occupancy), 4) if occupancy is not None else 0.0,
                "avg_revenue": round(float(ricavo), 2) if ricavo is not None else 0.0,
            }
        )
    return {"data": punti}
