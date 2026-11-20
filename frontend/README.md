# Buby Travel — frontend (D10 dashboard shell + D17 real-data)

React 18 + TypeScript + Vite + Tailwind CSS + Recharts (ADR 0001).
Talks to the real FastAPI backend by default (see root `README.md` for the
full startup sequence).

## Run the demo (real API)

The demo path requires the real backend running on `http://localhost:8000`.
Follow steps 1–4 of the root README (postgres → alembic → seed → uvicorn),
then:

```bash
cd frontend
npm install
npm run dev        # Vite dev server on :5173, points at http://localhost:8000
```

Open http://localhost:5173 and log in with any demo account:

| Email | Password | Role |
|---|---|---|
| `admin@buby.travel` | `demo` | admin |
| `manager@buby.travel` | `demo` | manager |
| `property.manager@buby.travel` | `demo` | property_manager |

The shell renders the KPI summary cards, the daily revenue/occupancy chart,
the reputation tab, the bookings search tab, and the guest-request inbox tab,
all from the real seeded database.

Individual commands:

| Command | What it does |
|---|---|
| `npm run dev` | Vite dev server (:5173, default → `http://localhost:8000`) |
| `npm run build` | Typecheck + production build |
| `npm run preview` | Serve the production build |
| `npm run typecheck` | `tsc --noEmit` |
| `npm test` | API client tests (vitest, 19 tests) |

The `VITE_API_BASE_URL` env var overrides the default API base; `npm run dev`
without it uses `http://localhost:8000`.

## Optional: Prism mock (contract development only)

Prism lets you run the frontend without the backend by serving the OpenAPI
spec as a mock. Use it for contract-first development or when iterating on
API shapes before the backend is available:

```bash
# terminal 1 — Prism mock on :4010
npm run mock

# terminal 2 — Vite pointed at the mock
VITE_API_BASE_URL=http://localhost:4010 npm run dev
```

Or, in one command:

```bash
npm run demo        # Prism mock on :4010 + Vite dev server on :5173
```

The mock accepts any credentials, returns the OpenAPI baseline examples, and
does **not** reflect changes to the real database. It is not the demo path
for graded delivery.

## Mock contract

`mock/openapi.yaml` is a synced copy of the canonical root `openapi.yaml` (D5,
contract v1 — `docs/data-dictionary.md` §3 baseline). The root spec is the single
source of truth: after any contract change regenerate this copy from it
(`cp ../openapi.yaml mock/openapi.yaml`). Field names, types and baseline
examples are binding.

Disclosures (also shown in the dashboard footer): occupancy/RevPAR use assumed
capacity (190/230 rooms, not measured); the reviews↔bookings link is asserted
at property level, not factual; guest-request emails are synthetic and the two
properties are fictional.
