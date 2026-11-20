# finto-booking (Buby Travel)

Fictional booking app for Caso 1 (Turismo). FastAPI + PostgreSQL backend, React + Vite frontend.
Decisions live in `docs/adr/`, the working plan in `docs/plan.md` and `docs/delivery-plan.md`.

## Status

Done and verified:
- Postgres schema v1: 5 tables, migrations 0001-0005, schema tests (`backend/`)
- Data pipeline: bookings, TripAdvisor reviews (1,638, English-only), 800 synthetic emails, daily KPIs (`data/etl/`)
- OpenAPI v1 contract: `openapi.yaml` (single source of truth, mirrored in `frontend/mock/`); S1–S3 fixed pre-freeze (PR #11)
- FastAPI app: all 11 contract operations on real data, JWT auth + role enforcement (D11/WP7/WP8)
- Login UI + dashboard shell (D10–D13, D19–D20): KPI, reputation, bookings, guest-request tabs
- Email classifier + draft replies (D15/WP10)
- Review NLP sentiment/topics (D14/WP9)
- Demand/pricing analysis (WP12)
- **D17 swap done**: frontend talks to real FastAPI by default (`http://localhost:8000`)
- E2E smoke in CI: seed → uvicorn → real HTTP assertions → restore

## Layout

```text
finto-booking/
├── backend/     FastAPI app, schema, migrations, tests   (WSA-1)
├── frontend/    React + Vite dashboard     (WSA-2)
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
PYTHONPATH=backend:data backend/.venv/bin/python data/etl/classify_emails.py --persist
```

The last step is D15: it classifies the 800 synthetic emails and writes
category/urgency/draft_reply with `status=draft` — the inbox tab and the E2E
smoke below expect this post-D15 state.

All steps are idempotent. Details and full-dataset runs: `docs/playbooks/solo-dataset.md`.

### 4. API (real data)

With the database seeded (step 3), from `backend/` with the venv of step 2:

```bash
cd backend
uvicorn app.main:app --port 8000
```

All 11 contract operations are live. JWT auth is enforced; demo credentials:
`admin@buby.travel`, `manager@buby.travel`, `property.manager@buby.travel`
— password `demo` for all three (published dev defaults, see `docs/api-contract.md`).

`avvia.sh` (Mac/Linux) / `avvia.bat` (Windows) start database + API +
frontend in one command.

### 5. Frontend (real API)

Requires the backend running (step 4):

```bash
cd frontend
npm install
npm run dev        # Vite on :5173, default base URL → http://localhost:8000
```

Open http://localhost:5173 and log in with any demo account (see step 4).
`VITE_API_BASE_URL` overrides the default; `http://localhost:8000` is
baked in by default. More in `frontend/README.md`.

#### Optional: Prism mock (contract development only)

Prism lets you iterate on API shapes without the backend. It is **not** the
demo path:

```bash
cd frontend
VITE_API_BASE_URL=http://localhost:4010 npm run demo   # mock on :4010 + Vite on :5173
```

## Weekly real-data smoke

After seeding the full dataset (see `docs/playbooks/solo-dataset.md`, plus
the D15 classify step of step 3 above) and starting uvicorn on `:8000`, run
the E2E smoke script against the live DB:

```bash
# with the backend venv active (steps 2–3 above)
cd backend
uvicorn app.main:app --port 8000 &
cd ..
python backend/tests/e2e_smoke.py
kill %1   # stop uvicorn
```

Expected full-DB output (61,777 valid bookings):

```
→ login (manager demo)
→ kpis/summary baseline
→   full DB detected: assertions passed (61777/22976960.13/218410/105.20/0.2749/0.6558/68.99)
→ kpis/daily meta
→   meta.total=793, total_pages=80
→ reviews/summary per-property
→   property_id=1 count=762 overall=3.86 ✓
→   property_id=2 count=876 overall=4.4 ✓
→ reviews list
→   meta.total=1638
→ bookings list
→   meta.total=87396
→ guest-requests (post-D15)
→   50 items, all category set + status=draft
→ PATCH row 1: draft→sent
→   row 1 → sent ✓
→ RESTORE row 1 to draft via SQL
→   row 1 restored: 800 draft / 0 sent ✓
→ 401 no-token check
→   401 without token ✓
→ properties open
→   ['Buby Lago', 'Buby Montagna'] ✓
All E2E assertions passed.
```

Final state invariant: all 800 guest_requests in `draft` status, 0 `sent`.

## Data

Full datasets stay on the client drive, not in the repository. Only trimmed samples are
committed under `data/raw/` (see `.gitignore`), so a fresh clone can run the pipeline
without large downloads. The sample baseline (5,000 bookings) differs from the full
baseline (61,777 valid bookings, €22,976,960.13 revenue); both are documented in
`docs/data-dictionary.md`.