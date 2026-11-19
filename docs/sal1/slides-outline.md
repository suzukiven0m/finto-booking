# SAL 1 — outline delle slide (ven 2026-11-20, cliente presente)

Outline slide-per-slide per la presentazione SAL 1: freeze di schema + contratto.
Quattro aree valutate: **ANALISI · PROCESSO · SCHEMA · CONTRATTO**, più una slide
**dedicata** alle disclosure (non una nota a piè di pagina), una slide sul freeze
e una sui prossimi passi. Ogni numero citato è tracciabile a dizionario dati
(`docs/data-dictionary.md`), audit (`docs/reviews/2026-11-19-shepherd-audit.md`),
contratto (`openapi.yaml`) o record WP: la fonte è indicata per slide, nessun
numero inventato. Presentazione: lead + team (ledger HA-11, dry run incluso).

---

## Slide 1 — Apertura: Buby Travel, SAL 1

- Titolo: «Buby Travel — SAL 1: freeze di schema e contratto dati» (ven 2026-11-20).
- **Dichiarazione di apertura (vincolante, dizionario §1 Assunzione 1):** le due
  strutture «Buby Lago» e «Buby Montagna» sono **fittizie**: mappatura 1:1 dei due
  tipi di hotel del CSV Kaggle Hotel Booking Demand (Resort Hotel → Buby Lago,
  City Hotel → Buby Montagna). Nessun dato Buby reale esiste.
- Oggi si congela: schema (migrazioni 0001–0005) + contratto API (`openapi.yaml`
  1.0.0), con sign-off del catalogo KPI da parte di entrambi i team.
- Percorso: analisi → processo → schema → contratto → disclosure → freeze → next steps.
- Fonte: dizionario §1 Assunzione 1 («Va detto al SAL 1 e nella slide di apertura»).

## Slide 2 — ANALISI: baseline verificata al centesimo

- Dopo deduplica esatta (**87.396** righe da 119.390 lorde) e filtro
  `is_canceled=0, nights>0, adr>0`:

| Metrica | Valore |
|---|---:|
| Prenotazioni valide | **61.777** |
| Room-night | **218.410** |
| Ricavo realizzato | **22.976.960,13 €** |
| ADR | **105,20 €** |
| Cancellation rate (post-dedup) | **27,49%** |

- Ricomputata oggi dall'audit direttamente dal DB seedato (Postgres 16): match
  esatto; `Σ kpi_daily.revenue` e `Σ room_nights` coincidono (1.605 righe kpi_daily).
- Regola vincolante: **qualsiasi endpoint KPI che non restituisce questi numeri è
  sbagliato**. Il campione committato (5.000 righe, seed 42) gira sempre in CI:
  3.564 valide / 12.696 room-night / 1.350.503,84 € / cancel 0,2696.
- Fonte: dizionario §3 «Baseline pulita»; audit §2 R4, §5 D4/D7.

## Slide 3 — ANALISI: le regole KPI (catalogo da firmare)

- Stessa metrica, definizioni diverse: oscillazioni del 10–40%. Regole vincolanti
  (dizionario §3, sign-off in `docs/sal1/kpi-signoff.md`):
  - **Cancellation rate:** solo cancellate, dopo deduplica; **No-Show a parte**
    (37,04% raw vs 27,49% dedup vs 27,98% se si fonde il No-Show).
  - **ADR:** revenue / room-night, solo `adr > 0`; mediana a fianco
    (media 101,83 distorta dal typo 5400,0 e da 1.959 zeri).
  - **Revenue:** `adr × nights`, solo non cancellate
    (42,72 M€ lordo vs 25,996 M€ realizzato vs 22,98 M€ realizzato+dedup).
  - **Seasonality:** medie **per mese dell'anno**, mai totali mensili grezzi
    (2015 e 2017 sono anni parziali).
  - **Channel mix:** per `market_segment` (8 valori); `agent`/`company` sono ID
    numerici non mappati → nessuna disaggregazione per OTA con nome.
  - **Occupancy / RevPAR:** contro la capacità **assunta** (slide 12), mai
    presentati come misurati.
- Fonte: dizionario §3; audit §1 (verdetto), delivery-plan §0.

## Slide 4 — ANALISI: il corpus reputazione è reale (TripAdvisor)

- ADR 0003 opzione E: `hotel_bookings.csv` per occupazione/ricavi, corpus
  TripAdvisor (`jniimi/tripadvisor-review-rating`, Li et al. 2013) per reputazione
  e testo. Unica opzione con **punteggio per dimensione reale**: nessuna sintesi.
- **N reale = 1.638 recensioni, non 20k:** le due strutture più recensite hanno
  762 e 876 recensioni; sotto 10k si prende tutto e si fissa l'N reale
  (campione committato `data/raw/sample_tripadvisor.csv`, ~1,6 MB).
- **Mapping scelto e immutabile dopo il SAL 1** (regola deterministica: più
  recensioni → Buby Montagna):

| Proprietà | `ta_hotel_id` (offering_id) | Recensioni | `overall` medio |
|---|---:|---:|---:|
| Buby Lago (1) | 93618 | 762 | 3,86 |
| Buby Montagna (2) | 2079052 | 876 | 4,40 |

- **Correzione offering_id:** nella distribuzione HF `hotel_id` è l'id della
  *recensione* (201.295 valori distinti su 201.295 righe); il vero id hotel si
  recupera da `review.txt` unendo su `id` — risolve il 100% delle righe. Senza
  questo passo il mapping sarebbe impossibile.
- **Cinque dimensioni reali** dal corpus: cleanliness, value, location, rooms,
  sleep_quality (+ overall). Sono etichette deboli oneste per valutare l'NLP (D14).
- **Corpus solo inglese** (tutte `__label__en`): accettato per la reputazione;
  la demo email resta italiana; niente ABSITA per ora.
- Fonte: dizionario §1 «Decisione TripAdvisor»; ADR 0003 §1–2; audit §5 D8.

## Slide 5 — PROCESSO: ETL e decisioni di pulizia

- Pipeline: CSV → **deduplica sulle 32 colonne originali** → pulizia → load →
  `kpi_daily`. La deduplica viene **prima** di aggiungere/rinominare colonne:
  quella su 34 colonne (file arricchito, superato da ADR 0003 E) darebbe
  103,05 €/notte e 25,99 M€ invece di 105,20 €/notte e 22,98 M€.
- Decisioni solo-dataset registrate nel dizionario (Assunzione 5):
  - NA di pandas default: i letterali `NA` (4 in `children`) e `NULL`
    (`agent`/`company`/`country`) diventano NaN; `children`/`babies` NaN → 0.
  - **`adults=0` si tengono** (385 post-dedup): toglierli rompe il baseline.
  - **Nessun clipping di `adr`:** il typo 5400,0 è su una riga cancellata, non
    entra mai in un KPI (verificato: ricavo identico con/senza clipping).
  - `agent`/`company` NaN → NULL nel DB, non la stringa "nan".
- `nights` è una colonna **GENERATED** di Postgres (weekend + week): il loader
  non la scrive mai.
- Fonte: dizionario §1 Assunzioni 4–5, §2; audit §3 S9; playbook solo-dataset §1.

## Slide 6 — PROCESSO: disciplina anti-leakage

- `true_category` e `true_urgency` vivono **solo** in `data/eval/email_gold.csv`:
  mai scritte nel DB, mai lette dalla pipeline. Verificato oggi: 0 etichette
  nel DB (800 email, `category`/`urgency`/`draft_reply` NULL).
- La colonna `guest_requests.urgency` (migrazione 0005) è l'output **predetto**
  da D15, non l'etichetta gold: la regola anti-leakage vale anche per lei.
- Niente `sentiment`/`topics` in `reviews`: sono output del modello (D14),
  calcolati al momento della query (decisione S8, slide 9).
- Valutazione onesta by construction: le cinque dimensioni reali fungono da
  etichetta debole per il sentiment; il gold file valuta il classificatore email.
- Lezione del postmortem 2026-11-11: 25 testi distinti nel dataset arricchito
  rendevano la valutazione una lookup table al 100% → generatore con ≥8 template
  per categoria × slot (nomi, date, camere, proprietà, registro).
- Fonte: dizionario §2 `guest_requests`/`reviews`, «Decisioni pre-freeze»; audit §2 R6, §5 D9.

## Slide 7 — PROCESSO: solo-work playbook, notifica, CI verificata

- DA-1/DA-2/DA-3 non presidiati: WSA-3 ha eseguito B6/D3/D4/D8/D9 (+ metà dati
  di D7) in solo secondo `docs/playbooks/solo-dataset.md`; **ogni decisione solo
  è registrata nel dizionario** il giorno in cui è presa.
- **Notifica al team** (playbook §8.1): bozza in `docs/client-comms.md`, finestra
  obiezioni fino al SAL 1; il silenzio dopo la scadenza è consenso documentato.
  Stato onesto: **ancora da inviare** (ledger HA-03); riassegnazione formale al
  sync (HA-04). Il voto di collaborazione non può reggersi su un WSA che fa il
  lavoro di due team senza traccia di consenso.
- **CI verificata** (GitHub Actions, verde su master e sulle PR mergiate):
  ruff/isort pinnati → migrazioni up → `alembic check` (models ≡ migrazioni) →
  schema test → round-trip (downgrade base → upgrade) → inverso a un passo
  (NOT NULL ripristinati) → seed + data test dal campione committato → GitGuardian.
  Niente falso verde: il test sul campione gira sempre; quello sul CSV completo
  si salta in CI per design (il CSV completo resta locale/drive cliente).
- Numeri di oggi: schema test **12 passed** (post-0005), data test **12 passed**,
  backend **28 passed, 1 skipped** sul merged master, frontend vitest **3 passed**
  + tsc pulito + build OK.
- Fonte: playbook §0/§8; client-comms §Notifica; audit §4–5; record WP2 §3, WP3 §2.

## Slide 8 — SCHEMA: 5 tabelle, migrazioni 0001–0005

- ERD completo in `docs/erd.md` (mostrare il diagramma): `properties` (2 righe) →
  `bookings` (87.396), `reviews` (1.638), `guest_requests` (800), `kpi_daily` (1.605).
- **`bookings.nights` GENERATED** (weekend + week): calcolata da Postgres, mai
  scritta dal loader.
- **`kpi_daily.occupancy numeric(5,4)`**: rapporto **0–1, senza ×100**; 4 decimali
  dalla migrazione 0004 (con 2 si quantizzava a 1 punto percentuale). Una riga
  per hotel e giorno (UNIQUE), inclusi i giorni a zero; ricavo spalmato sui
  giorni di soggiorno, non concentrato sull'arrivo.
- **Nessuna FK `reviews` ↔ `bookings`**: il legame è `property_id`, asserito
  (Assunzione 2). Vincolo test-enforced.
- **0005 — `guest_requests.urgency`** varchar(10) nullable, CHECK
  `low/medium/high`: casa nello schema per l'output predetto di D15 prima del
  freeze; NULL finché D15 non la produce. 0001–0004 byte-intatte.
- Verifica audit: **DB live ≡ models.py ≡ ERD ≡ dizionario**, colonna per colonna
  (tipi, nullabilità, CHECK, indici, generated column); `alembic check` pulito;
  round-trip + inverso a un passo su scratch DB.
- Fonte: dizionario §2; erd.md; audit §3; record WP2 §1/§3.

## Slide 9 — SCHEMA: decisioni pre-freeze S7/S8 (ratifica al SAL 1)

- **S7 — niente tabella `users` in v1.** Lo schema congelato ha 5 tabelle. Gli
  utenti demo **saranno** hardcoded in `backend/app/config.py` al momento di
  D11, con i 3 ruoli ADR 0001 (`admin`, `manager`, `property_manager`). Una
  tabella `users` vera più avanti = protocollo contract-bump.
- **S8 — output NLP al momento della query.** Sentiment/topics/sintesi (D14) si
  calcoleranno quando la query li chiede: nessuna tabella derivata in v1, nessun
  UPDATE sulla sorgente a ogni re-run del modello. Persistenza futura = stesso
  protocollo contract-bump. L'urgenza email ha invece la sua colonna (0005).
- Protocollo contract-bump: **nuovo ADR + bump di `info.version` in
  `openapi.yaml` + migrazione dedicata**. Mai modificare le migrazioni mergiate
  dopo il freeze: solo nuove revisioni.
- Fonte: dizionario §2 «Decisioni pre-freeze 2026-11-19»; audit §3 S7/S8; record WP2 §1.

## Slide 10 — CONTRATTO: OpenAPI 1.0.0, 11 operazioni, 4 su dati reali

- `openapi.yaml` (OpenAPI 3.0.3, `info.version: 1.0.0`) = single source of truth;
  mirror `frontend/mock/openapi.yaml` **byte-identico**; lint Redocly **0 errori**
  (4 warning inerenti al contratto pinned).
- **11 operazioni**; **4 implementate su dati reali** (PR #9 mergiata):
  `listProperties`, `getKpiSummary`, `getKpiDaily`, `login`.
  Verificate contro gli esempi pinned: il summary restituisce **tutti e 7** i
  campi dell'esempio (61777 / 22976960.13 / 218410 / 105.20 / 0.2749 /
  0.6558 / 68.99) sul DB pieno.
- **Mock Prism** dalla spec: serve la baseline, 401 senza token; la dashboard
  gira sul mock fino allo swap D17 (dichiarato, non spacciato per integrato).
- Convenzioni: liste paginate `page`/`page_size` (default 50, max 200) con
  envelope `{ data: [...], meta: { page, page_size, total, total_pages } }`;
  ogni 4xx/5xx usa `{ error: { code, message, details? } }`; rapporti
  (occupancy, cancellation_rate, share) sempre **0–1**, mai percentuali.
- Fonte: openapi.yaml info/conventions; api-contract.md; audit §4; record WP3 §1–2.

## Slide 11 — CONTRATTO: fix S1/S2/S3 prima del freeze + auth dichiarata

- **S1 (PR #11):** `occupancy_avg` = formula **pooled**
  `Σroom_nights / (Σroom_count × giorni della finestra)`:
  218.410 / (420 × 793) = **0,6558** (esempio pinned). La media dei rapporti
  giornalieri darebbe 0,6534: definizione da non usare. Testo corretto in
  entrambi i siti della spec.
- **S2 (PR #11):** riepilogo = **coorte di arrivi** (`bookings.arrival_date`
  nella finestra, estremi inclusi); giornaliero = **giorni di soggiorno**
  (`kpi_daily.date`). Ai bordi i totali differiscono **per progetto**: sulla
  finestra di default, 19 giorni / 723 room-night / 105.263,50 € oltre il
  2017-08-31 entrano nel riepilogo e restano fuori dalla serie giornaliera.
  Footnote UI dove i due widget coesistono.
- **S3 (PR #11):** daily con `property_id` omesso/null = una riga per data, somme
  delle due proprietà; occupancy/RevPAR su capacità combinata **420**; adr null
  a zero attività.
- **Auth — disclosure esplicita:** lo schema è congelato (JWT bearer, ruoli
  `admin`/`manager`/`property_manager`), ma **l'enforcement è D11**: oggi il
  login restituisce un token statico finto (`token-finto`, qualsiasi credenziale)
  e gli endpoint protetti rispondono 200 anche senza token o con token spazzatura.
  La spec congelata promette 401 che l'implementazione non applica ancora:
  dichiarato qui e in `api-contract.md`. `/api/properties` e `/api/auth/login`
  sono senza auth per la demo.
- Fonte: audit §3 S1–S3, §4; dizionario §3 «Finestra e aggregazione»; record WP1 §1/§3, WP3 §3 (G1/G2).

## Slide 12 — DISCLOSURE (slide dedicata, non una nota a piè di pagina)

Tutte le sostituzioni e i limiti dei dati, dichiarati dal team prima che il
cliente li scopra (audit §3 S4, §8.4):

1. **Strutture fittizie:** Buby Lago/Buby Montagna sono la mappatura 1:1 dei due
   tipi di hotel del CSV (Resort/City). Nessun dato Buby reale.
2. **Legame recensioni ↔ prenotazioni ASSERITO a livello di proprietà**, non
   fattuale: un recensore TripAdvisor del 2012 non è l'ospite di una prenotazione
   del 2016. KPI occupazione/ricavo solo da bookings; reputazione solo da reviews.
3. **Capacità assunta 190/230 camere** (Lago 190 ← picco osservato 187 + margine;
   Montagna 230 ← picco 226 + margine), **inferita dal picco, mai misurata**.
   Circolarità dichiarata: l'occupazione non può superare il 100% per
   costruzione. Accettabile solo se etichettata come assunzione; frode se
   presentata come misurata. Occupancy/RevPAR portano la footnote in dashboard.
4. **Email sintetiche:** 800 generate (seed 42, 6 categorie), nomi/indirizzi
   inventati (GDPR, O1). Non sono corrispondenza reale di ospiti.
5. **S4 — nessun overlap temporale (audit §3):** le recensioni sono **tutte del
   2012** (`post_date` 2012-01-02…2012-12-19, verificato sulla CSV committata);
   le prenotazioni coprono **2015-07…2017-09**: **zero mesi in comune**. Non
   esiste alcuna analisi congiunta a livello di mese: l'analisi «proprietà ×
   mese» sancita da ADR 0003 è vuota, resta solo la comparazione a livello di
   proprietà. Il trend di reputazione è una serie **solo-2012**: nessuna lettura
   causale accanto all'occupazione 2015–17.
6. **Corpus solo inglese:** tutte le 1.638 recensioni sono `__label__en`;
   accettato per la reputazione, la demo email resta italiana (niente ABSITA).
7. **N = 1.638, non 20k:** le due strutture più recensite hanno 762 + 876
   recensioni; si prende tutto e si fissa l'N reale. Campione ~1,6 MB.
8. **Nessun dato del cliente è mai arrivato:** la sostituzione è dichiarata
   (ADR 0003 opzione E); la richiesta dati scritta B4 è ancora da archiviare
   (🔴, ledger HA-09). Nessun dato cliente entra nel repository.

- Fonte: dizionario §1 Assunzioni 1–5 + «Decisione TripAdvisor» + S4; audit §3 S4/S6, §2 R4; ADR 0003 «Punto debole».

## Slide 13 — Il freeze: cosa si congela e come si cambia dopo

- **Si congela al SAL 1:** schema (migrazioni **0001–0005**, 5 tabelle) +
  contratto **`openapi.yaml` 1.0.0** (11 operazioni, esempi pinned, convenzioni).
  I due `ta_hotel_id` (93618 / 2079052) sono immutabili dopo il SAL 1.
- **Sign-off del catalogo KPI** da parte di entrambi i team
  (`docs/sal1/kpi-signoff.md`, 6 owner nominati): il freeze senza sign-off non è
  il freeze valutato (HA-01). Campi firma vuoti: firmano gli umani al SAL 1.
- **Protocollo contract-bump** per ogni modifica successiva: nuovo ADR + bump di
  `info.version` + migrazione dedicata. Vale per tabella users (S7), tabelle
  derivate NLP (S8), qualsiasi cambio di regola KPI o shape API.
- **Tag `v1.0.0`:** applicato dall'orchestratore **dopo il merge** del pacchetto
  SAL 1 — stato: *pending merge*, non ancora applicato.
- Checklist di freeze con evidenze: `docs/sal1/freeze-checklist.md`
  (delivery-plan §4).
- Fonte: delivery-plan §4; dizionario §2 «Decisioni pre-freeze»; ledger HA-01.

## Slide 14 — Prossimi passi e rischi

- **D11 auth reale** (JWT + 3 ruoli + enforcement; oggi token finto): rimuove il
  gap dichiarato alla slide 11. Da risolvere con il cliente al SAL 1 la
  contraddizione «auth cuttable» vs autenticazione nominata nel brief (HA-14).
- **7 operazioni contrattuali mancanti:** kpis/channels, kpis/seasonality,
  reviews/summary, reviews, bookings, guest-requests GET/PATCH + contract test
  in CI (spec vs implementazione).
- **D14/D15 NLP — componente obbligatoria del brief, oggi zero codice:**
  sentiment/topics/sintesi sulle 1.638 recensioni reali; classificatore email +
  bozze LLM human-in-the-loop sul gold file. Owner nominato per D14 per primo.
- **D16 forecast** — oggi zero codice, stretch per delivery-plan §11; la
  contraddizione con l'obiettivo del caso «prevedere la domanda» va risolta col
  cliente al SAL 1 (HA-14, memo WP12).
- **D17 swap mock → reale** + E2E (la headline WSA «integrazione con i dati
  reali»): la dashboard lascia Prism, weekly real-data smoke da subito.
- **Deploy (D18)** + demo finale 18 dic con 2 rehearsal; demo live in locale,
  istanza pubblica scaldata prima dei check esterni.
- **Rischi nominati:** (1) staffing — riassegnazione formale dei workstream
  DA-1/DA-2/DA-3/WSA-2 (HA-04): oggi un WSA porta due team, il voto di
  collaborazione è a rischio; (2) **O2 chiavi LLM e chi paga: decisione scaduta
  il 16 nov** (HA-05), blocca D15 e i secret di deploy. Aperti anche O1/O3/B4
  (HA-06/07/09) e il gap O5 del 13 nov (HA-02, riconosciuto nello stato da inviare).
- Fonte: audit §5/§6/§8; delivery-plan §2/§9/§11; ledger HA-02/04/05/14.

---

## Copertura disclosure → slide (verifica per il relatore)

| Assunzione / decisione (fonte) | Slide |
|---|---|
| Assunzione 1 — strutture fittizie, mappa 1:1 (dizionario §1) | 1 (apertura), 12.1 |
| Assunzione 2 — legame asserito a livello di proprietà (dizionario §1) | 8 (no FK), 12.2 |
| Assunzione 2 / **audit S4** — zero overlap 2012 vs 2015-07…2017-09, niente join mensile, trend solo-2012, nessuna lettura causale | 12.5 |
| Assunzione 3 — capacità assunta 190/230, picco-inferita, circolarità, mai misurata (dizionario §1) | 3 (regola), 12.3 |
| Assunzione 4 — deduplica 32 colonne originali (dizionario §1) | 5 |
| Assunzione 5 — decisioni di pulizia: NA default, adults=0 tenuti, no clipping adr, NaN→NULL (dizionario §1) | 5 |
| Decisione TripAdvisor — mapping immutabile dopo SAL 1 (93618/2079052) | 4, 13 |
| Decisione TripAdvisor — correzione offering_id (`hotel_id` = id recensione) | 4 |
| Decisione TripAdvisor — corpus solo inglese | 4, 12.6 |
| Decisione TripAdvisor — N reale 1.638, non 20k | 4, 12.7 |
| Email sintetiche 800, nomi inventati (dizionario §2) | 6, 12.4 |
| Nessun dato cliente mai arrivato; sostituzione dichiarata; B4 pending (audit §2 R4) | 12.8 |
| Auth: schema congelato, enforcement D11, token finto oggi (audit §4) | 11 |
| Dashboard sul mock fino a D17, non spacciata per integrata (audit §2 R7) | 10, 14 |

*Outline preparato da WP5 (2026-11-19). La presentazione, il dry run e il freeze
con sign-off sono azioni umane (ledger HA-11, HA-01).*
