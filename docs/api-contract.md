# API contract v1 — conventions

The canonical contract is [`openapi.yaml`](../openapi.yaml) at the repo
root (OpenAPI 3.0.3, `info.version: 1.0.0`). It freezes at SAL 1
(2026-11-20). KPI rules and the clean baseline live in
`docs/data-dictionary.md` §3; the schema in `docs/erd.md`.

## Conventions

- **Base path:** every route is under `/api`.
- **Servers:** `http://localhost:8000` (real FastAPI, D12) and
  `http://localhost:4010` (Prism mock, D6).
- **Auth:** global `bearerAuth` (HTTP bearer, JWT). Roles: `admin`,
  `manager`, `property_manager` (ADR 0001). Only the scheme is frozen at
  SAL 1; issuance and enforcement are D11. `/api/properties` and
  `/api/auth/login` set `security: []` for the demo.
- **Pagination** (list endpoints): query `page` (int, default 1, min 1)
  and `page_size` (int, default 50, min 1, max 200). Envelope:
  `{ "data": [...], "meta": { page, page_size, total, total_pages } }`.
- **Errors** (all 4xx/5xx): `{ "error": { code, message, details? } }`.
  Shared responses: `NotFound`, `Unauthorized`, `Forbidden`,
  `ValidationError` in `components.responses`.
- **Common filters:** `property_id` (1 = Buby Lago, 2 = Buby Montagna;
  omitted/null = both), `date_from` / `date_to` (ISO dates, inclusive,
  on `arrival_date`).
- **Ratios:** `occupancy`, `cancellation_rate` and `share` are 0-1
  ratios, never percentages.

## Disclosures (binding, also required in the UI)

1. Occupancy and RevPAR use **assumed capacity** (Buby Lago 190 rooms,
   Buby Montagna 230), inferred from observed peaks — not measured.
2. The reviews ↔ bookings link is **asserted at property level**, not
   factual. Reputation KPIs come only from reviews; occupancy/revenue
   only from bookings.
3. `guest_requests` emails are **synthetic**; the two properties are
   **fictional** (1:1 map of the CSV's two hotel types).

## Validate and mock

```bash
npx --yes @redocly/cli@latest lint openapi.yaml
npx --yes @stoplight/prism-cli@latest mock -p 4010 openapi.yaml
curl -H "Authorization: Bearer demo" \
  http://localhost:4010/api/kpis/summary   # returns the clean baseline
```

Lint is clean (0 errors). The remaining warnings are inherent to the
pinned contract: localhost servers are required, no license is declared,
and `GET /api/properties` has no natural 4xx response.