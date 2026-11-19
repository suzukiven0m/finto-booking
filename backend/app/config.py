import os

# stessa fonte del docker-compose: se cambi POSTGRES_PORT o le credenziali
# nel .env, l'app segue. DATABASE_URL vince su tutto se e' impostata.
_user = os.getenv("POSTGRES_USER", "buby")
_password = os.getenv("POSTGRES_PASSWORD", "buby")
_db = os.getenv("POSTGRES_DB", "buby")
_port = os.getenv("POSTGRES_PORT", "5432")
_host = os.getenv("POSTGRES_HOST", "localhost")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+psycopg://{_user}:{_password}@{_host}:{_port}/{_db}",
)

# Utenti demo hardcoded (decisione pre-freeze S7: niente tabella users in v1).
# Le password e il JWT_SECRET qui sotto sono default di sviluppo PUBBLICATI in
# docs/api-contract.md, non segreti. Una tabella users vera piu' avanti =
# protocollo contract-bump (nuovo ADR + bump info.version + migrazione).
DEMO_USERS = {
    "admin@buby.travel": {"password": "demo", "role": "admin"},
    "manager@buby.travel": {"password": "demo", "role": "manager"},
    "property.manager@buby.travel": {"password": "demo", "role": "property_manager"},
}

JWT_SECRET = os.getenv("JWT_SECRET", "buby-dev-jwt-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 8
