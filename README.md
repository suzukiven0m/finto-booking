# finto-booking (Buby Travel)

Fictional booking app for Caso 1 (Turismo). FastAPI + PostgreSQL backend, React + Vite frontend.
Decisions live in `docs/adr/`, the working plan in `docs/plan.md` and `docs/delivery-plan.md`.

## Status

Done and verified:
- Postgres schema v1: 5 tables, migrations 0001-0005, schema tests (`backend/`)
- Data pipeline: bookings, TripAdvisor reviews (1,638, English-only), 800 synthetic emails, daily KPIs (`data/etl/`)
- OpenAPI v1 contract: `openapi.yaml` (single source of truth, mirrored in `frontend/mock/`); S1–S3 fixed pre-freeze (PR #11)
- FastAPI app (PR #9): 4 of 11 contract operations on real data — properties,
  kpis/summary, kpis/daily, auth/login (fake token until D11; secured endpoints
  do not enforce it yet)
- Login UI (PR #10) against the fake login
- Dashboard shell (D10) running on the Prism mock (D6) until the D17 swap, see `frontend/README.md`

Not built yet: the remaining 7 contract operations (WP8), real JWT auth +
enforcement (D11/WP7), review NLP (D14), email assistant (D15), forecast
(D16, stretch).

## Layout

```text
finto-booking/
├── backend/     FastAPI app, schema, migrations, tests   (WSA-1)
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

### 4. API (real data)

With the database seeded (step 3), from `backend/` with the venv of step 2
(requirements now include fastapi/uvicorn/httpx2):

```bash
uvicorn app.main:app --port 8000
```

4 of 11 contract operations are implemented (properties, kpis/summary,
kpis/daily, auth/login). The login returns a fake token until D11 and secured
endpoints accept any/no token for now. `avvia.sh` (Mac/Linux) / `avvia.bat`
(Windows) at the repo root start database + API + dashboard in one command
(provisional, until compose covers API/web).

### 5. Frontend demo

Default: no backend needed, it runs against the Prism mock:

```bash
cd frontend
npm install
npm run demo        # mock on :4010 + Vite on :5173
```

To point the dashboard at the real API instead, set the `VITE_API_BASE_URL`
seam (`frontend/src/api/client.ts` defaults to `http://localhost:4010`):

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

Open http://localhost:5173. More in `frontend/README.md`.

## Data

Full datasets stay on the client drive, not in the repository. Only trimmed samples are
committed under `data/raw/` (see `.gitignore`), so a fresh clone can run the pipeline
without large downloads. The sample baseline (5,000 bookings) differs from the full
baseline (61,777 valid bookings, €22,976,960.13 revenue); both are documented in
`docs/data-dictionary.md`.