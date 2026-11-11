# finto-booking — Buby Travel

Fictional booking app for Caso 1 (Turismo). FastAPI + PostgreSQL backend, React + Vite frontend.
Decisions live in `docs/adr/`, the working plan in `docs/plan.md` and `docs/delivery-plan.md`.

## Layout

```
finto-booking/
├── backend/     FastAPI app        (WSA-1)
├── frontend/    React + Vite       (WSA-2)
├── data/        ETL, generators    (DA-1, DA-2, DA-3)
├── infra/       docker-compose, Dockerfiles, CI   (WSA-3)
└── docs/        plan, ADRs, contract, data dictionary
```

## Run it locally

Requires Docker with Compose. Nothing else.

```bash
git clone <repo-url> && cd finto-booking
docker compose -f infra/docker-compose.yml up -d
docker compose -f infra/docker-compose.yml ps      # postgres -> healthy
docker exec -it buby-postgres psql -U buby -d buby -c 'select version();'
```

Connection string: `postgresql://buby:buby@localhost:5432/buby`
Override user, password, database or host port by copying `.env.example` to `.env`.

Stop it with `docker compose -f infra/docker-compose.yml down`.
Add `-v` only when you mean to delete the database volume.

## Data

Full datasets stay on the client drive, not in the repository. Only a trimmed sample is committed
under `data/raw/` (see `.gitignore`), so a fresh clone can run the pipeline without a 24 MB download.
