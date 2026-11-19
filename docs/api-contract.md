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
  `manager`, `property_manager` (ADR 0001). **Enforcement implemented
  (D11/WP7, 2026-11-19):** `POST /api/auth/login` validates credentials
  against the demo users and issues an HS256 JWT (claims `sub`, `role`,
  `exp`; 8 h expiry); wrong/unknown credentials answer 401
  `invalid_credentials` per the login example. Secured routes answer the
  `Unauthorized` (401) envelope without a token or with a
  missing/malformed/expired/invalid one. `/api/properties` and
  `/api/auth/login` stay open (`security: []`).
  **Role matrix (fixed pre-freeze 2026-11-19, operator-approved):** all
  three roles may read every secured GET — no property-scoping of reads
  in v1; WRITE on guest-requests (`PATCH /api/guest-requests/{id}`)
  requires `admin` or `manager`, enforced by the `require_write_role`
  dependency (`property_manager` receives the declared `Forbidden` 403
  envelope); PATCH enforcement lands with the operation in WP8.
  **Demo users (S7: no users table in v1), hardcoded in
  `backend/app/config.py`:** `admin@buby.travel`, `manager@buby.travel`,
  `property.manager@buby.travel` — password `demo` for all three. These
  passwords and the dev-default JWT secret (`buby-dev-jwt-secret`,
  overridable via the `JWT_SECRET` env var) are **published dev defaults,
  NOT secrets**. A real users table later = contract-bump protocol (new
  ADR + `info.version` bump + dedicated migration).
- **Pagination** (list endpoints): query `page` (int, default 1, min 1)
  and `page_size` (int, default 50, min 1, max 200). Envelope:
  `{ "data": [...], "meta": { page, page_size, total, total_pages } }`.
- **Errors** (all 4xx/5xx): `{ "error": { code, message, details? } }`.
  Shared responses: `NotFound`, `Unauthorized`, `Forbidden`,
  `ValidationError` in `components.responses`.
- **Common filters:** `property_id` (1 = Buby Lago, 2 = Buby Montagna;
  omitted/null = both), `date_from` / `date_to` (ISO dates, inclusive,
  on `arrival_date`; for `getKpiDaily` the bounds filter `kpi_daily.date`
  — stay days — instead).
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
