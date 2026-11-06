# Buby Travel — Project Plan

- **Case:** Caso 1 — Turismo: Buby Travel
- **Team:** 3 Web Solutions Architects + 3 Data Analysts / AI Specialists
- **Status:** Starting fresh as of 2026-11-06 (kickoff-equivalent)
- **Hard dates:** SAL 1 — 2026-11-20 (schema + API contract frozen) · Final — 2026-12-18

## Guiding principle

The **data contract is the project's critical path**. Freeze it on Nov 20; from that moment WSA builds against mocks while Data builds the real pipeline; integration happens before the final week, not during it.

## Scope

### MVP (must ship)

1. Data contract + PostgreSQL schema + real seeded data
2. Occupancy/revenue dashboard: occupancy rate, ADR, RevPAR, channel mix, seasonality
3. Reputation dashboard: avg score, volume, sentiment trend, score by dimension
4. Review NLP: sentiment + multi-label topic classification + monthly summary
5. Guest-request/email classifier + LLM-drafted replies (human-in-the-loop)

### Stretch (only if MVP is green by Dec 4)

6. Demand forecast per property × week
7. Rate recommendation / pricing view
8. RAG assistant over reviews + policies + past replies

### Explicitly out of scope unless time allows

- Real OTA integrations, payments, booking engine, multi-language UI, mobile app.

## Compressed calendar

| Window | Dates | Focus | Exit criteria |
|---|---|---|---|
| **Sprint 0 — Foundations** | Nov 6–10 | Requirements recap, data request, repo scaffold, stack vote, KPI catalog | Stack ADR decided; repo runs locally; data requested in writing |
| **Sprint 1 — Contract** | Nov 11–19 | OpenAPI v1, mock server, DB schema, dashboard shell, ETL v0, data dictionary | Contract review + dry-run complete |
| **SAL 1** | **Nov 20** | Present analysis, process, schema, API contract | **Schema + contract frozen** |
| **Sprint 2 — Build** | Nov 20–Dec 4 | Dashboard features, NLP pipeline, forecast baseline, chat UI | Feature-complete on mock data |
| **Sprint 3 — Integrate** | Dec 4–11 | Swap mocks → real data, E2E tests, model evaluation | App runs end-to-end on real data |
| **Sprint 4 — Harden** | Dec 11–18 | Docs, deploy, demo rehearsal, report | **Final demo Dec 18** |

## SAL 1 definition of done (Nov 20)

- [ ] KPI catalog signed off by both teams
- [ ] PostgreSQL schema v1 (ERD + migrations)
- [ ] OpenAPI v1 (endpoints, JSON shapes, pagination, error envelope, auth)
- [ ] Mock server running from the spec; WSA dashboard shell consuming it
- [ ] Data dictionary v1; sample of real data flowing through ETL v0
- [ ] Written status sent to the client

## Workstreams

| Workstream | Owner | Scope |
|---|---|---|
| Backend / API / DB | WSA-1 | Schema, endpoints, auth, contract co-owner |
| Frontend / UX | WSA-2 | Dashboard, search, assistant UI |
| Integration / DevOps | WSA-3 | Docker, CI, deploy, mock→real swap |
| Structured ETL + KPI | DA-1 | Clean data, KPI engine, contract co-owner |
| NLP reviews/emails | DA-2 | Sentiment, topics, summarization, request classification |
| Forecast + AI assistant | DA-3 | Demand forecast, pricing support, RAG assistant |
| Client comms | Team Lead (rotating) | Weekly written status to client drive |

## Weekly rituals

- **Mon:** cross-team sync (30 min) — blockers, contract changes, board review
- **Wed:** integration smoke test — real data through the API
- **Fri:** written status to client + demo of the week's increment

## Top risks

| Risk | Mitigation |
|---|---|
| Data late/incomplete | Request in writing day 1; mock server keeps WSA moving |
| Contract drift | Contract tests in CI; integration owner validates weekly |
| Scope creep | MoSCoW above; freeze at SAL 1; stretch only if green Dec 4 |
| GDPR / email PII | Pseudonymize at ingestion; no PII in repo; document NDA status |
| LLM cost/reliability | Cache, template fallback, human-in-the-loop, evaluate pre-demo |
| Final-week crunch | Integration begins Dec 4; weekly real-data smoke test |

## Next 7 days

1. Send written data request + GDPR/NDA checklist to the client
2. Hold the stack vote (see `docs/adr/0001-tech-stack.md`)
3. Draft KPI catalog and circulate
4. Scaffold monorepo + `docker-compose` (Postgres + API + SPA)
5. Draft OpenAPI v1 and generate the mock server
6. Assign workstream owners and stand up the board
7. Schedule SAL 1 dry-run for Nov 18
