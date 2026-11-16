# Buby Travel — frontend (D10 dashboard shell + D6 Prism mock)

React 18 + TypeScript + Vite + Tailwind CSS + Recharts (ADR 0001).
Self-contained: runs against the Prism mock without the backend.

## Run the demo

All npm commands live here in `frontend/`, not at the repo root (there is no
root package.json).

```bash
cd frontend
npm install
npm run demo        # Prism mock on :4010 + Vite dev server on :5173
```

Open http://localhost:5173. The shell renders the KPI summary cards and the
daily revenue/occupancy chart from the mock's baseline examples.

Individual commands:

| Command | What it does |
|---|---|
| `npm run dev` | Vite dev server (:5173) |
| `npm run mock` | Prism mock of `mock/openapi.yaml` (:4010) |
| `npm run build` | Typecheck + production build |
| `npm run preview` | Serve the production build |
| `npm run typecheck` | `tsc --noEmit` |
| `npm test` | API client tests (vitest) |

`VITE_API_BASE_URL` (default `http://localhost:4010`) points the client at the
real FastAPI backend (`http://localhost:8000`) once D12 lands. The client logs
in via `/api/auth/login` (the mock accepts any credentials) and sends the
bearer token; real JWT issuance is D11.

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