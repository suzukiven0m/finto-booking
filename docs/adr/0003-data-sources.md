# ADR 0003 — Sorgenti dati per recensioni e testi

- **Stato:** Proposto (in attesa di voto del team)
- **Data:** 2026-11-09
- **Decisori:** 3 Web Solutions Architect + 3 Data Analyst / AI Specialist
- **Scadenza decisione:** 2026-11-20 (SAL 1) — lo schema si congela
- **Correlati:** `docs/plan.md`, `docs/delivery-plan.md`, `docs/adr/0001-tech-stack.md`, `docs/adr/0002-data-storage.md`

## Contesto

Il dataset disponibile, `Datasets/hotel_bookings.csv`, contiene 119.390 righe e 32 colonne di prenotazioni (2015-07 → 2017-08). È stato verificato colonna per colonna:

| Verifica | Risultato |
|---|---|
| Colonne recensione / rating / punteggio | **0 su 32** |
| Colonne testo libero | **0** (tutti i campi sono numerici, date o codici chiusi) |
| Colonna capacità / inventario camere | **0** |
| Proprietà distinte | 2 (`City Hotel`, `Resort Hotel`) |

Il brief richiede esplicitamente:

- una **dashboard reputazione**: punteggio medio, volume, trend del sentiment, **punteggio per dimensione**;
- **almeno una componente** di elaborazione di testi o email (classificazione, estrazione, sintesi).

Nessuna delle due ha una sorgente dati. Sono 2 dei 5 item MVP. `docs/plan.md` non segnala il problema.

## Il vincolo che nessuna opzione elimina

Non esiste una sorgente pubblica che contenga **contemporaneamente** volumi reali di prenotazioni e recensioni reali collegate alle stesse prenotazioni. Ogni opzione accetta un compromesso. La scelta non è "quale dataset è migliore", ma **quale compromesso è più difendibile davanti al cliente**.

## Opzioni considerate

### A. Solo dati sintetici

Generare 20.000 recensioni con punteggio e testo derivati dalle colonne reali delle prenotazioni (vedi `docs/delivery-plan.md` §1 B3).

- Copre tutto: reputazione, testo, legame con le prenotazioni.
- Nessun dato reale. Il punteggio è inventato, quindi l'analisi dei fattori di soddisfazione misura il generatore, non il mondo.

### B. Solo Booking.com RecTour 2024

`bookingcom/ml-dataset-reviews` — 1,6 M recensioni, 40.000 strutture, licenza CC BY-SA 4.0 (non commerciale).

Campi: `guest_score`, `review_positive`, `review_negative`, `room_nights`, `month`, `guest_type`, `accommodation_id`, `accommodation_type`, `accommodation_score`, `accommodation_star_rating`, `location_is_beach`, `location_is_ski`, `location_is_city_center`.

- Testo reale, punteggio reale, contesto di prenotazione reale.
- `location_is_ski` e `location_is_beach` corrispondono letteralmente a "lago e montagna".
- Nessun punteggio per dimensione. Nessun volume di prenotazioni → gli item KPI restano sul dataset attuale.

### C. Solo TripAdvisor (jniimi, derivato da Li et al. 2013)

1,5 M recensioni in inglese, 952 MB. Licenza del repository Apache 2.0; il dataset originale è accademico.

Campi: `hotel_id`, `overall`, **`cleanliness`, `value`, `location`, `rooms`, `sleep_quality`**, `title`, `text`, `stay_year`, `post_date`, `lang`.

- Unica opzione con **punteggio per dimensione reale**: soddisfa il brief senza sintesi.
- Nessun dato di prenotazione.

### D. `hotel_bookings.csv` + RecTour

Prenotazioni reali per occupazione e ricavi; RecTour per reputazione e testo. Legame a livello di proprietà.

- Tutto reale.
- Manca il punteggio per dimensione.

### E. `hotel_bookings.csv` + TripAdvisor ← **raccomandata**

Prenotazioni reali per occupazione e ricavi; TripAdvisor per reputazione e testo. Legame a livello di proprietà.

- Tutto reale.
- Punteggio per dimensione nativo: nessuna sintesi, nessuna giustificazione.
- Il legame tra prenotazione e recensione è **asserito**, non fattuale (vedi §"Punto debole").

### F. Ridurre lo scope

Eliminare dashboard reputazione e componente NLP.

- Zero rischio tecnico.
- Fallisce due requisiti obbligatori del brief. **Da respingere.**

## Valutazione

Punteggi 1-5. I pesi riflettono i criteri di valutazione del brief.

| Criterio | Peso | A. Sintetico | B. RecTour | C. TripAdvisor | D. Book+RecTour | E. Book+TripAdvisor | F. Ridurre |
|---|---:|---:|---:|---:|---:|---:|---:|
| Copertura dei requisiti del brief | 30% | 5 | 3 | 4 | 4 | 5 | 1 |
| Aderenza a "dati reali" | 20% | 1 | 4 | 4 | 4 | 4 | 5 |
| Sforzo e rischio entro il SAL 1 | 20% | 3 | 4 | 4 | 3 | 3 | 5 |
| Qualità dell'analisi (driver di reputazione) | 15% | 2 | 4 | 5 | 4 | 5 | 1 |
| Licenza / etica | 10% | 5 | 5 | 4 | 5 | 4 | 5 |
| Valore per la valutazione | 5% | 2 | 4 | 4 | 4 | 5 | 1 |
| **Punteggio ponderato** | **100%** | **3,20** | **3,80** | **4,15** | **3,90** | **4,30** | **3,00** |

## Raccomandazione

**Opzione E — `hotel_bookings.csv` + TripAdvisor.** Motivazioni:

- è l'unica opzione che copre **tutti** i requisiti del brief con dati reali;
- fornisce il punteggio per dimensione già pronto, che è la parte più difficile da sintetizzare in modo credibile;
- il legame a livello di proprietà è sufficiente: la dashboard reputazione aggrega per struttura e periodo, non per singola prenotazione;
- l'unica assunzione residua è la capacità camere, già inevitabile con qualunque opzione.

L'**opzione D** (RecTour) è la riserva se il download TripAdvisor non riesce: stesso impianto, si perde il punteggio per dimensione.

L'**opzione A** resta necessaria per le **email**, che nessuna sorgente pubblica fornisce.

## Punto debole della raccomandazione

Il legame prenotazione ↔ recensione è una **mappatura asserita**, non una chiave esterna reale. Un recensore TripAdvisor del 2012 non è l'ospite di una prenotazione del 2016.

Conseguenze da dichiarare nel data dictionary e al SAL 1:

- i KPI di occupazione e ricavi vengono **solo** da `hotel_bookings.csv`;
- i KPI di reputazione vengono **solo** da TripAdvisor;
- nessuna analisi congiunta a livello di singola prenotazione è lecita;
- un'analisi congiunta è lecita **a livello di proprietà e di mese**, con l'assunzione dichiarata.

Presentare il join come se fosse fattuale è l'unico modo per rendere questa opzione indifendibile.

## Decisione

> **Da completare con il voto del team il ______.**
>
> Opzione scelta: ______
>
> Voti: WSA ___ / Data ___
>
> Dissenso / condizioni: ______

## Conseguenze

**Positive**

- Reputazione e NLP su dati reali, senza generatore da difendere.
- Il punteggio per dimensione soddisfa il brief senza lavoro aggiuntivo.
- Se il cliente fornisce recensioni vere più avanti, si sostituisce il loader e il resto non cambia.

**Negative**

- Due dataset da caricare invece di uno.
- Il legame è asserito: va documentato e spiegato in demo.
- Le recensioni sono in inglese: per una demo in italiano serve un corpus aggiuntivo (ABSITA, 10.000 frasi annotate) oppure si accetta l'inglese.
- Licenza TripAdvisor: repository Apache 2.0, dataset originale accademico. Uso didattico ammesso; citare Li et al. (2013).

**Seguito**

- Se si sceglie B o D, registrare in un ADR successivo la perdita del punteggio per dimensione e come viene coperta.
- Se il cliente consegna recensioni reali, aprire un ADR di sostituzione prima di integrarle.

---

## Come procedere (se viene scelta E)

Sette passi, in ordine di dipendenza. Giorni lavorativi, weekend esclusi.

### 1. Tabella di mappatura proprietà — WSA-1 + DA-1, 11 nov

Due righe, nessuna logica.

```sql
CREATE TABLE properties (
  id            SERIAL PRIMARY KEY,
  name          TEXT NOT NULL,           -- 'Buby Lago', 'Buby Montagna'
  hotel_type    TEXT NOT NULL,           -- valore della colonna `hotel` nel CSV
  ta_hotel_id   BIGINT,                  -- hotel_id TripAdvisor
  room_count    INTEGER NOT NULL         -- assunzione, vedi delivery-plan §6
);
```

`ta_hotel_id` si sceglie prendendo, per ciascuna proprietà, l'hotel TripAdvisor con più recensioni. Va scelto **una volta** e non cambiato dopo il SAL 1.

### 2. Loader recensioni — DA-2, 12-13 nov

```bash
pip install huggingface_hub pandas
```

```python
from huggingface_hub import hf_hub_download
import pandas as pd

path = hf_hub_download(
    "jniimi/tripadvisor-review-rating",
    repo_type="dataset",
    filename="data.pkl",          # 952 MB — NON va nel repository
)
df = pd.read_pickle(path)
```

Regole:

- filtrare `lang == "__label__en"`;
- campionare **20.000** recensioni, bilanciate per `hotel_id`, `random_state=42`;
- scrivere `data/raw/tripadvisor_sample.csv` (~3 MB) e **committare quello**, non il pickle;
- per lo sviluppo veloce esiste `data1000.pkl` (1.000 righe), utile per provare il loader prima del download completo.

### 3. Schema recensioni — WSA-1, 12 nov

```sql
CREATE TABLE reviews (
  id             SERIAL PRIMARY KEY,
  property_id    INTEGER REFERENCES properties(id),
  ta_hotel_id    BIGINT NOT NULL,
  post_date      DATE NOT NULL,        -- da `post_date`, non `stay_year`
  stay_year      INTEGER,
  overall        NUMERIC(3,1),
  cleanliness    NUMERIC(3,1),
  value          NUMERIC(3,1),
  location       NUMERIC(3,1),
  rooms          NUMERIC(3,1),
  sleep_quality  NUMERIC(3,1),
  title          TEXT,
  body           TEXT,
  lang           TEXT
);
```

Nessuna chiave esterna verso `bookings`. Il legame è `property_id`, non la prenotazione.

### 4. Dashboard reputazione — WSA-2 + DA-2, 3 dic

- punteggio medio per proprietà;
- trend mensile su `post_date` (non `stay_year`: è solo l'anno);
- punteggio per dimensione: cinque assi, un grafico a barre;
- volume recensioni per mese.

### 5. NLP — DA-2, 3 dic

- sentiment sul `body` (modello multilingue preaddestrato, nessun training);
- topic multi-label (pulizia, personale, posizione, colazione, rumore, rapporto qualità-prezzo);
- sintesi mensile per proprietà.

Le cinque dimensioni e `overall` fungono da **etichetta debole** per valutare il sentiment: correlazione tra punteggio previsto e punteggio reale. È una valutazione onesta perché le etichette non sono state generate dal modello.

### 6. Email — DA-3, resta sintetico

800 email, 6 categorie (`availability`, `cancellation`, `complaint`, `special_request`, `billing`, `info`). Etichette esatte, tenute in `data/eval/email_gold.csv` e mai scritte nel database.

### 7. Divulgazione — lead, entro SAL 1

- data dictionary: due sorgenti, legame asserito, assunzione capacità;
- slide SAL 1: una riga esplicita sulle due sorgenti e sul tipo di legame;
- report finale: citazione Li et al. (2013) e licenza CC BY-SA 4.0 se si usa RecTour.
