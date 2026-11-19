from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, model_validator
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app import auth
from app.database import engine
from app.models import GuestRequest

router = APIRouter()

# transizioni consentite (HITL, D20): avanti di uno, bozza modificabile.
# new->new e new->sent rifiutati: si passa sempre da draft; sent e' terminale.
TRANSIZIONI = {("new", "draft"), ("draft", "sent"), ("draft", "draft")}

# i 7 campi dello schema GuestRequest. urgency (migrazione 0005) NON e'
# nel contratto: mai esposta, mai scritta.
CAMPI_GUEST_REQUEST = select(
    GuestRequest.id,
    GuestRequest.property_id,
    GuestRequest.received_at,
    GuestRequest.body,
    GuestRequest.category,
    GuestRequest.draft_reply,
    GuestRequest.status,
)


class GuestRequestUpdate(BaseModel):
    # update parziale (minProperties: 1): null esplicito non valido,
    # lo schema del contratto non e' nullable
    status: Literal["new", "draft", "sent"] | None = None
    draft_reply: str | None = None

    @model_validator(mode="after")
    def almeno_un_campo(self):
        if not self.model_fields_set:
            raise ValueError("At least one of status / draft_reply is required.")
        for campo in self.model_fields_set:
            if getattr(self, campo) is None:
                raise ValueError(f"{campo} cannot be null.")
        return self


@router.get("/api/guest-requests", dependencies=[Depends(auth.require_token)])
def list_guest_requests(
    property_id: Annotated[int | None, Query(ge=1, le=2)] = None,  # 1 o 2, vuoto = tutti e due
    status: Annotated[Literal["new", "draft", "sent"] | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,  # massimo 200 come da contratto
):
    filtri = []
    if property_id is not None:
        filtri.append(GuestRequest.property_id == property_id)
    if status is not None:
        filtri.append(GuestRequest.status == status)

    # email SINTESTICHE (DA-3). category/draft_reply: NULL finche' D15.
    stmt = (
        CAMPI_GUEST_REQUEST.where(*filtri)
        .order_by(GuestRequest.received_at.desc(), GuestRequest.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    )
    stmt_totale = select(func.count()).select_from(GuestRequest).where(*filtri)
    with Session(engine) as session:
        righe = session.execute(stmt).all()
        totale = session.execute(stmt_totale).scalar_one()

    dati = []
    for r in righe:
        dati.append(
            {
                "id": r.id,
                "property_id": r.property_id,
                "received_at": r.received_at,
                "body": r.body,
                "category": r.category,
                "draft_reply": r.draft_reply,
                "status": r.status,
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


@router.patch("/api/guest-requests/{id}", dependencies=[Depends(auth.require_write_role)])
def update_guest_request(id: Annotated[int, Path(ge=1)], body: GuestRequestUpdate):
    with Session(engine) as session:
        riga = session.execute(CAMPI_GUEST_REQUEST.where(GuestRequest.id == id)).one_or_none()
        if riga is None:
            raise HTTPException(404)
        if body.status is not None and (riga.status, body.status) not in TRANSIZIONI:
            raise HTTPException(422, f"Invalid status transition: {riga.status} -> {body.status}.")
        if body.status is None and riga.status == "sent":
            # sent e' terminale: dopo l'invio non si modifica piu' niente (HITL)
            raise HTTPException(422, "Guest request already sent.")

        # category/urgency non sono scrivibili dallo schema: non si toccano.
        # Nessuna transizione implicita: lo status cambia solo se nel body.
        valori: dict[str, str] = {}
        if body.status is not None:
            valori["status"] = body.status
        if body.draft_reply is not None:
            valori["draft_reply"] = body.draft_reply
        session.execute(update(GuestRequest).where(GuestRequest.id == id).values(**valori))
        session.commit()
        aggiornata = session.execute(CAMPI_GUEST_REQUEST.where(GuestRequest.id == id)).one()
        return {
            "id": aggiornata.id,
            "property_id": aggiornata.property_id,
            "received_at": aggiornata.received_at,
            "body": aggiornata.body,
            "category": aggiornata.category,
            "draft_reply": aggiornata.draft_reply,
            "status": aggiornata.status,
        }
