# finto-booking (Buby Travel)

Fictional booking app for Caso 1 (Turismo). FastAPI + PostgreSQL backend, React + Vite frontend.
Decisions live in `docs/adr/`, the working plan in `docs/plan.md` and `docs/delivery-plan.md`.

## Status

Done and verified:
- Postgres schema v1: 5 tables, migrations 0001-0004, schema tests (`backend/`)
- Data pipeline: bookings, TripAdvisor reviews, 800 synthetic emails, daily KPIs (`data/etl/`)
- OpenAPI v1 contract: `openapi.yaml` (single source of truth, mirrored in `frontend/mock/`)
- Dashboard shell (D10) running on the Prism mock (D6), see `frontend/README.md`

Not built yet: API endpoints and JWT auth (D11/D12), review NLP (D14),
email assistant (D15), forecast (D16). The backend is schema + migrations only,
there is no FastAPI app to run yet.

## Layout

```text
finto-booking/
├── backend/     schema, migrations, tests   (WSA-1)
├── frontend/    React + Vite, Prism mock    (WSA-2)
├── data/        ETL, generators, tests      (DA-1, DA-2, DA-3)
├── infra/       docker-compose (Postgres)   (WSA-3)
└── docs/        plan, ADRs, contract, data dictionary
   .github/      CI workflows                (WSA-3)
```

## Run it locally

### 1. Database

Requires Docker with Compose.

```bash
git clone <repo-url> && cd finto-booking
docker compose -f infra/docker-compose.yml up -d
docker compose -f infra/docker-compose.yml ps      # postgres -> healthy
```

Connection string: `postgresql://buby:buby@localhost:5432/buby`
To override user, password, database or host port, copy `.env.example` to
`infra/.env`. Compose reads `.env` from the compose file's folder, a root `.env`
is ignored.

Stop it with `docker compose -f infra/docker-compose.yml down`.
Add `-v` only when you mean to delete the database volume.

### 2. Backend (schema + tests)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m pytest
```

Il backend legge `DATABASE_URL`; se non è impostata, la costruisce dalle stesse
variabili `POSTGRES_*` del compose. Attenzione: `docker compose` legge il `.env`,
il backend legge l'ambiente del processo. Per allinearli esporta le stesse
variabili nell'ambiente (o `DATABASE_URL`) quando lanci il backend come processo
locale.

### 3. Data pipeline

From the repo root, with the backend venv (plus `pip install -r data/requirements.txt`):

```bash
PYTHONPATH=backend backend/.venv/bin/python data/etl/load_bookings.py data/raw/sample_hotel_bookings.csv
PYTHONPATH=backend backend/.venv/bin/python data/etl/load_reviews.py
PYTHONPATH=backend backend/.venv/bin/python data/etl/gen_emails.py
PYTHONPATH=backend backend/.venv/bin/python data/etl/build_kpi_daily.py
```

All steps are idempotent. Details and full-dataset runs: `docs/playbooks/solo-dataset.md`.

### 4. Frontend demo

No backend needed, it runs against the Prism mock:

```bash
cd frontend
npm install
npm run demo        # mock on :4010 + Vite on :5173
```

Open http://localhost:5173. More in `frontend/README.md`.

## Data

Full datasets stay on the client drive, not in the repository. Only trimmed samples are
committed under `data/raw/` (see `.gitignore`), so a fresh clone can run the pipeline
without large downloads. The sample baseline (5,000 bookings) differs from the full
baseline (61,777 valid bookings, €22,976,960.13 revenue); both are documented in
`docs/data-dictionary.md`.