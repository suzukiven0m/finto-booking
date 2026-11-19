# Data dictionary — schema v1

Dizionario dei campi, regole di calcolo e assunzioni dichiarate. Sorgente delle
decisioni: ADR 0001, ADR 0002, ADR 0003, `docs/delivery-plan.md`. Struttura
delle tabelle: `docs/erd.md`. Il codice che deve rispettare questo documento è
`backend/app/models.py` + `backend/alembic/versions/`.

Regola generale: **ogni numero in dashboard deve avere qui la sua regola.** Se
un KPI non è in §3, non va pubblicato finché non ci finisce.

---

## 1. Origine dei dati — cosa è reale e cosa no

| Tabella | Fonte | Reale? | Da dichiarare |
|---|---|---|---|
| `bookings` | `hotel_bookings.csv` (Kaggle, Hotel Booking Demand) | sì | è un dataset portoghese 2015-2017, non Buby |
| `properties` | mappatura 1:1 dei due hotel del CSV | no | due strutture fittizie |
| `reviews` | corpus TripAdvisor (`jniimi/tripadvisor-review-rating`) | sì | legame per proprietà **asserito** |
| `guest_requests` | generatore sintetico (DA-3) | no | email generate, non reali |
| `kpi_daily` | calcolata da `bookings` | derivata | — |

> Il file arricchito a 34 colonne in `mock-db/` (25 testi di recensione distinti,
> email per riga) è **superato da ADR 0003 opzione E**: resta solo locale, non si
> committa e non si usa per nessun KPI. La deduplica corretta è sulle 32 colonne
> originali (Assunzione 4).

### Assunzione 1 — i due hotel sono fittizi

Il CSV contiene due tipi di struttura, non due hotel con nome:

- **Buby Lago** ← *Resort Hotel* (40.060 righe, cancel rate 27,76%)
- **Buby Montagna** ← *City Hotel* (79.330 righe, cancel rate 41,73%)

Nessun dato Buby reale. Va detto al SAL 1 e nella slide di apertura, non solo in
una nota a piè di pagina.

### Assunzione 2 — il legame recensioni ↔ prenotazioni è asserito

Una recensione TripAdvisor del 2012 non è l'ospite di una prenotazione del 2016.
Vincolante per il codice e per il SAL 1:

- i KPI di occupazione e ricavo vengono **solo** da `bookings`;
- i KPI di reputazione vengono **solo** da `reviews`;
- nessuna analisi congiunta a livello di singola prenotazione;
- l'analisi congiunta a livello di **proprietà e mese** è lecita, con l'assunzione
  dichiarata.

Presentare il join come un fatto è l'unico modo per rendere l'opzione E
indifendibile.

### Assunzione 3 — la capacità delle strutture è assunta

Il CSV non ha una colonna di camere. Senza denominatore occupazione e RevPAR
sono indefiniti. Costanti fisse, da pubblicare anche nella footnote della
dashboard:

```python
# data/kpi/constants.py
CITY_ROOMS = 230      # picco osservato di camere occupate (226) + margine
RESORT_ROOMS = 190    # picco osservato di camere occupate (187) + margine
```

L'auditor ha segnalato la circolarità: la capacità è inferita dal picco, quindi
l'occupazione non può superare il 100%. Accettabile **se etichettata come
assunzione**. È frode se presentata come misurata.

### Assunzione 4 — la deduplica

Le righe identiche su tutte le colonne originali vanno collassate **prima** di
qualsiasi KPI. La deduplica su 34 colonne dà numeri diversi da quella su 32
(che include le colonne aggiunte `review_text`/`guest_email`): 103,05 €/notte e
25,99 M€ invece di 105,20 €/notte e 22,98 M€. **Riferimento: deduplica sulle
colonne originali.**

### Assunzione 5 — pulizia del CSV (decisioni solo-dataset, 2026-11-16)

Regole applicate da `data/etl/load_bookings.py`, tutte riflesse nel baseline:

- **Deduplica sulle 32 colonne originali**, prima di aggiungere/rinominare colonne
  (mai dopo: è la trappola del file arricchito a 34 colonne).
- **NA di pandas default:** i letterali `NA` (4 in `children`) e `NULL`
  (`agent`/`company`/`country`) diventano NaN automaticamente; non si passa
  `keep_default_na=False`. `children`/`babies` NaN → 0.
- **`adults=0` si tengono** (385 post-dedup): il filtro baseline non li esclude;
  toglierli rompe il baseline.
- **Nessun clipping di `adr`:** il typo 5400,0 è su una riga `is_canceled=1`, non
  entra mai in un KPI; clippare o no dà lo stesso ricavo (verificato). `adr` si
  salva così com'è. Correzione a delivery-plan §10.
- `agent`/`company` NaN → NULL nel DB (non la stringa "nan").

---

## 2. Tabelle e campi

### `properties` — le due strutture

| Campo | Tipo | Null | Regola |
|---|---|---|---|
| `id` | serial PK | no | |
| `name` | varchar(100) | no | unique: `Buby Lago`, `Buby Montagna` |
| `hotel_type` | varchar(50) | no | valore della colonna `hotel` del CSV. **Non** unique: due strutture possono essere entrambe "City Hotel" |
| `location_type` | varchar(20) | no | `lake` o `mountain` (CHECK) |
| `room_count` | integer | no | capacità assunta (Assunzione 3), non misurata |
| `ta_hotel_id` | bigint | **sì** | hotel TripAdvisor (ADR 0003 §1). Unique. Scelto una volta, immutabile dopo il SAL 1: vedi «Decisione TripAdvisor» |

### `bookings` — una riga del CSV, non cancellata o cancellata

Nomi delle colonne allineati al CSV. `arrival_date` è la fusione di
anno/mese/giorno. `week_number` e `reservation_status` non sono salvati: si
ricavano.

| Campo | Tipo | Null | Regola |
|---|---|---|---|
| `id` | serial PK | no | |
| `property_id` | integer FK | no | da `hotel` (Resort → Buby Lago, City → Buby Montagna) |
| `arrival_date` | date | no | anno + mese + giorno del CSV |
| `lead_time` | integer | no | |
| `stays_in_weekend_nights` | integer | no | |
| `stays_in_week_nights` | integer | no | |
| `nights` | integer GENERATED | — | `stays_in_weekend_nights + stays_in_week_nights`, calcolata da Postgres. **Non va scritta nel loader** |
| `adults`, `children`, `babies` | integer | no | `children` e `babies` hanno `server_default 0` (4 NA nel CSV) |
| `country` | varchar(3) | sì | |
| `customer_type` | varchar(30) | no | |
| `is_repeated_guest` | boolean | no | |
| `previous_cancellations` | integer | no | |
| `previous_bookings_not_canceled` | integer | no | |
| `market_segment` | varchar(30) | no | 8 valori, usato per la channel mix |
| `distribution_channel` | varchar(30) | no | |
| `agent` | integer | sì | ID OTA **non mappato**: nel CSV c'è "NULL", va salvato vuoto |
| `company` | integer | sì | ID azienda non mappato, idem |
| `meal` | varchar(20) | no | |
| `reserved_room_type` | varchar(5) | no | tipo camera prenotato |
| `assigned_room_type` | varchar(5) | no | tipo camera assegnato |
| `deposit_type` | varchar(20) | no | |
| `booking_changes` | integer | no | |
| `days_in_waiting_list` | integer | no | |
| `required_car_parking_spaces` | integer | no | |
| `total_of_special_requests` | integer | no | |
| `adr` | numeric(8,2) | no | ricavo medio per notte |
| `is_canceled` | boolean | no | |
| `reservation_status_date` | date | no | |

### `reviews` — corpus TripAdvisor (ADR 0003 §3)

Nessuna FK verso `bookings`. Il legame è `property_id`, asserito (Assunzione 2).
`sentiment` e `topics` **non stanno qui**: sono output del modello (D14) e in v1
si calcolano **al momento della query** (decisione pre-freeze 2026-11-19, sotto):
niente tabelle derivate, così un re-run del modello non deve fare `UPDATE` sulla
sorgente.

| Campo | Tipo | Null | Regola |
|---|---|---|---|
| `id` | serial PK | no | |
| `property_id` | integer FK | no | proprietà mappata. ADR §3 non mette NOT NULL; qui è obbligatorio perché una recensione senza proprietà non è collegabile a nessun KPI |
| `ta_hotel_id` | bigint | no | denormalizzato: traccia da quale hotel TripAdvisor arriva la riga |
| `post_date` | date | no | da `post_date` del corpus, non da `stay_year` |
| `stay_year` | integer | sì | solo l'anno: non basta per il trend mensile |
| `overall` | numeric(3,1) | sì | voto 1-5 con un decimale |
| `cleanliness`, `value`, `location`, `rooms`, `sleep_quality` | numeric(3,1) | sì | le cinque dimensioni, reali dal corpus |
| `title` | text | sì | |
| `body` | text | sì | testo della recensione: input dell'NLP |
| `lang` | varchar(20) | sì | ADR §3 dice `TEXT`; qui è `varchar(20)` perché i valori del corpus sono etichette `__label__xx` (max 12 caratteri). Se arriva un corpus con codici più lunghi, va allargato con una migrazione |

### Decisione TripAdvisor — mapping scelto (ADR 0003 §1, 2026-11-16)

I due `ta_hotel_id` sono scelti e **immutabili dopo il SAL 1**:

| Proprietà | `ta_hotel_id` (offering_id) | Recensioni | `overall` medio |
|---|---:|---:|---:|
| Buby Lago (1) | 93618 | 762 | 3,86 |
| Buby Montagna (2) | 2079052 | 876 | 4,40 |

- **Regola di assegnazione (deterministica):** la struttura con più recensioni →
  Buby Montagna (2), la seconda → Buby Lago (1). Il legame è **asserito**, non
  fattuale (Assunzione 2).
- **Correzione ad ADR 0003 / playbook §1:** nella distribuzione HF
  `jniimi/tripadvisor-review-rating` la colonna `hotel_id` è in realtà l'id della
  **recensione** (201.295 valori distinti su 201.295 righe), non dell'hotel. Il vero
  id hotel (`offering_id`) si recupera da `review.txt` (Li et al. 2013) unendo su
  `id`: risolve il 100% delle righe. Senza questo passo il mapping sarebbe impossibile.
- **N reale = 1.638, non 20k:** le due strutture più recensite hanno 762 e 876
  recensioni. Si prendono tutte (playbook §5.2: sotto 10k si prende tutto e si fissa
  l'N reale). Campione committato: `data/raw/sample_tripadvisor.csv` (~1,6 MB, non
  ~16 MB come stimato in ADR 0003).
- **Corpus solo inglese:** tutte le 1.638 recensioni sono `__label__en`. Decisione:
  si accetta l'inglese per la reputazione, la demo email resta italiana; niente
  ABSITA per ora (ADR 0003 nomina entrambe le opzioni). Da dichiarare al SAL 1.
- `review_id` (id recensione HF) è conservato solo nella CSV campione, non nel DB:
  serve a ricostruire il mapping, non è un campo dello schema.

### `guest_requests` — email generate (DA-3)

| Campo | Tipo | Null | Regola |
|---|---|---|---|
| `id` | serial PK | no | |
| `property_id` | integer FK | no | |
| `received_at` | timestamptz | no | |
| `body` | text | no | testo dell'email |
| `category` | varchar(50) | sì | 6 categorie: `availability`, `cancellation`, `complaint`, `special_request`, `billing`, `info` |
| `urgency` | varchar(10) | sì | `low`, `medium`, `high` (CHECK, migrazione 0005). NULL finché D15 non la produce, come `category`/`draft_reply` |
| `draft_reply` | text | sì | bozza prodotta dall'assistente |
| `status` | varchar(20) | no | `new`, `draft`, `sent` (CHECK), default `new` |

**Anti-leakage:** `true_category` e `true_urgency` vivono solo in
`data/eval/email_gold.csv`. Non vengono mai scritte nel database e mai lette
dalla pipeline. Se finiscono qui, la valutazione diventa una tautologia.
La colonna `urgency` (0005) è l'output **predetto** da D15, non l'etichetta gold:
la regola anti-leakage vale anche per lei.

**Generatore (`data/etl/gen_emails.py`, seed 42):** 800 email italiane, 6 categorie
(134/133/133/133/133/134), ≥8 template per categoria × slot (nomi, date, camere,
proprietà, registro): i quasi-duplicati sono rari. È la lezione del postmortem
2026-11-11 sul dataset arricchito, dove 25 testi distinti rendevano la valutazione
una lookup table al 100%. Nomi/indirizzi inventati (GDPR, O1). Il DB riceve solo
`property_id, received_at, body`; `category`/`urgency`/`draft_reply` restano NULL
(output D15).
Gli id del gold combaciano con `guest_requests.id` perché entrambi partono da
TRUNCATE RESTART IDENTITY nello stesso run: se ricarichi le email, rigenera il gold.

### Decisioni pre-freeze 2026-11-19 — auth e output NLP (audit S7/S8)

Fissate il giorno prima del freeze (SAL 1, 2026-11-20). Sorgente: audit
`docs/reviews/2026-11-19-shepherd-audit.md` §3; seguito anche in ADR 0001.

- **S7 — niente tabella `users` in v1.** Lo schema congelato ha 5 tabelle,
  nessuna per gli utenti. Gli utenti demo saranno hardcoded in
  `backend/app/config.py` al momento di D11, con i 3 ruoli di ADR 0001:
  `admin`, `manager`, `property_manager`. L'emissione dei JWT è D11: qui si
  fissa solo la decisione di schema, l'autenticazione non è implementata. Una
  tabella `users` vera più avanti richiede il protocollo di contract-bump:
  nuovo ADR + bump di `info.version` in `openapi.yaml` + migrazione dedicata.
- **S8 — output NLP al momento della query.** Sentiment, topics e sintesi delle
  recensioni (D14) si calcoleranno quando la query li chiede: nessuna tabella
  derivata in v1, nessun `UPDATE` sulla sorgente a ogni re-run del modello
  (delivery-plan §4 lo consente esplicitamente). Persistere gli output in
  tabelle dedicate più avanti = stesso protocollo di contract-bump: nuovo ADR +
  bump di `info.version` + migrazione. L'urgenza delle email ha invece la sua
  colonna `guest_requests.urgency` (migrazione 0005, sopra): il gold file valuta
  `true_urgency`, quindi all'output serve una casa nello schema prima del
  freeze. Resta NULL finché D15 non la produce.

### `kpi_daily` — KPI per hotel e per giorno

Regola di calcolo fissata (playbook solo-dataset §4.1, 2026-11-16 — chiude P1-2).
`kpi_daily` conta i **giorni di soggiorno** delle prenotazioni con `is_canceled=0
AND nights>0 AND adr>0` (stesso filtro della baseline; i soggiorni ad ADR zero sono
esclusi anche dall'occupazione — assunzione dichiarata). Per ognuna, ogni giorno
`arrival_date … arrival_date+nights-1` contribuisce 1 room-night e `adr` di ricavo.
Una sola riga per hotel e giorno (unique), per ogni giorno dell'intervallo osservato
della proprietà, inclusi i giorni a zero. **Invariante:** sul dataset completo
`Σ kpi_daily.revenue = 22.976.960,13 €` e `Σ room_nights = 218.410`
(test: `data/tests/test_kpi_daily.py`).

| Campo | Tipo | Null | Regola |
|---|---|---|---|
| `id` | serial PK | no | |
| `property_id` | integer FK | no | |
| `date` | date | no | |
| `room_nights` | integer | no | notti vendute quel giorno |
| `revenue` | numeric(10,2) | no | Σ `adr` delle camere occupate quel giorno (regola sopra), non `adr × nights` concentrato sull'arrivo |
| `occupancy` | numeric(5,4) | no | `room_nights / room_count`. **Rapporto 0-1, senza ×100** (delivery-plan §6). 4 decimali: migrazione 0004 (con 2 si quantizzava a 1 punto percentuale) |
| `adr` | numeric(8,2) | sì | `revenue / room_nights`, vuoto se quel giorno non c'era nessuno |
| `revenue_per_available_room` | numeric(8,2) | no | `revenue / room_count` |

---

## 3. Definizioni dei KPI — da fissare prima di scrivere query

L'auditor ha mostrato che la stessa metrica oscilla del 10-40% solo cambiando la
definizione. Queste sono le regole vincolanti.

| KPI | Regola | Trappola |
|---|---|---|
| Cancellation rate | solo cancellate, dopo deduplica. **No-Show riportato a parte** | 37,04% raw vs 27,49% dedup vs 27,98% se si fonde il No-Show |
| ADR | revenue / room-nights, solo `adr > 0`. Riportare anche la mediana | media 101,83 distorta da un typo 5400.0 e 1.959 zeri |
| Revenue | `adr × nights`, solo non cancellate | 42,72 M lordo vs 25,996 M realizzato vs 22,98 M realizzato + dedup |
| Seasonality | medie **per mese dell'anno**, mai totali mensili grezzi | 2015 e 2017 sono anni parziali: i totali grezzi ingannano |
| Channel mix | per `market_segment` (8 valori) | `agent`/`company` sono ID numerici non mappati: nessuna disaggregazione per OTA con nome |
| Occupancy / RevPAR | contro la capacità assunta (§1, Assunzione 3) | **mai** presentata come misurata |

### Finestra e aggregazione — riepilogo vs giornaliero (audit 2026-11-19, S1/S2/S3)

Regole fissate anche nel contratto (`openapi.yaml`: getKpiSummary, getKpiDaily,
getKpiSeasonality):

- **`occupancy_avg` (riepilogo)**: formula pooled
  `Σroom_nights / (Σroom_count × giorni della finestra)`, **non** la media dei
  rapporti giornalieri. I giorni della finestra sono le date distinte richieste
  (793 sulla finestra completa di default); `Σroom_count` è 190 o 230 per
  proprietà, 420 per entrambe. Esempio fissato: 218.410 / (420 × 793) = 0,6558
  (la media dei rapporti giornalieri darebbe 0,6534: definizione da non usare).
- **Riepilogo = coorte di arrivi**: filtra `bookings.arrival_date` in
  `[date_from, date_to]`, estremi inclusi. Un soggiorno che arriva nella finestra
  contribuisce con tutte le sue notti, anche quelle oltre `date_to`.
- **Giornaliero = giorni di soggiorno**: legge `kpi_daily.date`;
  `date_from`/`date_to` filtrano la data di soggiorno, non l'arrivo.
- Ai bordi dell'intervallo i totali **differiscono per progetto**: con la finestra
  di default, 19 giorni di soggiorno oltre il 2017-08-31 (723 room-nights,
  105.263,50 €) entrano nel riepilogo ma restano fuori dalla serie giornaliera.
  La baseline pulita qui sotto resta il riferimento del riepilogo sulla finestra
  completa.
- **Giornaliero con `property_id` omesso/null**: una sola riga per data, somma
  delle due proprietà (`room_nights` e `revenue` sommati); `occupancy` e
  `revenue_per_available_room` contro la capacità combinata di 420 camere;
  `adr` = revenue sommato / room_nights sommati, null quando sono zero.
- **Stagionalità — `avg_adr`**: ADR pooled `Σ(adr × nights) / Σnights` sulle
  prenotazioni valide (stesso filtro della baseline) con `arrival_date` nel mese
  dell'anno, **non** media semplice degli `adr` di riga.
- **Stagionalità con `property_id` omesso/null**: `room_nights` e `revenue`
  giornalieri sommati sulle due proprietà per data (come nel giornaliero);
  `avg_occupancy` contro la capacità combinata di 420 camere; `avg_revenue`
  = media del revenue giornaliero sommato divisa per 2 (media per proprietà).

### Baseline pulita — il seed script deve riprodurre questi numeri

Dopo deduplica esatta (87.396 righe) e filtro `is_canceled=0, nights>0, adr>0`:

| Metrica | Valore |
|---|---:|
| Prenotazioni valide | 61.777 |
| Room-nights | 218.410 |
| Ricavo realizzato | 22.976.960,13 € |
| ADR | 105,20 € |
| Cancellation (post-dedup) | 27,49% |

Qualsiasi endpoint KPI che non restituisce questi numeri è sbagliato.

**Campione committato** (`data/raw/sample_hotel_bookings.csv`, 5.000 righe dedup,
`random_state=42`) — è quello che gira in CI (`data/tests/test_baseline.py`):

| Metrica | Valore |
|---|---:|
| Righe | 5.000 |
| Prenotazioni valide | 3.564 |
| Room-nights | 12.696 |
| Ricavo | 1.350.503,84 € |
| Cancellation rate | 0,2696 |

Il CSV completo (119.390 righe lorde) resta solo locale/drive del cliente: il suo
test si salta in CI, ma il test sul campione gira sempre (niente falso verde, T-1).

---

## 4. Note sulla privacy

`country`, `agent` e `company` sono codici: nessun dato personale identificabile.
Le email degli ospiti sono generate, non reali. Le recensioni TripAdvisor sono
pubbliche. Nessun dato del cliente entra nel repository: i dataset completi
stanno sulla drive del cliente, in `data/raw/` solo il campione ridotto.
