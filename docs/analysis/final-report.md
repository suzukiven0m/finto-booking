# Report finale dati — Buby Travel (WP14 / D18)

**Data:** 2026-11-20 · **Perimetro:** risultati KPI, metriche dei modelli e
caveat dell'intero progetto, come consegnati alla demo finale (18 dic).
**Regola dei numeri:** ogni valore citato viene dai JSON committati
(`data/eval/demand_analysis.json`, `data/eval/email_metrics.json`,
`data/eval/review_nlp_metrics.json`, `data/eval/review_summaries.json`) o dal
dizionario (`docs/data-dictionary.md` §1/§3). La lista di spot-check in §5
mappa ogni numero alla sua fonte; nessun numero è stimato a memoria.

Fonti estese: `docs/analysis/demand-pricing.md` (WP12),
`docs/analysis/reputation-nlp.md` (D14/WP9), `docs/analysis/email-assistant.md`
(D15/WP10), `docs/sal1/slides-outline.md` (disclosure, slide 12).

---

## 1. Risultati KPI (domanda e prezzi)

### 1.1 Baseline pulita (pinned, dizionario §3)

Deduplica esatta sulle 32 colonne originali (119.390 righe lorde → 87.396),
poi filtro `is_canceled=0, nights>0, adr>0`:

| Metrica | Valore | Fonte |
|---|---:|---|
| Righe post-dedup | 87.396 | demand JSON `baseline.rows` |
| Prenotazioni valide | 61.777 | `baseline.valid` |
| Room-nights | 218.410 | `baseline.room_nights` |
| Ricavo realizzato | 22.976.960,13 € | `baseline.revenue` |
| ADR pooled | 105,20 € | `baseline.adr` |
| Mediana ADR (righe valide) | 95,20 € | `baseline.median_adr_valid_rows` |
| Cancellate | 24.025 | `baseline.canceled` |
| Cancellation rate (post-dedup) | 27,49% | `baseline.cancel_rate` |
| Occupazione media (pooled) | 0,6558 | dizionario §3: 218.410/(420×793) |
| RevPAR | 68,99 € | contratto pinned + dizionario §3 |

Campione committato (5.000 righe, seed 42 — quello che gira in CI): 3.564
valide / 12.696 room-night / 1.350.503,84 € / cancel 0,2696 (dizionario §3).
Il CSV completo resta sulla drive del cliente: nessun dato cliente nel repo.

### 1.2 Stagionalità — medie per mese dell'anno (mai totali grezzi)

Combined (capacità assunta 420; ricavo = media giornaliera per proprietà):
minimo **gennaio 6.149,95 €/giorno/proprietà** (occupazione 0,3982, ADR arrivi
69,98 €), massimo **agosto 25.029,60 €** (occupazione 0,7810, ADR 151,00 €):
~4× tra bassa e alta stagione. Fonte: demand JSON `seasonality.combined`.

Le due strutture sono complementari (`seasonality.per_property`):

- **Buby Lago** fortemente estivo: occupazione giugno 0,8853 / luglio 0,8691 /
  agosto **0,9172**, ADR agosto **175,86 €**; inverno debole (gennaio
  occupazione 0,3902, ADR 49,99 €).
- **Buby Montagna** più piatta: picco ADR a maggio (**126,22 €**), luglio
  sotto la propria media (luglio occupazione 0,5597 contro 0,8691 del Lago).

2015 e 2017 sono anni parziali: gennaio–giugno osservati solo 2016–17,
ottobre–dicembre solo 2015–16 (`days_observed`/`years_observed` nel JSON).

### 1.3 Canali (market_segment, 8 valori)

Quote/cancellazioni su tutte le righe post-dedup; ricavo/ADR sulle valide
(demand JSON `channels`):

| Segmento | Pren. | Share | Cancel | Ricavo (€) | Share ricavo | ADR (€) |
|---|---:|---:|---:|---:|---:|---:|
| Online TA | 51.618 | 59,06% | 35,35% | 12.973.686,94 | 56,46% | 116,31 |
| Offline TA/TO | 13.889 | 15,89% | 14,85% | 4.595.718,77 | 20,00% | 82,33 |
| Direct | 11.804 | 13,51% | 14,72% | 3.927.104,69 | 17,09% | 126,96 |
| Groups | 4.942 | 5,65% | 27,01% | 922.928,01 | 4,02% | 75,77 |
| Corporate | 4.212 | 4,82% | 12,11% | 483.748,83 | 2,11% | 67,90 |

(Complementary/Aviation/Undefined: quote ≤0,8%, tabelle complete nel JSON.)
Online TA domina ma cancella oltre una prenotazione su tre; Direct ha l'ADR
più alto e produce il 17,09% del ricavo dal 13,51% delle prenotazioni.
`agent`/`company` sono ID numerici non mappati: **nessuna disaggregazione per
OTA con nome** (dizionario §3).

### 1.4 Lead-time e cancellazioni

Il rischio cresce monotono col lead-time (demand JSON `lead_time.buckets`,
tutte le righe post-dedup): **8,43%** (0–7 giorni, n=18.304) → **39,74%**
(>180 giorni, n=11.765), ~4,7×. Correlazione lead-time↔cancellazione
**0,1848** (Pearson, `lead_time.corr_lead_cancel`: associazione). I mesi di
picco si prenotano presto: luglio media 112,0 / mediana **103** giorni, agosto
102,7 / 87 (`lead_time.by_month`). Segmenti a lead lungo: Groups media 147,6,
Offline TA/TO 106,1; Corporate last-minute (16,3) (`lead_time.by_segment`).

### 1.5 ADR ↔ occupazione e effetti ospite (associazioni, non causalità)

- Correlazione giornaliera ADR–occupazione **0,5535** (806 giorni,
  `adr_occupancy.daily_corr_adr_occupancy`); mensile combined 0,6898, Lago
  0,7620, Montagna 0,6266 (basi miste arrivi/stay-day, dizionario §3).
- ADR realizzato per bucket di occupazione (`adr_by_occupancy_bucket`):
  giorni <0,40 → **73,28 €** (102 giorni); giorni ≥0,80 → **128,55 €**
  (202 giorni): ~1,75×. La stagionalità muove entrambe le variabili: nessun
  esperimento di prezzo, nessuna elasticità stimabile.
- Ospiti ripetuti (`guest_effects`): cancellano al **7,64%** (n=3.415) contro
  **28,30%** dei nuovi (n=83.981), ma sono solo il 3,91% delle righe.
  Transient puro 30,11%; Group 9,93%, Contract 16,31%, Transient-Party 15,24%.
- **Anomalia da non leggere come policy:** Non Refund cancella al **94,70%**
  (n=1.038) — verosimile effetto di selezione/artefatto; Refundable n=107,
  troppo piccolo per conclusioni.

## 2. Metriche dei modelli

### 2.1 Sentiment recensioni (D14, etichette deboli)

Modello `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`
(revision `82107f4c…`), zero-shot, nessun training; score
`P(positive)−P(negative)`. I voti reali 1–5 degli ospiti sono l'etichetta
debole: **correlazione ≠ accuratezza** (review NLP JSON `sentiment`):

| Dimensione | Spearman (pooled, n=1.638) | Pearson |
|---|---:|---:|
| overall | **0,5517** | 0,5894 |
| rooms | 0,4565 | 0,5057 |
| value | 0,4396 | 0,4999 |
| cleanliness | 0,4154 | 0,4579 |
| sleep_quality | 0,4082 | 0,4438 |
| location | 0,2126 | 0,2230 |

Per proprietà (overall): **Lago ρ=0,6266** (n=762), **Montagna ρ=0,4370**
(n=876). Label pooled: negative **352**, neutral **477**, positive **809**
(Lago 196/277/289; Montagna 156/200/520).

### 2.2 Topics (zero-shot NLI multi-label)

`facebook/bart-large-mnli` (revision `d7645e12…`), ipotesi
«This review discusses {}.», soglie per-topic calibrate su probe di **20
recensioni** (120 giudizi manuali, `topic_probe_annotations.csv`):

| Topic | Soglia | F1 probe | Prevalenza pooled |
|---|---:|---:|---:|
| cleanliness | 0,70 | 0,889 | 0,4664 |
| staff | 0,55 | 0,929 | 0,6862 |
| location | 0,70 | 0,880 | 0,6813 |
| breakfast | 0,50 | 0,909 | 0,2265 |
| noise | 0,90 | 0,933 | 0,1783 |
| value | 0,85 | 0,857 | 0,7912 |

F1 probe **ottimistico** (probe piccola, stesso corpus, annotatore unico).
Prevalenza = «se ne parla», non giudizio positivo. Pattern dimensione
(`topics.dimension_patterns`, mappa dichiarata noise→sleep_quality):

- **noise → sleep_quality: delta −0,696** (media 3,596 con menzione vs 4,292
  senza, n=292): il segnale negativo più netto, coerente per proprietà
  (−0,626 Lago, −0,752 Montagna).
- value → value: +0,805 (4,048 vs 3,243, n=1.296) — associazione, e il topic
  value è il peggio calibrato: non è «il prezzo guida la soddisfazione».
- cleanliness +0,172, location +0,070: la menzione da sola non discrimina.

Sintesi mensili **estrattive** (niente LLM, O2 gated): 24 sintesi (2 proprietà
× 12 mesi del 2012), k=3 frasi reali tracciabili a `review_id`/`post_date`
(`review_summaries.json`). Output NLP solo a livello dati (S8): il contratto
v1 non espone output del modello, l'esposizione API è un contract-bump.

### 2.3 Email (D15, classificatore lessicale + bozze HITL)

800 email sintetiche, gold allineato **800/800** (`email_metrics.json`
`gold_alignment`). Macro-F1 categoria **0,9901**, urgenza **0,9659**:

| Categoria | F1 | | Urgenza | F1 |
|---|---:|---|---|---:|
| availability | 0,9848 | | low | 0,9555 |
| cancellation | 1,0000 | | medium | 0,9422 |
| complaint | 1,0000 | | high | 1,0000 |
| special_request | 0,9847 | | | |
| billing | 1,0000 | | | |
| info | 0,9710 | | | |

Confusion summary: categoria — **8 errori su 800**, tutti verso `info`
(4 availability + 4 special_request); urgenza — **27 errori** (22 low→medium,
5 medium→low), high perfetto (263/263). `--persist` è idempotente e HITL-safe
(clausola `AND status != 'sent'`: le righe inviate non si sovrascrivono).

**Onestà obbligatoria:** l'F1 è sul corpus sintetico che ha generato le stesse
regex (~48 template, slot controllati). **Non è evidenza di performance su
email reali**; un classificatore lessicale non generalizza fuori dal
vocabolario del generatore. Upgrade LLM gated su HA-05 (chiavi + chi paga).

## 3. Caveat — tutti, vincolanti

1. **Strutture fittizie** (Assunzione 1): Buby Lago/Buby Montagna = mappatura
   1:1 dei due tipi di hotel del CSV Kaggle (Resort/City), dataset portoghese
   2015–2017. Nessun dato Buby reale.
2. **Legame recensioni↔prenotazioni asserito** (Assunzione 2): per proprietà,
   non fattuale. KPI occupazione/ricavo solo da bookings; reputazione solo da
   reviews; nessuna analisi congiunta per singola prenotazione.
3. **S4 — zero overlap temporale:** recensioni tutte 2012
   (2012-01-02…2012-12-19), prenotazioni 2015-07…2017-09: zero mesi in comune.
   Nessuna analisi congiunta mensile; trend reputazione solo-2012, nessuna
   lettura causale accanto a occupazione/ricavi.
4. **Capacità assunta + circolarità** (Assunzione 3): 190 Lago / 230 Montagna
   inferite dal picco osservato (187/226) + margine. Per costruzione
   l'occupazione non può superare il 100%. Occupancy/RevPAR mai presentati
   come misurati (footnote in dashboard).
5. **Email sintetiche:** 800 generate (seed 42), nomi/indirizzi inventati
   (GDPR, O1). F1 non trasferibile a email reali (§2.3).
6. **Corpus solo inglese, N=1.638, due proprietà:** statistiche descrittive,
   non inferenza su una popolazione. N reale 1.638, non 20k.
7. **Nessun dato cliente mai arrivato (B4):** sostituzione dichiarata
   (ADR 0003 opzione E); richiesta scritta da archiviare (HA-09, overdue).
8. **Etichette deboli:** voti 1–5 soggettivi, non generati dal modello;
   correlazione ≠ accuratezza; nessun training/test held-out. Mappa
   noise→sleep_quality è un'assunzione dichiarata.
9. **Troncamenti:** sentiment 512 token (limite del modello): **112/1.638 =
   6,84%**; topics 256 token (scelta di runtime, il modello arriva a 1024):
   **420/1.638 = 25,64%** — le menzioni oltre il tetto non sono viste.
10. **Probe ottimistica:** 20 recensioni, stesso corpus, annotatore unico;
    falsi negativi irrecuperabili (menzioni esplicite con score 0,21/0,35).
11. **Associazione ≠ causazione:** nessuna elasticità, nessun esperimento di
    prezzo; correlazione mensile ADR–occupazione a basi miste (arrivi vs
    stay-day); Non Refund 94,70% verosimile selezione; Refundable n=107.
12. **Anni parziali:** solo medie per mese dell'anno, mai totali grezzi.
13. **Canali non disaggregabili per OTA con nome** (`agent`/`company` ID non
    mappati).
14. **S8 — output NLP query-time, mai nel DB:** non esposti dal contratto v1;
    esposizione API = contract-bump (nuovo ADR + bump info.version).
15. **Sintesi estrattive, non generative** (O2/HA-05 human-gated).

## 4. Comandi riproducibili

Tutti dalla root del repo; venv backend con `backend/requirements.txt` +
`data/requirements.txt` (torch CPU index: nota in `data/requirements.txt`).
DB: compose postgres (`docker compose -f infra/docker-compose.yml up -d`).

```bash
# seed (idempotente; campione committato — il completo è nel playbook)
PYTHONPATH=backend backend/.venv/bin/python data/etl/load_bookings.py data/raw/sample_hotel_bookings.csv
PYTHONPATH=backend backend/.venv/bin/python data/etl/load_reviews.py
PYTHONPATH=backend backend/.venv/bin/python data/etl/gen_emails.py
PYTHONPATH=backend backend/.venv/bin/python data/etl/build_kpi_daily.py
PYTHONPATH=backend:data backend/.venv/bin/python data/etl/classify_emails.py --persist

# eval email (scrive email_metrics.json) / analisi domanda (demand_analysis.json)
PYTHONPATH=backend:data backend/.venv/bin/python data/etl/classify_emails.py
PYTHONPATH=backend:data backend/.venv/bin/python data/etl/analyze_demand.py

# NLP recensioni: ~2h41m CPU, pesi HF (~2GB) al primo download — NON è CI.
# Comando sidecar completo (repo ro, eval scrivibile): reputation-nlp.md §5.
PYTHONPATH=backend:data backend/.venv/bin/python data/etl/run_review_nlp.py

# test + smoke (dalla root del repo)
(cd backend && .venv/bin/python -m pytest -q)        # 140 passed, 1 skipped
PYTHONPATH=backend:data backend/.venv/bin/python -m pytest -q data/tests
# con uvicorn acceso su :8000:
backend/.venv/bin/python backend/tests/e2e_smoke.py  # invariante 800 draft/0 sent
cd frontend && npm test -- --run && npm run typecheck && npm run build

# release (WP14)
docker compose -f infra/docker-compose.yml config -q
docker build -t buby-api:wp14 backend/ && docker build -t buby-web:wp14 frontend/
```

Nota: dove host→container TCP è bloccato (VPN), gli script dati girano nel
sidecar `--network container:buby-postgres` (comandi in reputation-nlp.md §5,
email-assistant.md §6, demand-pricing.md §1).

## 5. Spot-check — numero → fonte

| Numero citato | Fonte esatta |
|---|---|
| 87.396 / 61.777 / 218.410 / 22.976.960,13 / 105,20 / 95,20 / 24.025 / 0,2749 | demand JSON `baseline.*` + dizionario §3 |
| 0,6558 / 68,99 | dizionario §3 (pooled 218.410/(420×793)); openapi pinned (e2e) |
| 3.564 / 12.696 / 1.350.503,84 / 0,2696 | dizionario §3 «Campione committato» |
| 6.149,95 / 25.029,60 / 0,3982 / 0,7810 / 69,98 / 151,00 | demand JSON `seasonality.combined[1,8]` |
| 0,9172 / 175,86 / 0,3902 / 49,99 / 0,8853 / 0,8691 / 0,5597 / 126,22 | demand JSON `seasonality.per_property` |
| 51.618 / 0,5906 / 0,3535 / 12.973.686,94 / 0,5646 / 116,31 | demand JSON `channels[Online TA]` |
| 11.804 / 0,1351 / 0,1472 / 0,1709 / 126,96 | demand JSON `channels[Direct]` |
| 0,0843 / 0,3974 / 18.304 / 11.765 / 0,1848 | demand JSON `lead_time.buckets/corr_lead_cancel` |
| 112,0 / 103 / 102,7 / 87 / 147,6 / 106,1 / 16,3 | demand JSON `lead_time.by_month[7,8]`, `by_segment` |
| 0,5535 / 806 / 0,6898 / 0,7620 / 0,6266 / 73,28 / 128,55 / 102 / 202 | demand JSON `adr_occupancy.*` |
| 0,0764 / 3.415 / 0,2830 / 83.981 / 0,9470 / 1.038 / 107 / 0,3011 / 0,0993 / 0,1631 / 0,1524 | demand JSON `guest_effects.*` |
| 0,5517 / 0,5894 / 0,4565 / 0,4396 / 0,4154 / 0,4082 / 0,2126 | review NLP JSON `sentiment.correlations.pooled` |
| 0,6266 / 0,4370 / 762 / 876 | review NLP JSON `sentiment.correlations.per_property` + dizionario §2 |
| 352 / 477 / 809 / 196/277/289 / 156/200/520 | review NLP JSON `sentiment.label_counts` |
| soglie 0,70/0,55/0,70/0,50/0,90/0,85; F1 0,889/0,929/0,880/0,909/0,933/0,857; probe 20 | review NLP JSON `topics.thresholds/threshold_calibration` |
| prevalenze 0,4664/0,6862/0,6813/0,2265/0,1783/0,7912 | review NLP JSON `topics.prevalence.pooled` |
| −0,696 / 3,596 / 4,292 / 292 / +0,805 / 4,048 / 3,243 / 1.296 / −0,626 / −0,752 | review NLP JSON `topics.dimension_patterns` |
| 112 / 0,0684 / 512 / 420 / 0,2564 / 256 | review NLP JSON `truncation.*` |
| 0,9901 / 0,9659 / F1 per classe / 8 errori (4+4) / 27 (22+5) / 263 / 800/800 | email JSON `category/urgency/confusion_matrix/gold_alignment` |
| 762/3,86 / 876/4,40 / 2012-01-02…2012-12-19 / solo inglese | dizionario §2 «Decisione TripAdvisor» + S4 |
| 24 sintesi, k=3 | review_summaries.json (`k`, 2×12 mesi) |
| 190/230/420, picchi 187/226 | dizionario §1 Assunzione 3 |

## 6. Citazione del corpus recensioni

Il corpus TripAdvisor deriva da **Li et al. (2013)**: Jiwei Li, Myle Ott,
Claire Cardie, *Identifying Manipulated Offerings on Review Portals*,
EMNLP 2013. Distribuzione HF `jniimi/tripadvisor-review-rating` (repository
Apache 2.0); il vero `offering_id` si recupera da `review.txt` del corpus
originale (dizionario §2 «Decisione TripAdvisor», ADR 0003).