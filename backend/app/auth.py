import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app import errors
from app.config import DEMO_USERS, JWT_ALGORITHM, JWT_EXPIRY_HOURS, JWT_SECRET

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/api/auth/login")
def login(body: LoginRequest):
    user = DEMO_USERS.get(body.email)
    if user is None or not secrets.compare_digest(
        user["password"].encode(), body.password.encode()
    ):
        # 401 con il code dell'esempio del contratto per questa rotta
        return errors.errore(401, "invalid_credentials", "Email or password is incorrect.")
    scadenza = datetime.now(UTC) + timedelta(hours=JWT_EXPIRY_HOURS)
    token = jwt.encode(
        {"sub": body.email, "role": user["role"], "exp": scadenza},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    return {"access_token": token, "token_type": "bearer", "role": user["role"]}


# bearer JWT su tutte le rotte protette: senza token o con token non valido
# si alza 401, che errors.py veste con l'envelope Unauthorized del contratto
def require_token(request: Request) -> dict:
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(401)
    try:
        return jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub", "role"]},
        )
    except jwt.PyJWTError:
        raise HTTPException(401) from None


# matrice dei ruoli (bearerAuth, approvata dall'operator 2026-11-19):
# admin e manager possono scrivere, property_manager prende il 403 forbidden.
# La usera' PATCH /api/guest-requests/{id} quando arriva in WP8.
WRITE_ROLES = {"admin", "manager"}


def require_write_role(claims: Annotated[dict, Depends(require_token)]) -> dict:
    # role non-stringa (lista/dict nel JWT) = comunque vietato, mai un 500
    if not isinstance(claims.get("role"), str) or claims["role"] not in WRITE_ROLES:
        raise HTTPException(403)
    return claims
