from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from app import auth, errors, kpis
from app.database import engine
from app.models import Property

# per accenderlo: uvicorn app.main:app --reload
app = FastAPI(title="Buby Travel API", version="1.0.0")

# errori sempre nel formato del contratto (vedi errors.py)
app.add_exception_handler(HTTPException, errors.errore_http)
app.add_exception_handler(RequestValidationError, errors.errore_validazione)
app.add_exception_handler(Exception, errors.errore_imprevisto)

# endpoint che stanno negli altri file
app.include_router(kpis.router)
app.include_router(auth.router)

# senza questo il browser blocca la dashboard (gira su un'altra porta)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# i due hotel, non serve il login
@app.get("/api/properties")
def list_properties():
    with Session(engine) as session:
        hotels = session.scalars(select(Property).order_by(Property.id)).all()

    lista = []
    for h in hotels:
        lista.append(
            {
                "id": h.id,
                "name": h.name,
                "hotel_type": h.hotel_type,
                "location_type": h.location_type,
                "room_count": h.room_count,
                "ta_hotel_id": h.ta_hotel_id,
            }
        )
    return {"data": lista}
