from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from app.database import engine

router = APIRouter()

# se non passano le date uso tutto il dataset
INIZIO = date(2015, 7, 1)
FINE = date(2017, 8, 31)


@router.get("/api/kpis/summary")
def kpi_summary(
    property_id: Annotated[int | None, Query(ge=1, le=2)] = None,  # 1 o 2, vuoto = tutti e due
    date_from: date = INIZIO,
    date_to: date = FINE,
):
    if date_from > date_to:
        raise HTTPException(422, "date_from must be before date_to.")

    # valida = non cancellata, almeno una notte, prezzo > 0
    sql = """
        SELECT
            count(*) FILTER (WHERE NOT is_canceled AND nights > 0 AND adr > 0),
            sum(adr * nights) FILTER (WHERE NOT is_canceled AND nights > 0 AND adr > 0),
            sum(nights) FILTER (WHERE NOT is_canceled AND nights > 0 AND adr > 0),
            count(*),
            count(*) FILTER (WHERE is_canceled)
        FROM bookings
        WHERE arrival_date BETWEEN :date_from AND :date_to
    """
    sql_camere = "SELECT sum(room_count) FROM properties"
    params = {"date_from": date_from, "date_to": date_to}
    params_camere = {}

    # se scelgono un hotel filtro anche per quello
    if property_id is not None:
        sql += " AND property_id = :property_id"
        sql_camere += " WHERE id = :property_id"
        params["property_id"] = property_id
        params_camere["property_id"] = property_id

    with engine.connect() as conn:
        valide, incassi, notti, totali, cancellate = conn.execute(text(sql), params).one()
        camere = conn.execute(text(sql_camere), params_camere).scalar()

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
    where = "WHERE date BETWEEN :date_from AND :date_to"
    sql_camere = "SELECT sum(room_count) FROM properties"
    params = {"date_from": date_from, "date_to": date_to}
    params_camere = {}

    if property_id is not None:
        where += " AND property_id = :property_id"
        sql_camere += " WHERE id = :property_id"
        params["property_id"] = property_id
        params_camere["property_id"] = property_id

    sql_giorni = f"""
        SELECT date, sum(room_nights), sum(revenue)
        FROM kpi_daily
        {where}
        GROUP BY date
        ORDER BY date
        LIMIT :limit OFFSET :offset
    """
    sql_totale = f"SELECT count(DISTINCT date) FROM kpi_daily {where}"

    # pagina 1 = righe 0-49, pagina 2 = righe 50-99, ...
    params["limit"] = page_size
    params["offset"] = (page - 1) * page_size

    with engine.connect() as conn:
        righe = conn.execute(text(sql_giorni), params).all()
        totale = conn.execute(text(sql_totale), params).scalar()
        camere = conn.execute(text(sql_camere), params_camere).scalar()

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
