# Buby Travel — Delivery Plan

- **Written:** 2026-11-09 (Mon)
- **SAL 1:** 2026-11-20 (Fri) — schema + API contract frozen, client present. **9 working days** (Nov 9-19, weekends excluded).
- **Final demo:** 2026-12-18 (Fri). **39 days.**
- **Team:** 3 WSA + 3 Data/AI, students.
- **Sources of truth:** `docs/plan.md`, `docs/adr/0001`, `docs/adr/0002`, brief PDF, `Datasets/hotel_bookings.csv`.

---

## 0. Verdict — read this first

The project is **behind its own Sprint 0 exit criteria, which are due tomorrow.** Repo is docs-only: zero source files. ADRs 0001, 0002 and 0003 all accepted (0001/0002 on 2026-11-11, 0003 on 2026-11-13). Meanwhile the dataset cannot satisfy two mandatory deliverables.

Three facts, all computed from the raw CSV:

| Fact | Evidence | Consequence |
|---|---|---|
| No review/rating/score column | 0 of 32 headers qualify | Reputation dashboard has **no data source** |
| No free-text column | every field <12 chars avg, all codes/numerics | Mandatory NLP component has **no input** |
| No room-inventory column | only `reserved_room_type`/`assigned_room_type` | Occupancy and RevPAR need an **invented denominator** |

The brief requires "almeno una componente di elaborazione di testi/email" and a reputation dashboard. `hotel_bookings.csv` alone cannot deliver either. **This must be decided today, not discovered in December.**

### What the dataset actually is

Not "hotels on lake and mountains". It is the public Kaggle *Hotel Booking Demand* set: a Portuguese **City Hotel** (79,330) and **Resort Hotel** (40,060), 2015-07 → 2017-08.

| Property | Rows | Cancel rate |
|---|---:|---:|
| City Hotel | 79,330 | 41.73% |
| Resort Hotel | 40,060 | 27.76% |

**Decision D0 (today):** map the two hotel types to two fictional Buby properties — *Buby Lago* ← Resort, *Buby Montagna* ← City — in a `properties` table, and declare the substitution in the data dictionary and at SAL 1. Do not pretend it is real Buby data.

### Clean baseline (the seed script must reproduce these)

After exact dedup (87,396 rows) and filtering to `is_canceled=0, nights>0, adr>0`:

| Metric | Value |
|---|---:|
| Valid bookings | 61,777 |
| Room-nights | 218,410 |
| Realized revenue | €22,976,960.13 |
| ADR | €105.20 |
| Cancellation (post-dedup) | 27.49% |

Any KPI endpoint that does not match these numbers is wrong.

### KPI definitions — pin these before anyone writes a query

The auditor showed the same metric swings 10-40% on definition alone. Every headline number must carry its rule in the data dictionary, or it gets contradicted on recompute.

| KPI | Rule | Trap |
|---|---|---|
| Cancellation rate | Canceled only, after dedup. **No-Show reported separately.** | 37.04% raw vs 27.49% dedup vs 27.98% if No-Show folded in |
| ADR | Revenue / room-nights, over `adr > 0` only. Report median alongside. | Mean 101.83 is skewed by a 5400.0 typo and 1,959 zeros |
| Revenue | `adr × nights`, non-canceled only | 42.72M gross vs 25.996M realized vs 22.98M realized+dedup |
| Seasonality | Month-of-year **averages**, never raw monthly totals | 2015 and 2017 are partial years; raw totals mislead |
| Channel mix | By `market_segment` (8 values) | `agent`/`company` are unmapped numeric IDs — no named OTA breakdown possible |
| Occupancy / RevPAR | Against assumed capacity (§6) | Never present as measured |

---

## 1. Blockers to clear today (Nov 9, ~2 hours)

| # | Action | Owner | Done when |
|---|---|---|---|
| B1 | **Vote ADR 0001.** ✅ **Done 2026-11-11: Option A (FastAPI + React), 6/6.** | All 6 | ADR 0001 says "Accettato" |
| B2 | **Vote ADR 0002.** ✅ **Done 2026-11-11: Option A (Postgres only), 6/6.** | All 6 | ADR 0002 says "Accettato" |
| B3 | **Decide the reviews/text gap.** ✅ **Done 2026-11-13: ADR 0003 option E (`hotel_bookings.csv` + TripAdvisor), 6/6.** | All 6 | ADR 0003 says "Accettato" |
| B4 | **Confirm data request was sent to client in writing.** | Team lead | Copy in `docs/` or client drive |
| B5 | Scaffold monorepo skeleton + `docker-compose` up. | WSA-3 | `docker compose up` gives a reachable Postgres |
| B6 | **Commit the dataset to `data/raw/`.** It exists only on `origin/fabio`, not on master. | DA-1 | `Datasets/hotel_bookings.csv` on master; nobody can seed without it |

### B3 — the reviews/text decision ✅ **Decided 2026-11-13: option E**

| Option | Effort | Risk | Verdict |
|---|---|---|---|
| A. Ask client for real reviews + emails | 0 dev, unknown latency | Data may not exist | **Do this anyway, day 1** |
| B. Generate synthetic corpus linked to bookings | ~1 day (DA-2) | Must be declared as synthetic | **Rejected for reviews** — kept for emails only |
| C. Drop reputation + NLP from scope | 0 | Fails a mandatory brief deliverable | **Reject** |
| E. `hotel_bookings.csv` + TripAdvisor | ~2 days (DA-2) | Property-level link is asserted, not factual | **Accepted, 6/6** |

**Decision: option E.** Bookings come from `hotel_bookings.csv`; reviews and text come from the TripAdvisor corpus (`jniimi/tripadvisor-review-rating`). Both real. The per-dimension score the brief requires exists natively in that corpus, so nothing is synthesised. Full rationale, weighted scoring and the seven-step plan: `docs/adr/0003-data-sources.md`.

**The link is asserted, not factual.** A 2012 TripAdvisor reviewer is not the guest of a 2016 booking. Binding on the data dictionary and the SAL 1 slide:

- occupancy and revenue KPIs come **only** from `hotel_bookings.csv`;
- reputation KPIs come **only** from TripAdvisor;
- no joint analysis at the individual-booking level is legitimate;
- joint analysis at **property and month** level is legitimate, with the assumption stated.

Presenting the join as factual is the one way to make this option indefensible.

**Emails stay synthetic.** No public source provides guest emails, so option B survives for that corpus only (DA-3, 800 rows, 6 categories).

Corpus shape:

| Corpus | Rows | Source | Shape |
|---|---:|---|---|
| Reviews | 20,000 | TripAdvisor, `lang == "__label__en"`, balanced by `hotel_id`, `random_state=42` | `ta_hotel_id`, `post_date`, `stay_year`, `overall`, `cleanliness`, `value`, `location`, `rooms`, `sleep_quality`, `title`, `body`, `lang` |
| Emails | 800 | synthetic (DA-3) | 6 categories: `availability`, `cancellation`, `complaint`, `special_request`, `billing`, `info`. Fields: `body`, `category`, `draft_reply`, `status` |

Reviews are sampled to `data/raw/tripadvisor_sample.csv` (~3 MB) and **that** is committed; the 952 MB pickle is not. Loader: `docs/adr/0003-data-sources.md` §2.

**Anti-leakage rule (emails only):** `true_category` and `true_urgency` live only in `data/eval/email_gold.csv`. They are never written to the database and never read by the pipeline. DA-3 scores predictions against the gold file. Leaking them into the DB turns a real evaluation into a tautology.

**Review evaluation is honest by construction.** The five dimensions and `overall` are real guest scores, not model output, so they work as weak labels: correlate predicted sentiment against the real score. No generator to defend.

---

## 2. Deliverables

Each is a thing a student codes, not a theme.

| ID | Deliverable | Owner | Lands |
|---|---|---|---|
| D1 | Monorepo scaffold + docker-compose (Postgres, API, SPA) | WSA-3 | Nov 10 |
| D2 | PostgreSQL schema v1 + Alembic migration | WSA-1 | Nov 11 |
| D3 | ETL v0: CSV → dedup → clean → load | DA-1 | Nov 12 |
| D4 | Seed script reproducing the clean baseline | DA-1 | Nov 13 |
| D5 | OpenAPI v1 spec (`openapi.yaml`) | WSA-1 + DA-1 | Nov 16 |
| D6 | Mock server from spec | WSA-3 | Nov 17 |
| D7 | KPI engine (occupancy, ADR, RevPAR, channels, seasonality) | DA-1 | Nov 18 |
| D8 | TripAdvisor review sample + loader (20k rows) | DA-2 | Nov 17 |
| D9 | Synthetic guest-email corpus generator | DA-3 | Nov 17 |
| D10 | Dashboard shell (React) consuming the mock | WSA-2 | Nov 18 |
| D11 | Auth: JWT login, 3 roles | WSA-1 | Nov 27 |
| D12 | KPI API endpoints on real data | WSA-1 | Dec 2 |
| D13 | Reputation dashboard (sentiment, topics, trend) | WSA-2 + DA-2 | Dec 3 |
| D14 | Review NLP: sentiment + multi-label topics + monthly summary | DA-2 | Dec 3 |
| D15 | Email classifier + LLM draft reply (human-in-the-loop) | DA-3 | Dec 3 |
| D16 | Demand forecast baseline (moving average) | DA-3 | Dec 3 |
| D17 | Mock → real swap, E2E test | WSA-3 | Dec 10 |
| D18 | Deploy + docs + demo rehearsal | WSA-3 | Dec 17 |
| D19 | Search/filter UI over bookings | WSA-2 | Dec 2 |
| D20 | Guest-request inbox UI (approve / edit / send) | WSA-2 + DA-3 | Dec 4 |

**Deploy target (decide by Nov 13):** Render (API) + Vercel (SPA) + Neon (Postgres), free tiers. Free tiers sleep — **the demo runs on local `docker compose`, never on a cold-started free instance.** The public URL is for the report and grading; the live demo is local. Warm the deployed instance 10 minutes before any external check.

**Load check** (deliverables per person, after rebalance): WSA-1 4 · WSA-2 4 · WSA-3 4 · DA-1 4 · DA-2 4 · DA-3 3. Balanced.

D19 and D20 fill the gap the brief names explicitly — "dashboard, **ricerca**, visualizzazioni" and the assistant that helps answer guest requests. Without them WSA-2 and DA-3 finish early and the app has no search and no inbox.

---

## 3. Sprint 0 — Nov 9-10 (foundations)

Exit criteria from `docs/plan.md` are due **tomorrow**.

| Day | Item | Owner | Done when |
|---|---|---|---|
| Mon 9 | B1-B5 (§1) | all | ADRs accepted, compose up |
| Tue 10 | D1 repo dirs `/backend /frontend /data /infra /docs`; README with run instructions | WSA-3 | A new member clones and runs in <10 min |

```ascii
finto-booking/
├── backend/     FastAPI app
├── frontend/    React + Vite
├── data/        ETL, generators, notebooks
├── infra/       docker-compose, Dockerfiles
└── docs/        plan, ADRs, contract, dictionary
```

---

## 4. Sprint 1 — Nov 11-19 → SAL 1 freeze

**9 working days, weekends excluded.** No weekend assignments — if the team works Saturday it is a bonus, not a plan.

Everything here exists to make Nov 20 defensible. Ten items in nine days means the spec and mock must be drafted by the people who will build against them, in parallel.

| Day | Item | Owner | Done when |
|---|---|---|---|
| Mon 9 | B1-B5 (§1) | all | ADRs accepted, compose up |
| Tue 10 | D1 scaffold | WSA-3 | `docker compose up` works |
| Wed 11 | D2 schema v1 + ERD | WSA-1 | `alembic upgrade head` creates all tables |
| Thu 12 | D3 ETL v0 | DA-1 | 87,396 rows loaded, duplicates gone |
| Fri 13 | D4 seed + **status to client** | DA-1 | Baseline numbers reproduced exactly |
| Mon 16 | D5 OpenAPI v1 + D8/D9 corpora start | WSA-1 + DA-1, DA-2 | Spec validates; TripAdvisor sample downloaded, email generator sketched |
| Tue 17 | D6 mock server + D8/D9 corpora finish | WSA-3, DA-2 | `GET /api/kpis/*` returns fixtures; 20k reviews loaded, 800 emails |
| Wed 18 | D7 KPI engine + D10 dashboard shell | DA-1, WSA-2 | KPIs match baseline; shell renders mock |
| Thu 19 | **SAL 1 dry run**; fix gaps; tag contract `v1.0.0` | all | Dry run complete, contract frozen |
| **Fri 20** | **SAL 1** | lead | Schema + contract frozen |

**Why this fits:** each of the four heavy days (16-19) pairs one backend item with one data/frontend item, so the six people split 3+3 rather than serialising. D11 (auth) is deferred to Sprint 2 — it is not needed for SAL 1 and would break this schedule.

**The one tight chain — watch it daily:** D5 spec (Mon 16) → D6 mock (Tue 17) → D10 shell (Wed 18) → dry run (Thu 19). Three dependencies in three days, zero slack. If the spec slips past Monday, cut the mock server and point the shell at hard-coded fixtures inside the frontend instead — the contract still freezes on time, which is what SAL 1 grades.

### Schema v1 (student-level, 5 tables)

```ascii
properties(id, name, hotel_type, location_type, room_count,
           ta_hotel_id)                          -- 2 rows, ta_hotel_id from ADR 0003 §1
bookings(id, property_id, arrival_date, nights, adr,
         is_canceled, channel, country, ...)     -- 87,396 rows
reviews(id, property_id, ta_hotel_id, post_date, stay_year,
        overall, cleanliness, value, location, rooms,
        sleep_quality, title, body, lang)        -- 20k, TripAdvisor
                                                 -- NO FK to bookings (ADR 0003 §3)
guest_requests(id, received_at, body, category,
               draft_reply, status)              -- synthetic
kpi_daily(property_id, date, room_nights,
          revenue, adr, occupancy)               -- computed
```

Flat, no star schema. No lookup tables — 178 countries is a plain column. `reviews` carries no `sentiment`/`topics` columns: those are model output, computed at query time or in a derived table, not frozen into the source table.

### Contract freeze checklist (SAL 1)

- [ ] KPI catalog signed by both teams
- [ ] ERD + migration merged
- [ ] `openapi.yaml` v1.0.0 tagged
- [ ] Mock server running from the spec
- [ ] Data dictionary v1 (every column, every assumption)
- [ ] Occupancy assumption documented (see §6)
- [ ] Two-source disclosure written: asserted property-level link, assumed room capacity (see §1 B3)
- [ ] NDA / GDPR status stated, code ownership agreed (O1, O3)
- [ ] Written status sent to client (O5)

---

## 5. Sprint 2 — Nov 20 → Dec 4 (build on mock)

| Week | Focus | Owners | Done when |
|---|---|---|---|
| Nov 20-27 | D12 KPI endpoints on real data; D13 dashboard pages | WSA-1, WSA-2 | Occupancy + revenue dashboards live |
| Nov 27-Dec 4 | D14 NLP, D15 classifier + replies, D16 forecast | DA-2, DA-3 | All MVP features on real data |

**Stretch gate (Dec 4):** only if all MVP is green. Otherwise stretch is cancelled and the last two weeks are hardening.

---

## 6. The occupancy problem — decide it explicitly

No capacity column exists. Occupancy and RevPAR are **undefined** without a denominator.

**Chosen approach:** hard-code an assumed room count per property as a named constant, publish it in the data dictionary and on the dashboard footnote.

```python
# data/kpi/constants.py
CITY_ROOMS = 230      # peak observed concurrent rooms (226) + margin
RESORT_ROOMS = 190    # peak observed concurrent rooms (187) + margin

# occupancy = room_nights_sold / (ROOMS * days_in_period)
```

The auditor flagged the circularity: capacity inferred from peak means occupancy can never exceed 100%. That is acceptable *if labelled an assumption*. It is fraud if presented as measured. The dashboard must carry the footnote.

---

## 7. Sprint 3 — Dec 4-11 (integrate)

| Item | Owner | Done when |
|---|---|---|
| D17 mock → real swap | WSA-3 | Frontend hits real API, no fixtures |
| Contract tests in CI | WSA-1 | CI fails if API drifts from `openapi.yaml` |
| Model evaluation (sentiment accuracy, classifier F1) | DA-2 | Numbers in report |
| Client data swap if it arrived | DA-1 | Same contract, different source |

**Integration starts Dec 4, not the final week.** Weekly real-data smoke test from Sprint 1 onward prevents the classic December collapse.

---

## 8. Sprint 4 — Dec 11-18 (harden)

| Item | Owner | Done when |
|---|---|---|
| D18 deploy | WSA-3 | Public URL works |
| Technical docs: architecture, API, install | WSA-1 | A stranger can run it |
| Data report: KPI findings, model metrics | DA-1 | Numbers + caveats |
| Demo rehearsal ×2 | lead | Runs in under 10 min without errors |
| **Final demo Dec 18** | all | — |

---

## 9. Brief obligations not covered by code

The brief names these explicitly (lines 145-159). They are graded. None are optional.

| # | Obligation | Brief line | Owner | When |
|---|---|---|---|---|
| O1 | **NDA + GDPR + anonymization** agreed with client; emails pseudonymized at ingestion, no PII in repo | 145-146 | lead | Before first email data lands |
| O2 | **AI service access and costs** clarified with client (LLM API keys, who pays) | 147 | DA-3 | By Nov 16, before D15 |
| O3 | **Code / analysis / model ownership** agreed and documented | 147 | lead | By SAL 1 |
| O4 | **Client present at 4 sessions** — kickoff (done, Oct 26), SAL 1 (Nov 20), final (Dec 18), plus one more; confirm which | 146-158 | lead | Confirm by Nov 13 |
| O5 | **Weekly written status** to client drive, every week, by the team lead | 159 | lead (rotating) | Fridays: Nov 13, 20, 27, Dec 4, 11, 18 |
| O6 | **Repository + install instructions** delivered as artefacts, not just a README | 101, 131 | WSA-3 | Dec 17 |

O1 is the one with legal weight. Pseudonymize guest emails before they touch the database — a name or address in a `body` column is a GDPR incident, not a bug.

---

## 10. Risks, ranked by damage

| # | Risk | Evidence | Mitigation |
|---|---|---|---|
| R1 | Brief deliverables unmet: no reviews, no text | 0 of 32 columns | ✅ Closed by ADR 0003 option E (TripAdvisor corpus); emails stay synthetic and disclosed |
| R2 | Occupancy/RevPAR fabricated | no capacity column | Named constants + dashboard footnote |
| R3 | Sprint 0 already late | due Nov 10, nothing built | Clear B1-B6 today |
| R4 | Contract drift after freeze | — | Contract tests in CI |
| R5 | Data cleaning bugs | 8,171 dup groups, 4 `NA` children, 403 `adults=0`, 715 zero-night rows | D4 baseline check as a test |
| R6 | Forecast overpromised | 115 weekly points | Moving average only; say so |
| R7 | Final-week crunch | integration starts Dec 4 | Weekly real-data smoke test |
| R8 | GDPR on emails | brief requires NDA/GDPR | Pseudonymize at ingestion; no PII in repo |
| R9 | Dataset not on master | only on `origin/fabio` | B6: commit to `data/raw/` Nov 10 |
| R10 | Naive KPIs contradict on recompute | cancel 37.04 vs 27.49; revenue 42.72M vs 22.98M | Per-KPI definition table (§0) in the data dictionary |

### Data traps that will bite

| Trap | Count | Fix |
|---|---:|---|
| Exact duplicate rows | 31,994 extra | `drop_duplicates()` first |
| `children` contains literal `NA` | 4 | `pd.to_numeric(errors='coerce')` |
| Zero-night bookings | 715 | Filter `nights > 0` |
| `adults=0` | 403 | Flag or drop |
| Negative / extreme `adr` | 1 / 1 | Clip to `[0, 1000]` |
| `arrival_date_week_number` not ISO | 64,054 differ | Derive ISO week from the date |
| `reservation_status` duplicates `is_canceled` | all rows | Keep `is_canceled` only |

---

## 11. If you fall behind — cut in this order

20 deliverables for 6 students in 39 days is tight. When something slips, cut from the top of this list, never from the bottom.

| Cut order | Item | Why it is safe to cut |
|---:|---|---|
| 1 | D16 demand forecast | Brief calls predictive modelling "eventuale" (optional) |
| 2 | D20 guest-request inbox UI | The classifier can be shown via API/notebook; UI is polish |
| 3 | D19 search / filter UI | Dashboard already proves the brief's "visualizzazioni" |
| 4 | D11 auth | Demo does not need a login wall; adds nothing to grading |

**Never cut:** D12/D7 (KPI), D14 (NLP), D15 (classifier), D17 (real data), D18 (deploy). Those are the graded minimum — the brief's "almeno una componente di analisi e una di elaborazione testi".

If by Dec 4 the MVP is green, add stretch from `docs/plan.md` §Stretch in order: forecast → pricing view → RAG assistant.

---

## 12. Definition of done (Dec 18)

- [ ] App deployed, public URL, login works
- [ ] Occupancy + revenue dashboard on real (cleaned) data
- [ ] Reputation dashboard on real TripAdvisor reviews, property-level link disclosed as asserted
- [ ] Search / filter over bookings (brief line 97: "dashboard, ricerca, visualizzazioni")
- [ ] Email classifier + LLM draft reply, human approves before send
- [ ] Guest-request inbox with approve / edit / send
- [ ] Data dictionary with every assumption stated
- [ ] Contract tests green in CI
- [ ] Report with KPI findings and model metrics
- [ ] NDA / GDPR status documented; no PII in repo (O1)
- [ ] Code / model ownership documented (O3)
- [ ] Repository + install instructions delivered (O6)
- [ ] Demo rehearsed twice
