# Freeze checklist — SAL 1 (ven 2026-11-20)

Mappa i requisiti della checklist di freeze (`docs/delivery-plan.md` §4
«Contract freeze checklist») alle evidenze. Verifiche tecniche eseguite il
2026-11-19 e registrate nei record WP (`docs/reviews/2026-11-19-wp*.md`);
le azioni umane restano aperte nel ledger (`docs/reviews/human-actions.md`).
**Nessuna azione umana è dichiarata fatta: il freeze è effettivo al SAL 1 con
sign-off e tag.**

| Requisito (delivery-plan §4) | Evidenza | Stato |
|---|---|---|
| KPI catalog signed by both teams | `docs/sal1/kpi-signoff.md` pronto: 6 owner nominati, campi data/firma **vuoti** | Aperto — firmano gli umani al SAL 1 (HA-01) |
| ERD + migration merged | `docs/erd.md` + migrazioni 0001–0005 mergiate (0005: PR #12). **Schema test 12 passed + `alembic check` pulito + round-trip e inverso a un passo su scratch DB** (`wp2_rev_scratch`, creato→testato→droppato; DB seedato mai toccato), eseguiti oggi — record WP2 §3; riverificati sul merged master `cc732bf` | Evidenza OK (record WP2) |
| `openapi.yaml` v1.0.0 tagged | Il tag `v1.0.0` lo applica l'orchestratore **dopo il merge** del pacchetto SAL 1 | **Pending merge** — non ancora applicato |
| Mock server running from the spec | Prism serve la baseline (summary `occupancy_avg 0.6558` / `revenue 22976960.13`, **401 senza token**); mirror `frontend/mock/openapi.yaml` **byte-identico**; lint Redocly **0 errori** (4 warning preesistenti) — record WP1 §3 | Evidenza OK (record WP1) |
| Data dictionary v1 (every column, every assumption) | `docs/data-dictionary.md`: §2 ogni campo, §1 Assunzioni 1–5 + decisione TripAdvisor + S4, §3 regole KPI + baseline, decisioni pre-freeze S7/S8 | Evidenza OK |
| Occupancy assumption documented | Dizionario Assunzione 3 (190/230, picco + margine, circolarità dichiarata, mai misurata) + delivery-plan §6 + footnote dashboard | Evidenza OK |
| Two-source disclosure written (asserted link, assumed capacity) | Slide disclosure **dedicata** (`docs/sal1/slides-outline.md`, slide 12: tutte le assunzioni §1 + S4 + auth D11) + dizionario §1 + ADR 0003 «Punto debole» (correzione S4) + stato O5 | Evidenza OK |
| NDA / GDPR status stated, code ownership agreed (O1, O3) | Mitigazione tecnica documentata e verificata (email sintetiche, niente PII nel repo: dizionario §1/§4); **accordo con il cliente non archiviato** | Aperto — 🔴 O1/O3 (HA-06/HA-07) |
| Written status sent to client (O5) | Testo finale send-ready `docs/sal1/o5-status.md` (gap 13 nov riconosciuto); invio + archiviazione copia = azioni umane | Aperto — 🟡 da inviare e archiviare (HA-02); nulla inviato |

## Evidenze aggiuntive pre-freeze (eseguite oggi, record WP)

| Verifica | Evidenza | Stato |
|---|---|---|
| Esempi del contratto = DB reale | TestClient PR #9 sul DB pieno: summary == **tutti e 7** i campi pinned (61777 / 22976960.13 / 218410 / 105.20 / 0.2749 / 0.6558 / 68.99); **27 passed, 1 skipped** (lo skip è il baseline-campione sul DB pieno, per design); merged master: backend 28 passed 1 skipped + data 12 passed — record WP3 §2 | Evidenza OK (record WP3) |
| Decisioni S7/S8 registrate | Dizionario §2 «Decisioni pre-freeze 2026-11-19» + ADR 0001 «Seguito»: niente tabella users in v1 (demo users hardcoded al momento di D11), output NLP al momento della query; `guest_requests.urgency` in 0005 — record WP2 §1 | Evidenza OK (record WP2) |
| CI verde | GitHub Actions: backend (lint pinnato, migrazioni, alembic check, schema test, round-trip, inverso a un passo, seed + data test) + GitGuardian, verdi su master e sulle PR mergiate (#9/#10/#11/#12) — audit §4, record WP1/WP2/WP3 | Evidenza OK |
| Disclosure complete nelle slide | Slide 12 copre: strutture fittizie, legame asserito, capacità assunta, email sintetiche, **S4 zero overlap 2012 vs 2015–17**, solo inglese, N=1.638, nessun dato cliente (B4 pending); tabella di copertura in fondo all'outline | Evidenza OK (WP5) |

---

*Preparato da WP5 (2026-11-19). Il freeze si chiude al SAL 1: sign-off umano
(HA-01) + tag `v1.0.0` applicato dall'orchestratore post-merge (pending).
Nessuna riga umana viene chiusa da un agent.*
