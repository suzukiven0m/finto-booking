# Domanda e prezzi — analisi descrittiva e decisioni (WP12, R2)

**Questo memo risponde all'obiettivo del Caso 1 «Prevedere la domanda e supportare
le decisioni sui prezzi» al livello analitico** (audit R2, §6): stagionalità,
lead-time, canali, relazione ADR–occupazione, effetti di deposito/tipo
cliente/ospite ripetuto sulle cancellazioni. La metà previsionale («prevedere»)
è una decisione del cliente al SAL 1: opzioni e stima nell'ultima sezione
(HA-14). Nessun taglio silenzioso.

| | |
|---|---|
| Script | `data/etl/analyze_demand.py` — sola lettura: 3 SELECT, nessuna scrittura, nessun cambio schema |
| Output | `data/eval/demand_analysis.json` — ogni numero delle tabelle sotto viene da qui |
| Test | `data/tests/test_demand_analysis.py` — fixture senza DB + 1 integrazione DB |
| Regole vincolanti | `docs/data-dictionary.md` §3 (formule congelate), `openapi.yaml` (getKpiSeasonality, getKpiChannels) |
| Decisione cliente | `docs/reviews/human-actions.md` HA-14, SAL 1 2026-11-20; `docs/delivery-plan.md` §11 (cut-order #1, D16) |

## 1. Metodo e riproduzione

Tre SELECT sul DB (testo completo in `meta.queries` del JSON e nello script):
`bookings` (colonne dell'analisi), `kpi_daily` (room-nights e revenue per giorno
di soggiorno), `properties` (capacità assunta). Filtri, come da dizionario §3:

- **KPI** (ADR, ricavo, occupazione, stagionalità): baseline
  `is_canceled=false AND nights>0 AND adr>0`.
- **Cancellazioni e lead-time**: TUTTE le righe post-dedup (Assunzione 4: la
  dedup sulle 32 colonne originali è già avvenuta nel loader; il DB contiene
  87.396 righe sul dataset completo).
- **Capacità assunta** (Assunzione 3, non misurata): Buby Lago **190**, Buby
  Montagna **230**, combinata **420** (`properties.room_count`). Occupazione =
  room-nights del giorno / capacità, rapporto 0–1.
- **Stagionalità**: medie per mese dell'anno, mai totali grezzi (2015 e 2017
  sono parziali). `avg_adr` pooled sulle coorti di arrivi
  `Σ(adr×nights)/Σnights`; occupazione e ricavo dai giorni di soggiorno
  (`kpi_daily`); combined = somme giornaliere sulle due proprietà, `avg_revenue`
  diviso 2 (formula congelata getKpiSeasonality con property null).

Finestra osservata: arrivi 2015-07-01 → 2017-08-31; giorni di soggiorno
2015-07-01 → 2017-09-13 (806 date distinte, nessuna a zero). I valori nelle
tabelle sono riportati come nel JSON (punto decimale, stessi arrotondamenti).

Riproduzione end-to-end (host→container TCP bloccato: sidecar nel namespace di
rete del Postgres; il mount `data/eval` è l'unico scrivibile):

```bash
docker run --rm -i --network container:buby-postgres \
  -v "$PWD":/repo:ro -v "$PWD/data/eval":/repo/data/eval -w /repo \
  -e PYTHONPATH=/repo/.venv/lib/python3.12/site-packages:/repo/backend:/repo/data \
  python:3.12-slim python data/etl/analyze_demand.py
```

Lo script asserisce la baseline completa prima di scrivere il JSON: se i numeri
non tornano, è il codice a essere sbagliato (mai aggiustare il baseline).

## 2. Baseline (pinned, dizionario §3)

| Metrica | Valore |
|---|---:|
| Righe post-dedup | 87396 |
| Prenotazioni valide (filtro baseline) | 61777 |
| Room-nights | 218410 |
| Ricavo realizzato | 22976960.13 € |
| ADR pooled | 105.20 € |
| Mediana ADR (righe valide) | 95.20 € |
| Cancellate | 24025 |
| Cancellation rate (post-dedup) | 0.2749 |

## 3. Stagionalità — medie per mese dell'anno

Combined (capacità 420; `avg_revenue` = media per proprietà):

| Mese | Giorni oss. | Anni | Room-nights/giorno | Ricavo/giorno/proprietà (€) | Occupazione | ADR arrivi (€) | Pren. valide |
|---:|---:|---|---:|---:|---:|---:|---:|
| 1 | 62 | 2016–17 | 167.3 | 6149.95 | 0.3982 | 69.98 | 3547 |
| 2 | 57 | 2016–17 | 234.6 | 8671.25 | 0.5586 | 73.93 | 4562 |
| 3 | 62 | 2016–17 | 293.0 | 11245.26 | 0.6977 | 77.63 | 5551 |
| 4 | 60 | 2016–17 | 304.2 | 14940.35 | 0.7244 | 98.60 | 5392 |
| 5 | 62 | 2016–17 | 319.6 | 16342.60 | 0.7610 | 103.14 | 5784 |
| 6 | 60 | 2016–17 | 331.3 | 18739.78 | 0.7888 | 113.41 | 5308 |
| 7 | 93 | 2015–17 | 293.8 | 19749.24 | 0.6996 | 137.10 | 6719 |
| 8 | 93 | 2015–17 | 328.0 | 25029.60 | 0.7810 | 151.00 | 7489 |
| 9 | 73 | 2015–17 | 268.9 | 14602.03 | 0.6402 | 104.81 | 4922 |
| 10 | 62 | 2015–16 | 277.9 | 12191.08 | 0.6616 | 87.21 | 5118 |
| 11 | 60 | 2015–16 | 218.6 | 7806.68 | 0.5204 | 71.26 | 3808 |
| 12 | 62 | 2015–16 | 173.3 | 6887.71 | 0.4127 | 82.22 | 3577 |

Per proprietà (occupazione sulla capacità della singola struttura; ricavo
giornaliero medio, nessuna divisione):

| Mese | Lago occ. | Lago ADR (€) | Lago ricavo (€) | Montagna occ. | Montagna ADR (€) | Montagna ricavo (€) |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0.3902 | 49.99 | 4128.79 | 0.4048 | 86.24 | 8171.12 |
| 2 | 0.5550 | 54.41 | 5686.94 | 0.5616 | 90.18 | 11655.57 |
| 3 | 0.6579 | 58.99 | 7191.91 | 0.7305 | 91.39 | 15298.62 |
| 4 | 0.7068 | 77.51 | 10381.43 | 0.7388 | 115.61 | 19499.28 |
| 5 | 0.8094 | 78.48 | 11776.13 | 0.7210 | 126.22 | 20909.08 |
| 6 | 0.8853 | 103.67 | 17326.13 | 0.7092 | 123.54 | 20153.43 |
| 7 | 0.8691 | 149.81 | 23972.01 | 0.5597 | 120.73 | 15526.47 |
| 8 | 0.9172 | 175.86 | 31184.37 | 0.6684 | 122.43 | 18874.83 |
| 9 | 0.7501 | 92.13 | 14133.63 | 0.6076 | 119.02 | 16668.82 |
| 10 | 0.7329 | 64.85 | 9274.82 | 0.6027 | 108.54 | 15107.34 |
| 11 | 0.5695 | 50.74 | 5544.90 | 0.4799 | 90.69 | 10068.46 |
| 12 | 0.4310 | 68.77 | 5317.29 | 0.3976 | 94.27 | 8458.13 |

(Giorni osservati per proprietà: come combined, tranne settembre Montagna 66
invece di 73; tabelle complete nel JSON, `seasonality.per_property`.)

**Lettura.** Le due strutture hanno stagionalità complementari: Lago è
fortemente estiva (agosto occupazione 0.9172, ADR 175.86; giugno 0.8853) e in
bassa stagione d'inverno (gennaio 0.3902, ADR 49.99); Montagna è più piatta,
con picco di ADR a maggio (126.22) e luglio sotto la propria media
(luglio occupazione 0.5597 contro 0.8691 del Lago). Il picco combined di
agosto (ricavo 25029.60 €/giorno/proprietà) e il minimo di gennaio (6149.95)
differiscono di ~4×: il calendario prezzi è la leva di domanda più evidente.

## 4. Lead-time e cancellazioni

Cancellazioni per bucket di lead-time (tutte le righe post-dedup):

| Bucket (giorni) | Prenotazioni | Cancellate | Cancel rate | Lead medio |
|---|---:|---:|---:|---:|
| 0–7 | 18304 | 1543 | 0.0843 | 2.3 |
| 8–30 | 16340 | 4145 | 0.2537 | 17.8 |
| 31–90 | 22744 | 7280 | 0.3201 | 56.8 |
| 91–180 | 18243 | 6382 | 0.3498 | 131.7 |
| >180 | 11765 | 4675 | 0.3974 | 251.1 |

Correlazione lead-time ↔ cancellazione: **0.1848** (Pearson, associazione).

Lead-time per mese di arrivo (media / mediana, giorni): gennaio 34.5 / 12,
aprile 75.9 / 62, **luglio 112.0 / 103**, agosto 102.7 / 87, dicembre 59.0 / 30
(tabella completa 12 mesi nel JSON, `lead_time.by_month`). Per segmento:

| Segmento | Prenotazioni | Lead medio | Lead mediano |
|---|---:|---:|---:|
| Online TA | 51618 | 79.9 | 55.0 |
| Offline TA/TO | 13889 | 106.1 | 82.0 |
| Direct | 11804 | 48.8 | 15.0 |
| Groups | 4942 | 147.6 | 114.0 |
| Corporate | 4212 | 16.3 | 5.0 |
| Complementary | 702 | 13.6 | 3.0 |
| Aviation | 227 | 4.3 | 3.0 |
| Undefined | 2 | 1.5 | 1.5 |

**Lettura.** Il rischio di cancellazione cresce monotono col lead-time:
dall'8.43% sotto una settimana al 39.74% oltre 180 giorni (~4.7×). I mesi di
picco si prenotano con largo anticipo (luglio: mediana 103 giorni) e proprio
lì si concentra l'esposizione: Groups (media 147.6) e Offline TA/TO (106.1)
sono i segmenti a lead più lungo; Corporate e Aviation sono last-minute.

## 5. Canali (market_segment)

Quote e cancellazioni su tutte le righe; ricavo e ADR sulle valide.
`agent`/`company` sono ID numerici non mappati: **nessuna disaggregazione per
OTA con nome è possibile** (dizionario §3, openapi getKpiChannels).

| Segmento | Pren. | Share | Cancel rate | Ricavo (€) | Share ricavo | ADR (€) |
|---|---:|---:|---:|---:|---:|---:|
| Online TA | 51618 | 0.5906 | 0.3535 | 12973686.94 | 0.5646 | 116.31 |
| Offline TA/TO | 13889 | 0.1589 | 0.1485 | 4595718.77 | 0.2000 | 82.33 |
| Direct | 11804 | 0.1351 | 0.1472 | 3927104.69 | 0.1709 | 126.96 |
| Groups | 4942 | 0.0565 | 0.2701 | 922928.01 | 0.0402 | 75.77 |
| Corporate | 4212 | 0.0482 | 0.1211 | 483748.83 | 0.0211 | 67.90 |
| Complementary | 702 | 0.0080 | 0.1254 | 4804.53 | 0.0002 | 33.60 |
| Aviation | 227 | 0.0026 | 0.1982 | 68968.36 | 0.0030 | 102.63 |
| Undefined | 2 | 0.0000 | 1.0000 | 0.00 | 0.0000 | — |

**Lettura.** Online TA domina (59.06% delle prenotazioni, 56.46% del ricavo)
ma cancella al 35.35%: oltre una prenotazione su tre di questo canale non si
realizza. Direct ha l'ADR più alto (126.96 €) e cancellazione bassa (14.72%):
il 13.51% delle prenotazioni produce il 17.09% del ricavo. Offline TA/TO
cancella poco (14.85%) ma a basso ADR (82.33 €); Groups paga 75.77 € e cancella
al 27.01%.

## 6. ADR vs occupazione — associazione, non causalità

Sui giorni di soggiorno (ADR realizzato = revenue/room-nights del giorno):

- Correlazione giornaliera ADR ↔ occupazione: **0.5535** (806 giorni, 0 a zero).
- Correlazione mensile (ADR pooled arrivi vs occupazione media stay-day):
  combined **0.6898**, Lago **0.7620**, Montagna **0.6266**.
- Per segmento (ADR mensile del segmento vs occupazione combined): Online TA
  0.7656, Corporate 0.7334, Direct 0.6714, Offline TA/TO 0.6104, Aviation
  0.7411 (10 mesi), Groups −0.0179, Complementary −0.0787.

ADR realizzato per livello di occupazione giornaliera:

| Occupazione | Giorni | ADR medio (€) | Mediana (€) | p25 (€) | p75 (€) |
|---|---:|---:|---:|---:|---:|
| <0.40 | 102 | 73.28 | 63.66 | 58.90 | 73.27 |
| 0.40–0.59 | 174 | 86.66 | 76.02 | 69.87 | 93.58 |
| 0.60–0.79 | 328 | 97.74 | 94.40 | 81.79 | 107.04 |
| ≥0.80 | 202 | 128.55 | 124.13 | 111.32 | 151.56 |

**Lettura.** Nei giorni ad alta occupazione (≥0.80, 202 giorni) l'ADR
realizzato è 128.55 € contro 73.28 € nei giorni sotto 0.40: ~1.75×.
**Questo non prova che alzare i prezzi aumenti l'occupazione (né viceversa):**
la stagionalità muove entrambe le variabili (mesi di picco = alta occupazione
e alte tariffe). Nel dataset non c'è alcun esperimento di prezzo: nessuna
elasticità stimabile, nessuna raccomandazione causale. La correlazione mensile
mescola inoltre due basi diverse (coorti di arrivi per l'ADR, giorni di
soggiorno per l'occupazione); quella giornaliera è sulla stessa base.

## 7. Ospite ripetuto, deposito, tipo cliente

Cancellazioni per gruppo (tutte le righe post-dedup):

| Gruppo | Prenotazioni | Cancellate | Cancel rate |
|---|---:|---:|---:|
| Ospite ripetuto: no | 83981 | 23764 | 0.2830 |
| Ospite ripetuto: sì | 3415 | 261 | 0.0764 |
| Deposito: No Deposit | 86251 | 23016 | 0.2668 |
| Deposito: Non Refund | 1038 | 983 | 0.9470 |
| Deposito: Refundable | 107 | 26 | 0.2430 |
| Cliente: Contract | 3139 | 512 | 0.1631 |
| Cliente: Group | 544 | 54 | 0.0993 |
| Cliente: Transient | 71986 | 21672 | 0.3011 |
| Cliente: Transient-Party | 11727 | 1787 | 0.1524 |

**Lettura.** Gli ospiti ripetuti (solo il 3.91% delle righe) cancellano al
7.64% contro 28.30% dei nuovi: ~3.7× meno. I tipi cliente contrattualizzati
(Group 9.93%, Transient-Party 15.24%, Contract 16.31%) cancellano molto meno
del Transient puro (30.11%). **Anomalia da non leggere come causalità:** il
94.70% di cancellazioni su Non Refund (1038 righe) è un'associazione estrema,
verosimilmente un effetto di selezione (politiche applicate a coorti già a
rischio o artefatti del dataset); Refundable ha n=107, troppo piccolo per
conclusioni. Nessuna modifica delle politiche di deposito va basata su questi
due numeri senza indagine.

## 8. Decisioni su prezzi e domanda supportate dai dati

Quattro decisioni concrete che l'analisi supporta, con i numeri che le
giustificano. Sono indicazioni osservazionali sul dataset 2015–17 (non Buby,
Assunzione 1): il cliente le valida sul proprio contesto; nessuna è una
prescrizione causale.

1. **Calendiere prezzi differenziato per struttura e stagione.** Lago:
   spingere giugno–agosto (occupazione 0.8853 / 0.8691 / 0.9172, ADR fino a
   175.86 €) con tariffe alte e minimi di soggiorno; promuovere la bassa
   stagione invernale (gennaio 0.3902, ADR 49.99 €). Montagna: difendere
   inverno–primavera (febbraio 0.5616, maggio ADR 126.22 €) e riempire
   luglio–agosto (0.5597 / 0.6684) con offerte mirate. Il gradiente ADR per
   occupazione (73.28 € sotto 0.40 → 128.55 € sopra 0.80) è la base storica
   dello yield management: tariffe crescenti al crescere dell'occupazione
   attesa, mai una tariffa piatta annuale.
2. **Termini di cancellazione proporzionali al lead-time.** Il rischio passa
   da 0.0843 (0–7 giorni) a 0.3974 (>180): chiedere deposito o penali più
   stringenti sulle prenotazioni a lungo lead (Groups media 147.6 giorni,
   Offline TA/TO 106.1), soprattutto per arrivi di luglio–agosto (mediana
   103 / 87 giorni). Il 27.49% complessivo è il riferimento storico per
   qualunque politica di overbooking: non una previsione.
3. **Riequilibrio verso il diretto.** Direct: ADR 126.96 € (il più alto) e
   cancellazione 14.72%, contro Online TA 116.31 € / 35.35%; il diretto
   produce il 17.09% del ricavo dal 13.51% delle prenotazioni. Investire sul
   canale diretto e valutare il costo dei canali intermediati al netto delle
   cancellazioni. Nessuna ottimizzazione per OTA con nome: `agent`/`company`
   non mappati.
4. **Fedeltà come stabilizzatore di domanda.** I ripetuti cancellano al 7.64%
   contro 28.30% dei nuovi, ma sono solo il 3.91%: incentivi al ritorno
   (soprattutto sul Transient, 30.11% di cancellazioni) riducono l'esposizione.
   Per la bassa stagione, puntare ai segmenti a cancellazione contenuta
   (Group 9.93%, Transient-Party 15.24%, Contract 16.31%).

## 9. Limiti (da dichiarare al SAL 1)

- **Osservazionale, non causale.** Dataset portoghese 2015–17, non Buby
  (Assunzione 1): nessun esperimento di prezzo, nessuna elasticità, nessuna
  claims di causalità in questo memo. Le correlazioni sono associazioni.
- **Capacità assunta, non misurata** (Assunzione 3): 190/230/420 inferite dal
  picco osservato + margine; per costruzione l'occupazione non può superare
  100%. Presentarla come misurata è frode; qui è etichettata come assunzione.
- **Anni parziali → solo medie per mese dell'anno, mai totali grezzi.**
  Gennaio–giugno osservati solo 2016–17, ottobre–dicembre solo 2015–16
  (`days_observed`/`years_observed` per ogni punto nel JSON). I totali mensili
  grezzi ingannerebbero.
- **Nessun join con le recensioni (S4):** recensioni tutte 2012, prenotazioni
  2015–17, zero mesi in comune. La reputazione non entra in questa analisi
  della domanda; resta la comparazione a livello di proprietà.
- **Canali non disaggregabili per OTA con nome:** `agent`/`company` sono ID
  numerici non mappati (dizionario §3).
- **Filtri diversi per KPI e cancellazioni:** i KPI escludono cancellate,
  nights=0 e adr=0 (assunzione dichiarata: i soggiorni ad ADR zero sono fuori
  anche dall'occupazione); cancellazioni e lead-time usano tutte le righe
  post-dedup. Il typo ADR 5400.0 è su una riga cancellata: non entra mai nei
  KPI (Assunzione 5).
- **Non Refund 0.9470 (n=1038) e Refundable n=107:** associazione estrema /
  campione piccolo, verosimile selezione; nessuna conclusione di policy.
- **Basi miste nella correlazione mensile** ADR–occupazione (arrivi vs
  stay-day); ai bordi della finestra le due basi differiscono by design
  (dizionario §3 «Finestra e aggregazione»). La giornaliera è sulla stessa
  base.

## 10. Decisione sulla previsione — HA-14, SAL 1 (decide il cliente)

**La tensione è reale e va risolta col cliente, non tagliata in silenzio**
(audit R2 e §6): il delivery-plan §11 mette D16 (forecast) al cut-order #1
perché il brief definisce la modellazione predittiva «eventuale»; l'obiettivo
del Caso 1 però dice «Prevedere la domanda e supportare le decisioni sui
prezzi». Questo memo copre la metà analitica (domanda descrittiva + decisioni
sui prezzi). Per la metà previsionale il cliente sceglie al SAL 1
(2026-11-20) tra due opzioni; la decisione va archiviata nella riga HA-14
(chiusura solo umana, nessun agent la compila).

**Opzione A — D16 come stretch: baseline moving-average.**

- Cosa: media mobile sui `kpi_daily` per proprietà (il piano stretch chiede
  property × settimana, `docs/plan.md` §Stretch #6; D16 è «demand forecast
  baseline (moving average)», delivery-plan §2). Output: previsione di
  room-nights/ricavo/occupazione con backtest sul 2017 e errore misurato
  (MAE/MAPE). Nessuna dipendenza nuova (pandas già pinned), nessun cambio
  schema (output al momento della query, pattern S8).
- Stima: **≈1 giornata DA-3** per script + test + backtest con output
  JSON/memo; **+1–2 giornate** se esposto via API/dashboard, perché un nuovo
  endpoint richiede il protocollo contract-bump (nuovo ADR + bump
  `info.version` in `openapi.yaml`).
- Cosa dà: una risposta quantitativa e difendibile a «prevedere», con errore
  dichiarato. Cosa non dà: simulazione causale dei prezzi, elasticità,
  regressori esterni. Il backtest è limitato: 2017 parziale (gennaio →
  13 settembre nei giorni di soggiorno) e solo ~2 anni di storia.
- Condizione del piano: stretch solo se MVP verde entro il 4 dicembre
  (delivery-plan §11).

**Opzione B — waiver del cliente sulla metà previsionale.**

- Il cliente accetta questa analisi come risposta al Caso 1: stagionalità,
  lead-time e canali come base di pianificazione della domanda, decisioni sui
  prezzi supportate dai dati; nessun modello predittivo.
- Serve **waiver scritto del cliente al SAL 1**, archiviato in HA-14. Il
  taglio diventa esplicito e approvato, non silenzioso.
- Rischio da dichiarare: «prevedere» è nominato nell'obiettivo del caso; in
  sede di valutazione la metà previsionale potrebbe risultare scoperta
  (audit §6). Il waiver copre il team sul piano contrattuale, non elimina
  questo rischio.

**Nessuna delle due è decisa qui.** Il team prepara entrambe le opzioni;
la scelta è del cliente al SAL 1 e va registrata in HA-14.

---

Verifica: `data/tests/test_demand_analysis.py` (25 test su fixture + 1
integrazione DB che quadra la baseline dell'analisi con SQL indipendente;
con `CI=true` e DB spento il test DB fallisce, regola di casa). Il test
baseline sul CSV completo si salta in questo worktree by design (file
gitignored, solo drive del cliente); sul DB seedato completo la baseline è
asserita dallo script a ogni run: 87396 / 61777 / 218410 / 22976960.13 / 0.2749.
