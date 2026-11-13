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
| `ta_hotel_id` | bigint | **sì** | hotel TripAdvisor scelto da DA-2 (ADR 0003 §1). Unique. Nullo finché non viene scelto; si sceglie una volta e non si cambia dopo il SAL 1 |

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
`sentiment` e `topics` **non stanno qui**: sono output del modello (D14) e vanno
in una tabella derivata, così un re-run non deve fare `UPDATE` sulla sorgente.

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

### `guest_requests` — email generate (DA-3)

| Campo | Tipo | Null | Regola |
|---|---|---|---|
| `id` | serial PK | no | |
| `property_id` | integer FK | no | |
| `received_at` | timestamptz | no | |
| `body` | text | no | testo dell'email |
| `category` | varchar(50) | sì | 6 categorie: `availability`, `cancellation`, `complaint`, `special_request`, `billing`, `info` |
| `draft_reply` | text | sì | bozza prodotta dall'assistente |
| `status` | varchar(20) | no | `new`, `draft`, `sent` (CHECK), default `new` |

**Anti-leakage:** `true_category` e `true_urgency` vivono solo in
`data/eval/email_gold.csv`. Non vengono mai scritte nel database e mai lette
dalla pipeline. Se finiscono qui, la valutazione diventa una tautologia.

### `kpi_daily` — KPI per hotel e per giorno

Calcolata dalle prenotazioni non cancellate. Una sola riga per hotel e giorno
(unique).

| Campo | Tipo | Null | Regola |
|---|---|---|---|
| `id` | serial PK | no | |
| `property_id` | integer FK | no | |
| `date` | date | no | |
| `room_nights` | integer | no | notti vendute quel giorno |
| `revenue` | numeric(10,2) | no | `adr × nights`, sole non cancellate |
| `occupancy` | numeric(5,2) | no | `room_nights / room_count`. **Rapporto 0-1, senza ×100** (delivery-plan §6) |
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

---

## 4. Note sulla privacy

`country`, `agent` e `company` sono codici: nessun dato personale identificabile.
Le email degli ospiti sono generate, non reali. Le recensioni TripAdvisor sono
pubbliche. Nessun dato del cliente entra nel repository: i dataset completi
stanno sulla drive del cliente, in `data/raw/` solo il campione ridotto.
