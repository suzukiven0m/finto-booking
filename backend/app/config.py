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
