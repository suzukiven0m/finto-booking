# Rehearsal demo ×2 — 2026-11-20 (WP14 / D18)

Registro delle due rehearsal end-to-end richieste da delivery-plan §8 e
HA-12 (ledger: la presenza umana alle rehearsal resta azione umana; questo
documento è l'evidenza tecnica della catena dati, eseguita dall'agent WP14).

- **Script:** `docs/demo-script.md` — l'Appendice A è la catena eseguita,
  passo per passo, con gli stessi endpoint/patch/restore.
- **Mezzo:** sidecar uvicorn (`backend/.venv`, processo host, porta 8000) +
  catena curl/jq contro il DB completo seedato (compose `buby-postgres`,
  healthy). Il percorso dati UI↔API è verificato via API; il frontend è
  verificato a parte (test + typecheck + build, sotto). Il pacing umano dei
  10 minuti è quello delle sezioni temporizzate dello script; la catena API
  gira in ~2 secondi.
- **Ambiente:** branch `fix/wp14-release` (base master @ c51daac); Python
  3.12.8 (venv backend), node v26.13.1, Docker 29.9.3 / Compose 5.7.0.
- **Stato DB prima di ogni run:** 87.396 bookings, 1.638 reviews, 1.605
  kpi_daily, 800 guest_requests tutte `draft` / 0 `sent`.
- **Immagini Docker (build sequenziali, una volta ciascuna, prima delle
  rehearsal):** `buby-api:wp14` OK; `buby-web:wp14` OK (`nginx -t` OK con la
  DNS compose — fuori rete il nome `api` non risolve, atteso).
  `docker compose -f infra/docker-compose.yml config -q` OK.
  **Correzione pass-2 (review P0):** quel bundle aveva base `/api` → doppio
  prefisso `/api/api/*` nel browser; le rehearsal 1–2 sotto hanno verificato
  solo la catena API, non le URL del bundle. Base corretta a `""`, web image
  rebuildata e bundle verificato via proxy: entry 3 in fondo.

## Verifica frontend (host, prima delle rehearsal)

```text
$ npm test -- --run
 ✓ src/session.test.ts (8 tests) 40ms
 ✓ src/api/client.test.ts (11 tests) 49ms
 Test Files  2 passed (2)
      Tests  19 passed (19)

$ npm run typecheck        # tsc --noEmit: nessun errore

$ VITE_API_BASE_URL=http://localhost:8000 npm run build
dist/assets/index-8YI98SS-.css   17.63 kB │ gzip:   4.32 kB
dist/assets/index-DlX2n10t.js   603.55 kB │ gzip: 169.65 kB
✓ built in 2.40s
(warning chunk >500 kB: pre-esistente, non bloccante)
```

## Suite backend + E2E smoke (acceptance WP14)

```text
$ cd backend && .venv/bin/python -m pytest -q
140 passed, 1 skipped in 2.53s
```

E2E smoke con sidecar uvicorn (DB completo rilevato automaticamente):

```text
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

## Intoppi + fix (tutti risolti prima della chiusura)

1. **Snapshot bozza con newline (trovato in pre-run review).** `jq -r` aggiunge
   un newline finale al file di snapshot: il ripristino via PATCH avrebbe
   restituito un testo diverso byte-per-byte. Fix: `jq -j` nell'Appendice A +
   verifica md5 DB-vs-file dopo il restore (aggiunta alla catena).
2. **Id della prima email in inbox.** Lo script diceva «#800»: l'ordinamento è
   `received_at DESC, id DESC` e la prima riga reale è la **#666** (categoria
   billing). Fix: script corretto («l'id non è prevedibile, annotare quello
   mostrato»); la catena usa l'id dinamico dalla lista, come la UI.
3. **Cleanup kill: pgrep self-match (run 1 e run 2).** Il pattern
   `pgrep -f "bin/uvicorn app.main"` matchava anche il bash esterno (il cui
   argv contiene il comando di avvio): `head -1` prendeva il PID del bash, il
   kill terminava la shell chiamante (exit 143) e uvicorn restava vivo.
   Fix: kill del PID reale letto dal log di uvicorn
   (`Started server process [283406]` run 1, `[283864]` run 2), poi verifica
   porta 8000 libera + nessun processo residuo. Le righe `uvicorn pid=` nei
   log verbatim sotto riportano il PID sbagliato (outer shell): tenute
   verbatim, corrette qui. Stessa classe di intoppo nel warm-up E2E
   (`$!` = wrapper 282225, processo reale 282227): risolto allo stesso modo.
   Lezione per le rehearsal umane: leggere il PID dal log del server, non da
   pgrep, quando il launcher condivide la riga di comando.

Nessun intoppo sui passi della demo: login, baseline, summary recensioni,
ricerca, HITL (edit→send→422 terminale), restore e invariante finali sono
passati identici in entrambi i run.

## Run 1 — verbatim (2026-11-20, UTC)

```text
START 2026-11-20T02:32:33Z
uvicorn pid=283402

== [2026-11-20T02:32:34Z] STEP 0:45 login manager
token: eyJhbGciOiJIUzI1NiIsInR5c... (len 165)

== [2026-11-20T02:32:34Z] STEP 0:45 dashboard baseline (kpis/summary)
{
  "valid_bookings": 61777,
  "room_nights": 218410,
  "revenue": 22976960.13,
  "adr": 105.2,
  "cancellation_rate": 0.2749,
  "occupancy_avg": 0.6558,
  "revpar": 68.99
}

== [2026-11-20T02:32:35Z] STEP 0:45 daily meta (footnote S2)
{
  "page": 1,
  "page_size": 10,
  "total": 793,
  "total_pages": 80
}

== [2026-11-20T02:32:35Z] STEP 2:30 reviews/summary property 1 (Buby Lago)
{
  "property_id": 1,
  "count": 762,
  "overall": 3.86,
  "cleanliness": 4.11,
  "value": 3.43,
  "location": 4.62,
  "rooms": 3.78,
  "sleep_quality": 4.17
}

== [2026-11-20T02:32:35Z] STEP 2:30 reviews/summary property 2 (Buby Montagna)
{
  "property_id": 2,
  "count": 876,
  "overall": 4.4,
  "cleanliness": 4.63,
  "value": 4.27,
  "location": 4.47,
  "rooms": 4.28,
  "sleep_quality": 4.16
}

== [2026-11-20T02:32:35Z] STEP 2:30 reviews list meta
{
  "page": 1,
  "page_size": 5,
  "total": 1638,
  "total_pages": 328
}

== [2026-11-20T02:32:35Z] STEP 4:00 bookings unfiltered meta
{
  "page": 1,
  "page_size": 5,
  "total": 87396,
  "total_pages": 17480
}

== [2026-11-20T02:32:35Z] STEP 4:00 bookings filtered: Lago + Online TA + 2016
{
  "page": 1,
  "page_size": 5,
  "total": 7474,
  "total_pages": 1495
}

== [2026-11-20T02:32:35Z] STEP 5:00 inbox: first row + snapshot draft (jq -j, byte-exact)
first row id=666; snapshot bytes: 334
{
  "id": 666,
  "category": "billing",
  "status": "draft"
}

== [2026-11-20T02:32:35Z] STEP 5:00 HITL edit draft (status stays draft)
{
  "id": 666,
  "status": "draft"
}

== [2026-11-20T02:32:35Z] STEP 5:00 HITL approve/send (draft -> sent)
{
  "id": 666,
  "status": "sent"
}

== [2026-11-20T02:32:35Z] STEP 5:00 sent filter shows the row
{
  "sent_total": 1,
  "ids": [
    666
  ]
}

== [2026-11-20T02:32:35Z] STEP 5:00 sent is terminal: PATCH after sent must be 422
PATCH after sent → HTTP 422

== [2026-11-20T02:32:35Z] STEP 5:00 RESTORE: SQL status back to draft
UPDATE 1

== [2026-11-20T02:32:35Z] STEP 5:00 RESTORE: original draft text via PATCH
{
  "id": 666,
  "status": "draft"
}

== [2026-11-20T02:32:35Z] STEP 5:00 end-state invariant: 800 draft / 0 sent + byte-exact draft
draft|800
draft_reply md5 db=8b53738dd9f8363869091a36196a9b0f file=8b53738dd9f8363869091a36196a9b0f
RESTORE VERIFY: byte-exact OK

== [2026-11-20T02:32:35Z] STEP 9:30 401 without token
no-token → HTTP 401

== [2026-11-20T02:32:35Z] STEP 9:30 properties open
[
  "Buby Lago",
  "Buby Montagna"
]

== [2026-11-20T02:32:35Z] REHEARSAL 1 CHAIN COMPLETE
END 2026-11-20T02:33:01Z CHAIN_RC=0 (cleanup kill hit outer shell first — see stumble log; uvicorn 283406 killed, port verified free)
```

## Run 2 — verbatim (2026-11-20, UTC)

```text
START 2026-11-20T02:33:22Z
uvicorn pid=283860

== [2026-11-20T02:33:23Z] STEP 0:45 login manager
token: eyJhbGciOiJIUzI1NiIsInR5c... (len 165)

== [2026-11-20T02:33:23Z] STEP 0:45 dashboard baseline (kpis/summary)
{
  "valid_bookings": 61777,
  "room_nights": 218410,
  "revenue": 22976960.13,
  "adr": 105.2,
  "cancellation_rate": 0.2749,
  "occupancy_avg": 0.6558,
  "revpar": 68.99
}

== [2026-11-20T02:33:23Z] STEP 0:45 daily meta (footnote S2)
{
  "page": 1,
  "page_size": 10,
  "total": 793,
  "total_pages": 80
}

== [2026-11-20T02:33:23Z] STEP 2:30 reviews/summary property 1 (Buby Lago)
{
  "property_id": 1,
  "count": 762,
  "overall": 3.86,
  "cleanliness": 4.11,
  "value": 3.43,
  "location": 4.62,
  "rooms": 3.78,
  "sleep_quality": 4.17
}

== [2026-11-20T02:33:23Z] STEP 2:30 reviews/summary property 2 (Buby Montagna)
{
  "property_id": 2,
  "count": 876,
  "overall": 4.4,
  "cleanliness": 4.63,
  "value": 4.27,
  "location": 4.47,
  "rooms": 4.28,
  "sleep_quality": 4.16
}

== [2026-11-20T02:33:23Z] STEP 2:30 reviews list meta
{
  "page": 1,
  "page_size": 5,
  "total": 1638,
  "total_pages": 328
}

== [2026-11-20T02:33:23Z] STEP 4:00 bookings unfiltered meta
{
  "page": 1,
  "page_size": 5,
  "total": 87396,
  "total_pages": 17480
}

== [2026-11-20T02:33:23Z] STEP 4:00 bookings filtered: Lago + Online TA + 2016
{
  "page": 1,
  "page_size": 5,
  "total": 7474,
  "total_pages": 1495
}

== [2026-11-20T02:33:23Z] STEP 5:00 inbox: first row + snapshot draft (jq -j, byte-exact)
first row id=666; snapshot bytes: 334
{
  "id": 666,
  "category": "billing",
  "status": "draft"
}

== [2026-11-20T02:33:23Z] STEP 5:00 HITL edit draft (status stays draft)
{
  "id": 666,
  "status": "draft"
}

== [2026-11-20T02:33:23Z] STEP 5:00 HITL approve/send (draft -> sent)
{
  "id": 666,
  "status": "sent"
}

== [2026-11-20T02:33:23Z] STEP 5:00 sent filter shows the row
{
  "sent_total": 1,
  "ids": [
    666
  ]
}

== [2026-11-20T02:33:23Z] STEP 5:00 sent is terminal: PATCH after sent must be 422
PATCH after sent → HTTP 422

== [2026-11-20T02:33:23Z] STEP 5:00 RESTORE: SQL status back to draft
UPDATE 1

== [2026-11-20T02:33:24Z] STEP 5:00 RESTORE: original draft text via PATCH
{
  "id": 666,
  "status": "draft"
}

== [2026-11-20T02:33:24Z] STEP 5:00 end-state invariant: 800 draft / 0 sent + byte-exact draft
draft|800
draft_reply md5 db=8b53738dd9f8363869091a36196a9b0f file=8b53738dd9f8363869091a36196a9b0f
RESTORE VERIFY: byte-exact OK

== [2026-11-20T02:33:24Z] STEP 9:30 401 without token
no-token → HTTP 401

== [2026-11-20T02:33:24Z] STEP 9:30 properties open
[
  "Buby Lago",
  "Buby Montagna"
]

== [2026-11-20T02:33:24Z] REHEARSAL 2 CHAIN COMPLETE
END 2026-11-20T02:33:51Z CHAIN_RC=0 (cleanup: pgrep self-match again — actual uvicorn pid 283864 from server log, killed, port verified free)
```

## Stato finale (dopo run 2, verificato via SQL)

```text
$ docker exec buby-postgres psql -U buby -d buby -tAc \
    "SELECT status, count(*) FROM guest_requests GROUP BY status;"
draft|800
$ curl -s -m 3 localhost:8000/api/properties   # porta 8000
port 8000 free
$ pgrep -af "bin/uvicorn"                      # nessun processo residuo
no uvicorn left
```

Invariante di fine demo rispettata dopo **ogni** run: 800 draft / 0 sent,
bozza della riga toccata ripristinata byte-per-byte (md5
`8b53738dd9f8363869091a36196a9b0f` in entrambi i run). Tutti i processi
avviati (uvicorn ×3, container di build) terminati; `buby-postgres` condiviso
mai toccato oltre le UPDATE/restore documentate.

**Esito:** 2/2 rehearsal complete senza errori sulla catena demo; intoppi di
cleanup documentati e risolti. Timing catena: run 1 02:32:34→02:32:35Z,
run 2 02:33:23→02:33:24Z (~2 s each); il budget ≤10 min dello script è il
pacing umano delle sezioni UI, non il tempo della catena API.

## Entry 3 — fix pass-2 (review P0/P1/P2): bundle verificato via proxy (2026-11-20, UTC)

**Premessa onesta.** Le rehearsal 1–2 hanno verificato la catena API della demo
direttamente contro uvicorn :8000, **non** le URL di fetch del bundle buildato.
Lo smoke compose dell'orchestratore ha verificato nginx→api (solo API). Il
review pass-2 ha colto il P0 che entrambi avevano mancato: con
`VITE_API_BASE_URL=/api` e le path del client già `/api/*`, il browser avrebbe
chiamato **`/api/api/*` → 404**. Questa entry è la verifica corretta del
bundle servito, non solo del proxy.

**Fix applicati:**

- P0: build arg compose e ARG del Dockerfile → `""`. Il `??` del client
  (`client.ts`) tiene `""` (non null/undefined): `fetch("/api/…")` same-origin
  a prefisso unico attraverso nginx. Wording «/api baked-in» corretto in
  README, ADR 0004, demo-script e in questo file.
- P1: percorso host-venv → `up -d postgres` (README §1, demo-script prep,
  `avvia.sh`/`avvia.bat` con `--wait postgres`): la 8000 host non collide con
  il service api del compose.
- P2: comando repro data-tests dalla root (`PYTHONPATH=backend:data
  backend/.venv/bin/python -m pytest -q data/tests`, come ci.yml); wording
  «luglio sotto la propria media» (final-report + demand-pricing: agosto
  0,6684 è sopra la media Montagna, solo luglio 0,5597 è sotto).

**Riverifica (mandatoria, passi a–d):** `compose config -q` OK →
`docker compose build web` (infra-web rebuildata con base vuota) →
`up -d api web` (postgres **non toccato**: Up 15 hours healthy, mai ricreato) →
sidecar nel netns di `buby-postgres` che fetcha SPA e JS **serviti** via
`http://web:80`, grep del bundle, login con la URL esatta a prefisso unico
della SPA → `stop` + `rm -f` di api/web, porte libere.

### Bundle + proxy — verbatim (sidecar `--network container:buby-postgres`)```text

== [2026-11-20T03:05:24Z] STEP b1: fetch SPA index via http://web:80/
GET / -> 200, 407 bytes
assets: ['/assets/index-DnafXET0.js', '/assets/index-8YI98SS-.css']

== [2026-11-20T03:05:24Z] STEP b2: fetch JS asset /assets/index-DnafXET0.js
GET /assets/index-DnafXET0.js -> 200, 603466 bytes

== [2026-11-20T03:05:25Z] STEP b3: bundle grep (P0 checks)
  PASS: 'localhost:8000' ABSENT
  PASS: '/api/api' ABSENT (no double prefix)
  PASS: old base constant '"/api"' ABSENT
  PASS: client paths '/api/auth/login' present
  PASS: client paths '/api/kpis/summary' present

== [2026-11-20T03:05:25Z] STEP b4: base resolves to '' (relative fetch) — minified fetch sites:
  ...origin",u}function n(a){if(a.ep)return;a.ep=!0;const u=r(a);fetch(a.href,u)}})();var hs=typeof globalThis<"u"?globalThis:typeof window<"u"?window:type...
  ...d";function Dg(e){su=e}async function pn(e,t){const r=await fetch(`${wM}${e}`,{...t,headers:{...t!=null&&t.body?{"Content-Type":"application/json"}:{}...
PASS: no absolute base at fetch sites (empty-string base folded)

== [2026-11-20T03:05:25Z] STEP c1: POST http://web:80/api/auth/login (SPA single-prefix URL)
POST /api/auth/login -> 200
token: eyJhbGciOiJIUzI1NiIsInR5c... (len 165), role=manager

== [2026-11-20T03:05:25Z] STEP c2: GET http://web:80/api/kpis/summary with Bearer token
GET /api/kpis/summary -> 200
{
  "valid_bookings": 61777,
  "room_nights": 218410,
  "revenue": 22976960.13,
  "adr": 105.2,
  "cancellation_rate": 0.2749,
  "occupancy_avg": 0.6558,
  "revpar": 68.99
}
PASS: baseline 61777 / 22976960.13 / 0.6558 via web proxy

== [2026-11-20T03:05:25Z] BUNDLE + PROXY VERIFICATION COMPLETE (all checks passed)
Traceback (most recent call last):
  File "<stdin>", line 8, in <module>
AssertionError: base not empty: not found

== [2026-11-20T03:05:43Z] STEP b5: base constant definition

== [2026-11-20T03:05:55Z] STEP b5 (retry): all wM occurrences
occurrences: 2
  ...teRoot=e.createRoot,vs.hydrateRoot=e.hydrateRoot,vs}var xM=bM();const wM="";class on extends Error{constructor(t,r,n,a){...
  ...ed";function Dg(e){su=e}async function pn(e,t){const r=await fetch(`${wM}${e}`,{...t,headers:{...t!=null&&t.body?{"Conte...

== [2026-11-20T03:06:08Z] STEP b5 (final): base constant assertion
PASS: bundle contains 'const wM="";' and fetch(`${wM}${e}`)
PASS: BASE_URL="" -> fetch("/api/...") same-origin, single prefix through nginx
```
Intoppo di questa entry (solo del check, non del bundle): la prima regex per
la costante di base (`[,;]wM=`) mancava `const wM="";` (spazio prima del nome,
non virgola/punto-e-virgola) → AssertionError «not found». Fix: elenco di
tutte le occorrenze di `wM` + assert sulla stringa esatta `const wM="";`.
Il bundle era corretto già dal primo fetch.

### Ciclo compose — verbatim```text
$ docker compose -f infra/docker-compose.yml config -q
CONFIG -Q: OK
$ docker compose -f infra/docker-compose.yml config | grep -A1 args
      args:
        VITE_API_BASE_URL: ""
$ docker compose -f infra/docker-compose.yml build web
Successfully built a2f0e0b503d8
Successfully tagged infra-web:latest
 Image infra-web Built
$ docker compose -f infra/docker-compose.yml up -d api web
 Container buby-web Creating
 Container buby-web Created
 Container buby-postgres Waiting
 Container buby-postgres Healthy
 Container buby-api Starting
 Container buby-api Started
 Container buby-web Starting
 Container buby-web Started
$ docker compose -f infra/docker-compose.yml ps
buby-api Up 3 seconds
buby-postgres Up 15 hours (healthy)
buby-web Up 3 seconds
$ docker compose -f infra/docker-compose.yml stop api web
 Container buby-web Stopping
 Container buby-web Stopped
 Container buby-api Stopping
 Container buby-api Stopped
$ docker compose -f infra/docker-compose.yml rm -f api web
Going to remove buby-web, buby-api
 Container buby-api Removing
 Container buby-web Removing
 Container buby-api Removed
 Container buby-web Removed
$ docker compose -f infra/docker-compose.yml ps
buby-postgres Up 15 hours (healthy)
port 8000 free
port 8080 free
draft|800
```
### Re-run suite (passo f) — verbatim```text
$ cd frontend && npm test -- --run
 Test Files  2 passed (2)
      Tests  19 passed (19)
   Start at  04:06:21
   Duration  402ms (transform 142ms, setup 0ms, collect 110ms, tests 85ms, environment 0ms, prepare 176ms)
$ npm run typecheck
(tsc --noEmit: nessun errore)
$ npm run build
(default host, nessun override VITE_API_BASE_URL; warning chunk >500 kB pre-esistente)
✓ built in 2.30s
$ grep -c "localhost:8000" frontend/dist/assets/*.js
1
(fallback host invariato: il build di default punta ancora a http://localhost:8000)
$ cd backend && .venv/bin/python -m pytest -q
140 passed, 1 skipped in 2.59s

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
port 8000 free (uvicorn 295925 killed)
draft|800
E2E_RC=0
```
**Esito entry 3:** bundle servito con base `""` — `localhost:8000` assente,
`/api/api` assente, vecchia costante `"/api"` assente, `const wM="";` +
`fetch(`${wM}${e}`)` = fetch relativa a prefisso unico. Login manager via
`http://web:80/api/auth/login` → 200 + token; summary via proxy → baseline
61777 / 22976960.13 / 0.6558. Frontend host invariato (19 test + tsc + build,
fallback `localhost:8000` presente nel build di default). Backend 140 passed /
1 skipped; e2e_smoke all-pass con invariante 800 draft / 0 sent. api/web
fermati e rimossi, postgres condiviso intatto, porte 8000/8080 libere, nessun
processo residuo. Il gap di verifica che ha lasciato passare il P0 (bundle
mai fetchato/greppato) è chiuso: d'ora in poi la verifica release include il
bundle servito, non solo il proxy API.## Entry 4 — restructure GitGuardian (decisione operator): POSTGRES_* passthrough, config.py assembla la URL (2026-11-20, UTC)

**Razionale.** Incident GitGuardian 39943867 («Generic Password») sulla riga
`DATABASE_URL` inline del service api (`:${POSTGRES_PASSWORD:-buby}@` nel
URL, commit f9e71c1, poi squashato in ae7d07c). Primo tentativo (463cbb9):
ignore scoped in `.gitguardian.yaml` — **non ha risolto**: l'integrazione
dashboard riporta l'incidente registrato («Triggered») sui commit della PR
(check ri-run 1 s, stesso incident, nessuna nuova scansione config-aware);
la risoluzione dashboard non è stata intrapresa. **L'operator ha scelto il
restructure.**

**Scoperta chiave:** `backend/app/config.py` (righe 3–15) assembla già
`DATABASE_URL` da `POSTGRES_USER/PASSWORD/DB/HOST/PORT` quando `DATABASE_URL`
non è impostata → **nessun cambio backend**. Il service api ora passa le
stesse righe di interpolazione del service postgres (pattern che scansiona
pulito da settimane) + `POSTGRES_HOST: postgres`; il default porta 5432 di
config.py copre la rete compose. `exec alembic` è sicuro perché le env sono
a livello container, non entrypoint — provato sotto (`alembic current` →
0005 head).

**Supersessione:** `.gitguardian.yaml` RIMOSSO (il pattern segnalato non
esiste più; il restructure approvato dall'operator sostituisce l'ignore).
La riga sicurezza di ADR 0004 mantiene «un deploy reale DEVE impostare
`POSTGRES_PASSWORD` e `JWT_SECRET` via env», senza più il riferimento
all'ignore-file.

### a. Config renderizzata — verbatim

```text
$ docker compose -f infra/docker-compose.yml config -q
CONFIG -Q: OK
$ docker compose -f infra/docker-compose.yml config   # env del service api
    environment:
      POSTGRES_DB: buby
      POSTGRES_HOST: postgres
      POSTGRES_PASSWORD: buby
      POSTGRES_USER: buby
$ docker compose -f infra/docker-compose.yml config | grep -c DATABASE_URL
0
$ docker exec buby-api env | grep -E '^POSTGRES_|^DATABASE_URL'
POSTGRES_DB=buby
POSTGRES_HOST=postgres
POSTGRES_PASSWORD=buby
POSTGRES_USER=buby
```

### b. Ciclo compose — verbatim

```text
$ docker compose -f infra/docker-compose.yml up -d --build api web
 Container buby-api Creating
 Container buby-api Created
 Container buby-web Creating
 Container buby-web Created
 Container buby-postgres Waiting
 Container buby-postgres Healthy
 Container buby-api Starting
 Container buby-api Started
 Container buby-web Starting
 Container buby-web Started
$ docker compose -f infra/docker-compose.yml ps
buby-api Up 3 seconds
buby-postgres Up 20 hours (healthy)
buby-web Up 3 seconds
$ docker compose -f infra/docker-compose.yml stop api web && ... rm -f api web
 Container buby-web Stopping
 Container buby-web Stopped
 Container buby-api Stopping
 Container buby-api Stopped
 Container buby-api Removing
 Container buby-web Removing
 Container buby-api Removed
 Container buby-web Removed
$ docker compose -f infra/docker-compose.yml ps
buby-postgres Up 20 hours (healthy)
port 8000 free
port 8080 free
draft|800
```

Postgres riutilizzato, dati seedati intatti (800 draft prima e dopo).

### c. Bundle servito + proxy — verbatim (sidecar netns buby-postgres)
```text

== [2026-11-20T08:20:28Z] STEP b1: fetch SPA index via http://web:80/
GET / -> 200, 407 bytes
assets: ['/assets/index-DnafXET0.js', '/assets/index-8YI98SS-.css']

== [2026-11-20T08:20:28Z] STEP b2: fetch JS asset /assets/index-DnafXET0.js
GET /assets/index-DnafXET0.js -> 200, 603466 bytes

== [2026-11-20T08:20:28Z] STEP b3: bundle grep (P0 checks)
  PASS: 'localhost:8000' ABSENT
  PASS: '/api/api' ABSENT (no double prefix)
  PASS: old base constant '"/api"' ABSENT
  PASS: client paths '/api/auth/login' present
  PASS: client paths '/api/kpis/summary' present

== [2026-11-20T08:20:28Z] STEP b4: base resolves to '' (relative fetch) — minified fetch sites:
  ...origin",u}function n(a){if(a.ep)return;a.ep=!0;const u=r(a);fetch(a.href,u)}})();var hs=typeof globalThis<"u"?globalThis:typeof window<"u"?window:type...
  ...d";function Dg(e){su=e}async function pn(e,t){const r=await fetch(`${wM}${e}`,{...t,headers:{...t!=null&&t.body?{"Content-Type":"application/json"}:{}...
PASS: no absolute base at fetch sites (empty-string base folded)

== [2026-11-20T08:20:28Z] STEP b5: empty-base constant present (dynamic)
PASS: const wM=""; -> fetch(`${wM}${path}`) = relative "/api/..." single prefix

== [2026-11-20T08:20:28Z] STEP c1: POST http://web:80/api/auth/login (SPA single-prefix URL)
POST /api/auth/login -> 200
token: eyJhbGciOiJIUzI1NiIsInR5c... (len 165), role=manager

== [2026-11-20T08:20:28Z] STEP c2: GET http://web:80/api/kpis/summary with Bearer token
GET /api/kpis/summary -> 200
{
  "valid_bookings": 61777,
  "room_nights": 218410,
  "revenue": 22976960.13,
  "adr": 105.2,
  "cancellation_rate": 0.2749,
  "occupancy_avg": 0.6558,
  "revpar": 68.99
}
PASS: baseline 61777 / 22976960.13 / 0.6558 via web proxy

== [2026-11-20T08:20:29Z] BUNDLE + PROXY VERIFICATION COMPLETE (all checks passed)
```
### d. exec-alembic proof — verbatim

```text
$ docker compose -f infra/docker-compose.yml exec api alembic current
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
0005 (head)
$ docker compose -f infra/docker-compose.yml exec api alembic heads
0005 (head)
```

La fallback di config.py funziona anche per `exec` (env a livello container):
è il motivo per cui questo restructure è sicuro senza entrypoint dedicati.

### f. Re-run suite — verbatim

```text
$ cd backend && .venv/bin/python -m pytest -q
140 passed, 1 skipped in 2.60s
$ cd frontend && npm test -- --run
 Test Files  2 passed (2)
      Tests  19 passed (19)
$ npm run typecheck
(tsc --noEmit: nessun errore)
$ npm run build
✓ built in 2.48s
$ # uvicorn sidecar :8000 + e2e_smoke (PID dal log del server, kill verificato)→ login (manager demo)
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
port 8000 free (uvicorn 378905 killed)
draft|800
E2E_RC=0
```

**Esito entry 4:** restructure completo e riverificato — api env solo
`POSTGRES_*` (zero `DATABASE_URL` renderizzate), bundle servito invariato
(base vuota, nessun doppio prefisso), login+baseline via proxy OK,
`exec alembic current` → 0005 (head), suite backend/frontend/e2e identiche
ai run precedenti (config.py invariato). Invariante 800 draft / 0 sent;
api/web fermati e rimossi; postgres condiviso intatto; porte libere; nessun
processo residuo. `.gitguardian.yaml` rimosso perché superseded dal
restructure (decisione operator registrata qui e in ADR 0004).
## Entry 5 — restructure finale (ultimo tentativo agent-side, operator informato): api env = solo POSTGRES_HOST (2026-11-20, UTC)

**Lezione sul detector (comportamento osservato, non ipotizzato).** GitGuardian
«Generic Password» (incident 39943867) segnala il match `buby` in **contenuto
nuovo** della PR in entrambe le forme provate:

1. URL con password inline (`:${POSTGRES_PASSWORD:-buby}@` nella
   `DATABASE_URL` del service api) — occurrence 314545002 @ ae7d07c R31;
2. interpolazione standalone (`POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-buby}`
   aggiunta al service api) — occurrence 314550096 @ c291cd4 R34.

Le righe identiche del service **postgres** passano solo perché **precedono
il diff della PR** (contenuto pre-esistente su master, non aggiunto dalla PR).
Quindi qualsiasi passthrough di credenziali con default `:-buby` aggiunto in
questa PR viene segnalato, anche se il pattern è «già presente» altrove nel
file. L'ignore-file `.gitguardian.yaml` non risolve l'integrazione dashboard
(entry 4); la risoluzione dashboard non è stata intrapresa.

**Fix finale (decisione operator):** il service api passa **solo**
`POSTGRES_HOST: postgres`. I default di `backend/app/config.py`
(buby/buby/buby, pubblicati in `docs/api-contract.md`, postura demo S7)
assemblano già `postgresql+psycopg://buby:buby@postgres:5432/buby` quando
nessuna `POSTGRES_*` è impostata: il percorso demo di default ha bisogno
solo dell'host. Le righe `POSTGRES_USER/PASSWORD/DB` sono rimosse dal
service api (tripwire del detector in contenuto nuovo). Credenziali custom
via `infra/.env`: il README «Run with Docker» ora documenta che vanno passate
esplicitamente anche al service api (override environment o
`docker compose run -e … api …`).

**Squash rewrite (precedente WP7, pattern approvato dall'orchestratore):**
`git reset --soft master` + un solo commit feat(release) — la storia della PR
non porta più il pattern segnalato (né l'URL inline né il passthrough).
Hard check: `git diff c291cd4 HEAD` = sole modifiche intended di questa entry
(env compose, 2 righe README, questa entry). Se GitGuardian segnala ancora,
la decisione passa a dashboard/admin: **nessun ulteriore tentativo agent**.

### Verifica rapida — verbatim

```text
$ docker compose -f infra/docker-compose.yml config -q
CONFIG -Q: OK
$ docker compose -f infra/docker-compose.yml config   # env del service api
    environment:
      POSTGRES_HOST: postgres
$ docker exec buby-api env | grep -E '^POSTGRES_|^DATABASE_URL'
POSTGRES_HOST=postgres
$ docker compose -f infra/docker-compose.yml up -d api web   # immagini cached
 Container buby-postgres Waiting
 Container buby-postgres Healthy
 Container buby-api Starting
 Container buby-api Started
 Container buby-web Starting
 Container buby-web Started
buby-api Up 3 seconds
buby-postgres Up 20 hours (healthy)
buby-web Up 3 seconds
$ docker compose -f infra/docker-compose.yml exec api alembic current
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
0005 (head)
$ docker compose -f infra/docker-compose.yml stop api web && ... rm -f api web
 Container buby-api Stopping
 Container buby-api Stopped
 Container buby-api Removed
 Container buby-web Removed
buby-postgres Up 20 hours (healthy)
port 8000 free
port 8080 free
draft|800
```

### Bundle servito + proxy — verbatim (sidecar netns buby-postgres)
```text

== [2026-11-20T08:30:49Z] STEP b1: fetch SPA index via http://web:80/
GET / -> 200, 407 bytes
assets: ['/assets/index-DnafXET0.js', '/assets/index-8YI98SS-.css']

== [2026-11-20T08:30:49Z] STEP b2: fetch JS asset /assets/index-DnafXET0.js
GET /assets/index-DnafXET0.js -> 200, 603466 bytes

== [2026-11-20T08:30:49Z] STEP b3: bundle grep (P0 checks)
  PASS: 'localhost:8000' ABSENT
  PASS: '/api/api' ABSENT (no double prefix)
  PASS: old base constant '"/api"' ABSENT
  PASS: client paths '/api/auth/login' present
  PASS: client paths '/api/kpis/summary' present

== [2026-11-20T08:30:49Z] STEP b4: base resolves to '' (relative fetch) — minified fetch sites:
  ...origin",u}function n(a){if(a.ep)return;a.ep=!0;const u=r(a);fetch(a.href,u)}})();var hs=typeof globalThis<"u"?globalThis:typeof window<"u"?window:type...
  ...d";function Dg(e){su=e}async function pn(e,t){const r=await fetch(`${wM}${e}`,{...t,headers:{...t!=null&&t.body?{"Content-Type":"application/json"}:{}...
PASS: no absolute base at fetch sites (empty-string base folded)

== [2026-11-20T08:30:49Z] STEP b5: empty-base constant present (dynamic)
PASS: const wM=""; -> fetch(`${wM}${path}`) = relative "/api/..." single prefix

== [2026-11-20T08:30:49Z] STEP c1: POST http://web:80/api/auth/login (SPA single-prefix URL)
POST /api/auth/login -> 200
token: eyJhbGciOiJIUzI1NiIsInR5c... (len 165), role=manager

== [2026-11-20T08:30:49Z] STEP c2: GET http://web:80/api/kpis/summary with Bearer token
GET /api/kpis/summary -> 200
{
  "valid_bookings": 61777,
  "room_nights": 218410,
  "revenue": 22976960.13,
  "adr": 105.2,
  "cancellation_rate": 0.2749,
  "occupancy_avg": 0.6558,
  "revpar": 68.99
}
PASS: baseline 61777 / 22976960.13 / 0.6558 via web proxy

== [2026-11-20T08:30:50Z] BUNDLE + PROXY VERIFICATION COMPLETE (all checks passed)
```
**Esito entry 5:** con api env = solo `POSTGRES_HOST`, i default di config.py
bastano: login via proxy 200, baseline 61777 / 22976960.13 / 0.6558, bundle
invariato (base vuota, nessun doppio prefisso), `exec alembic current` →
0005 (head). Invariante 800 draft / 0 sent; api/web fermati e rimossi;
postgres condiviso intatto; porte libere; nessun processo residuo. Suite
backend/frontend/e2e invariate rispetto all'entry 4 (config.py e codice
sorgente non toccati da questo restructure: solo env compose + docs).
