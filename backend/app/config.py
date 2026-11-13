import os

# stessi valori del docker-compose
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://buby:buby@localhost:5432/buby",
)
