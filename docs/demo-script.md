# Script demo — Buby Travel (demo finale 18 dic, ≤10 minuti)

**WP14 / D18.** Demo **locale**, sempre: il deploy pubblico è gated su HA-10
(account umani, `docs/reviews/human-actions.md`) e i free tier dormono
(delivery-plan §2). Rehearsal registrate:
`docs/reviews/2026-11-20-demo-rehearsals.md` (×2, catena API identica a questa).

Ogni numero citato viene da `docs/data-dictionary.md` (§1, §3),
`data/eval/demand_analysis.json`, `data/eval/email_metrics.json`,
`data/eval/review_nlp_metrics.json` o dal contratto `openapi.yaml` (esempi
pinned). Nessun numero inventato. Disclosure complete: slide 12 di
`docs/sal1/slides-outline.md` (slide dedicata, non nota a piè di pagina).

## Preparazione (prima del pubblico, non conteggiata nei 10 min)

DB seedato e API accesa. Due percorsi equivalenti (README «Run with Docker» e
«Run it locally»):

- **Compose full-stack:** `docker compose -f infra/docker-compose.yml up -d --build`
  → `... exec api alembic upgrade head` → seed (README) → web su
  **http://localhost:8080** (bundle a base vuota, fetch `/api/*` same-origin
  a prefisso unico; nginx proxya `/api` → api:8000).
- **Host venv:** `docker compose -f infra/docker-compose.yml up -d postgres`
  (solo postgres: la 8000 la usa uvicorn host) + `uvicorn app.main:app --port 8000`
  (backend/.venv) + `npm run dev` → **http://localhost:5173**.

Seed: dataset completo per i numeri citati sotto (baseline 61.777 valide;
playbook `docs/playbooks/solo-dataset.md`). Con il **campione committato**
(5.000 righe, fresh clone) la demo gira uguale ma i KPI sono quelli campione:
3.564 valide / 12.696 room-night / 1.350.503,84 € / cancel 0,2696
(dizionario §3) — dirlo ad alta voce se si usa il campione.

Stato inbox atteso prima di iniziare: **800 draft / 0 sent** (post-D15).
Verifica: `docker exec buby-postgres psql -U buby -d buby -tAc
"SELECT status, count(*) FROM guest_requests GROUP BY status;"`.

Credenziali demo (default di sviluppo pubblicati, `docs/api-contract.md`):
`manager@buby.travel` / `demo` (anche `admin@buby.travel`,
`property.manager@buby.travel`).

---

## 0:00–0:45 — Apertura e login

1. Aprire il web, login come **manager** (`manager@buby.travel` / `demo`).
   «L'autenticazione è JWT reale con 3 ruoli: admin, manager, property manager.
   Il property manager legge ma non può inviare email (403).»
2. **Dichiarazione di apertura (vincolante, dizionario §1 Assunzione 1):**
   «Buby Lago e Buby Montagna sono strutture **fittizie**: mappatura 1:1 dei due
   tipi di hotel del dataset Kaggle Hotel Booking Demand (Resort → Lago,
   City → Montagna), portoghese 2015–2017. Nessun dato Buby reale è mai
   arrivato: la richiesta scritta B4 è agli atti come azione umana HA-09.»

## 0:45–2:30 — Dashboard KPI (baseline parlata)

Selettore «Both», finestra default 2015-07-01 → 2017-08-31. Leggere le card:

| Card | Valore (DB completo) |
|---|---:|
| Revenue | **22.976.960,13 €** |
| Room nights | **218.410** |
| ADR | **105,20 €** |
| Cancellation rate | **27,49%** |
| Occupancy (avg) | **65,58%** (capacità assunta) |
| RevPAR | **68,99 €** (capacità assunta) |

«Sono **61.777 prenotazioni valide** su 87.396 righe post-deduplica: il baseline
pulito del dizionario §3, riprodotto al centesimo dal seed e asserito dalla CI.
Ogni KPI ha la sua regola scritta: cancellazione solo post-dedup (27,49%, non
37,04% lordo), ADR = ricavo/room-night, stagionalità a medie per mese dell'anno
perché 2015 e 2017 sono parziali.»

**Footnote S2 (spiegarla, il cliente la vede):** «Il riepilogo conta gli
**arrivi** nel periodo (coorte: un soggiorno che arriva nella finestra
contribuisce con tutte le sue notti); il grafico giornaliero conta i **giorni di
soggiorno**. Ai bordi i totali differiscono per progetto: con la finestra
default, 19 giorni di soggiorno oltre il 2017-08-31 (723 room-night,
105.263,50 €) entrano nel riepilogo ma non nella serie giornaliera.»

**Footnote capacità (Assunzione 3):** «Occupazione e RevPAR usano capacità
**assunta**: 190 camere Lago, 230 Montagna, inferite dal picco osservato
(187/226) + margine. Circolarità dichiarata: per costruzione l'occupazione non
può superare il 100%. Non sono misure.»

## 2:30–4:00 — Tab Reputazione (disclosure 2012 parlata)

1. «Entrambe»: **1.638 recensioni TripAdvisor reali**, voto medio per dimensione
   (pulizia, rapporto Q/P, posizione, camere, qualità del sonno).
2. Per proprietà: **Buby Lago 762 recensioni, overall 3,86**; **Buby Montagna
   876, overall 4,40** (mapping dichiarato e immutabile, dizionario §2).
3. **Disclosure S4 (dirla prima che il cliente chieda):** «Le recensioni sono
   **tutte del 2012** (2012-01-02…2012-12-19); le prenotazioni coprono
   2015–2017: **zero mesi in comune**. Il trend che vedete è una serie
   solo-2012: nessuna analisi congiunta con occupazione/ricavi, il legame
   recensioni↔prenotazioni è **asserito a livello di proprietà**, non fattuale.
   Il corpus è solo inglese, N=1.638: statistiche descrittive, non inferenza.»
4. «Sentiment e topic NLP sono calcolati sui body reali (D14): i numeri che
   mostriamo tra poco vengono dalle valutazioni committate, non da questa
   pagina — il contratto v1 espone solo i voti reali degli ospiti (S8).»

## 4:00–5:00 — Tab Ricerca

1. Senza filtri: **87.396 prenotazioni** (righe post-dedup, dizionario §1).
2. Filtri live: proprietà **Buby Lago**, canale **Online TA**, anno 2016 →
   leggere il totale mostrato. «La ricerca è sui dati reali, paginata lato
   server; i canali sono gli 8 `market_segment` del CSV: `agent`/`company` sono
   ID numerici non mappati, quindi nessuna disaggregazione per OTA con nome.»

## 5:00–7:00 — Tab Inbox: human-in-the-loop ( UNA riga )

1. **Disclosure sintetiche (il banner è in pagina):** «Le 800 email sono
   **sintetiche** (generatore DA-3, seed 42, 6 categorie, nomi/indirizzi
   inventati per GDPR). Nessuna corrispondenza reale. Nessuno invio
   automatico: approva una persona.»
2. Aprire la **prima email in lista** (ordinamento per `received_at` discendente:
   l'id non è prevedibile, nelle rehearsal era la **#666**; annotare l'id
   mostrato, qui `<ID>`). Categoria e urgenza sono
   predette dal classificatore D15; la bozza è già pronta.
3. **Modificare la bozza** (es. aggiungere una frase) → «Salva bozza»: lo stato
   resta `draft`.
4. **Approvare e inviare** → «Invia»: lo stato passa a `sent`. Mostrare il
   filtro stato «Inviata»: la riga è lì.
5. **Sent è terminale:** provare a modificare la bozza dopo l'invio → l'API
   risponde **422** («Guest request already sent»). «Dopo l'invio non si
   riscrive nulla: è il guard HITL.»
6. **RIPRISTINARE subito dopo la demo** (l'invariante di fine demo è 800 draft /
   0 sent). `sent` non è revertibile via API: si usa SQL documentata:

   ```bash
   # 1. stato back a draft (compose postgres; su host venv: psql della propria istanza)
   docker exec buby-postgres psql -U buby -d buby \
     -c "UPDATE guest_requests SET status='draft' WHERE id=<ID>;"
   # 2. verifica invariante
   docker exec buby-postgres psql -U buby -d buby \
     -tAc "SELECT status, count(*) FROM guest_requests GROUP BY status;"
   # atteso: draft|800  (nessuna riga sent)
   ```

   Il testo originale della bozza (copiato prima del punto 3) si ripristina
   dalla UI («Salva bozza») o via API PATCH `draft_reply` — ora che la riga è
   di nuovo `draft` è modificabile. Le rehearsal usano questa stessa catena.

## 7:00–8:30 — NLP/valutazioni + memo domanda (numeri dai JSON committati)

**Email (D15, `email_metrics.json`):** «Macro-F1 categoria **0,9901**, urgenza
**0,9659**, gold allineato 800/800. Errori: 8 email su 800 confuse come `info`
(4 availability + 4 special_request); urgenza: 22 low→medium e 5 medium→low.
**Onestà obbligatoria:** il corpus è sintetico e le regex del classificatore
derivano dagli stessi template: questo F1 **non è evidenza su email reali**.
L'upgrade LLM è gated su HA-05 (chiavi e chi paga, decisione umana scaduta).»

**Recensioni (D14, `review_nlp_metrics.json`):** «Sentiment preaddestrato
multilingue, zero training: correlazione di Spearman col voto overall reale
**0,5517** (pooled, n=1.638); per proprietà **0,6266 Lago / 0,4370 Montagna**.
Etichette deboli: correlazione ≠ accuratezza. Topics zero-shot NLI: il segnale
più netto è **noise → sleep_quality −0,696** (3,596 vs 4,292): chi parla di
rumore dorme peggio, in entrambe le strutture. Soglie calibrate su probe di 20
recensioni: F1 0,857–0,933, **ottimistico** (stesso corpus, annotatore unico).
Troncamenti: 6,84% dei body a 512 token (sentiment), 25,64% a 256 (topics).»

**Domanda/prezzi (WP12, `demand_analysis.json`):** «Agosto contro gennaio:
ricavo medio giornaliero per proprietà **25.029,60 € vs 6.149,95 €** (~4×).
Lago è estivo (occupazione agosto **0,9172**, ADR 175,86 €), Montagna più piatta.
Online TA: **59,06%** delle prenotazioni ma cancella al **35,35%**; Direct:
ADR più alto (126,96 €) e cancellazione 14,72%. Il rischio di cancellazione
cresce col lead-time: **8,43%** sotto una settimana → **39,74%** oltre 180 giorni.
Tutte associazioni, nessuna causalità: nessun esperimento di prezzo nel dataset.»

## 8:30–9:30 — Domanda al cliente: la previsione (HA-14)

«Il caso dice "prevedere la domanda"; il piano mette il forecast tra gli
stretch perché il brief lo definisce "eventuale". Non lo tagliamo in silenzio:
**decidete voi al SAL 1** (ledger HA-14, memo `docs/analysis/demand-pricing.md` §10):

- **Opzione A — D16 stretch:** baseline moving-average sui KPI giornalieri per
  proprietà, backtest 2017 con errore dichiarato (MAE/MAPE). Stima ≈1 giornata
  DA-3 (+1–2 se esposta via API, che richiede contract-bump). Limite: ~2 anni
  di storia, 2017 parziale.
- **Opzione B — waiver scritto:** questa analisi descrittiva + decisioni sui
  prezzi come risposta al caso; nessun modello predittivo. Il waiver copre il
  team contrattualmente, ma "prevedere" resta nominato nell'obiettivo.

La decisione va archiviata in HA-14: la chiude un umano, non un agent.»

## 9:30–10:00 — Chiusura

- «Tutte le disclosure sono nella slide dedicata (slide 12,
  `docs/sal1/slides-outline.md`): strutture fittizie, legame asserito, capacità
  assunta, email sintetiche, S4 zero overlap, solo inglese N=1.638, nessun dato
  cliente (B4/HA-09).»
- «La demo è locale di proposito: il deploy pubblico (Render/Vercel/Neon,
  ADR 0004) aspetta gli account umani HA-10; l'istanza pubblica si scalda
  10 minuti prima di ogni check esterno.»
- Report finale numeri + caveat: `docs/analysis/final-report.md`.

---

## Appendice A — catena di verifica API (usata nelle rehearsal)

Da repo root, con uvicorn acceso su :8000 (host venv) o con la catena puntata
all'api del compose. `jq` richiesto. È la stessa catena delle rehearsal
registrate in `docs/reviews/2026-11-20-demo-rehearsals.md`.

```bash
BASE=http://localhost:8000
AUTH='Content-Type: application/json'

# 0:45 login manager
TOKEN=$(curl -s -X POST "$BASE/api/auth/login" -H "$AUTH" \
  -d '{"email":"manager@buby.travel","password":"demo"}' | jq -r .access_token)
H="Authorization: Bearer $TOKEN"

# 0:45 dashboard: baseline + meta giornaliero (footnote S2)
curl -s "$BASE/api/kpis/summary" -H "$H" | jq '{valid_bookings,room_nights,revenue,adr,cancellation_rate,occupancy_avg,revpar}'
curl -s "$BASE/api/kpis/daily?page_size=10" -H "$H" | jq .meta

# 2:30 reputazione: summary per proprietà + lista
curl -s "$BASE/api/reviews/summary?property_id=1" -H "$H" | jq '{property_id,count,overall,cleanliness,value,location,rooms,sleep_quality}'
curl -s "$BASE/api/reviews/summary?property_id=2" -H "$H" | jq '{property_id,count,overall,cleanliness,value,location,rooms,sleep_quality}'
curl -s "$BASE/api/reviews?page_size=5" -H "$H" | jq .meta

# 4:00 ricerca: totale + filtri live
curl -s "$BASE/api/bookings?page_size=5" -H "$H" | jq .meta
curl -s "$BASE/api/bookings?property_id=1&market_segment=Online%20TA&date_from=2016-01-01&date_to=2016-12-31&page_size=5" -H "$H" | jq .meta

# 5:00 inbox HITL: prima riga, snapshot bozza, edit, invio, terminale
ID=$(curl -s "$BASE/api/guest-requests?page_size=5" -H "$H" | jq '.data[0].id')
curl -s "$BASE/api/guest-requests?page_size=5" -H "$H" | jq -j '.data[0].draft_reply' > /tmp/demo-draft-original.txt
curl -s "$BASE/api/guest-requests?page_size=5" -H "$H" | jq '.data[0] | {id,category,status}'
curl -s -X PATCH "$BASE/api/guest-requests/$ID" -H "$H" -H "$AUTH" \
  -d '{"draft_reply":"Gentile ospite, confermiamo la disponibilità per le date richieste. Un nostro operatore la contatterà entro 24 ore. — Buby Travel"}' | jq '{id,status}'
curl -s -X PATCH "$BASE/api/guest-requests/$ID" -H "$H" -H "$AUTH" \
  -d '{"status":"sent"}' | jq '{id,status}'
curl -s "$BASE/api/guest-requests?status=sent&page_size=5" -H "$H" | jq '{sent_total:.meta.total, ids:[.data[].id]}'
# sent è terminale: una modifica dopo l'invio deve dare 422
curl -s -o /dev/null -w 'PATCH after sent → HTTP %{http_code}\n' \
  -X PATCH "$BASE/api/guest-requests/$ID" -H "$H" -H "$AUTH" -d '{"draft_reply":"prova"}'

# RIPRISTINO (subito): SQL per lo stato + PATCH per il testo originale
docker exec buby-postgres psql -U buby -d buby \
  -c "UPDATE guest_requests SET status='draft' WHERE id=$ID;"
ORIG=$(jq -Rs . < /tmp/demo-draft-original.txt)
curl -s -X PATCH "$BASE/api/guest-requests/$ID" -H "$H" -H "$AUTH" \
  -d "{\"draft_reply\":$ORIG}" | jq '{id,status}'
docker exec buby-postgres psql -U buby -d buby \
  -tAc "SELECT status, count(*) FROM guest_requests GROUP BY status;"

# chiusura: 401 senza token + properties aperto
curl -s -o /dev/null -w 'no-token → HTTP %{http_code}\n' "$BASE/api/kpis/summary"
curl -s "$BASE/api/properties" | jq '[.data[].name]'
```

Nota: `urgency` (predetta da D15) non è nel contratto v1: l'API non la espone
né la scrive. La bozza originale si ripristina con PATCH solo dopo il ritorno
a `draft` via SQL: `sent` è terminale.