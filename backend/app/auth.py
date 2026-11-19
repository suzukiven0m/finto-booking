from fastapi import APIRouter
from pydantic import BaseModel

# LOGIN FINTO per provare la dashboard: accetta qualsiasi email e password.
# quello vero (tabella users, password, token jwt, ruoli) lo facciamo dopo

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/api/auth/login")
def login(body: LoginRequest):
    return {
        "access_token": "token-finto",
        "token_type": "bearer",
        "role": "manager",
    }
