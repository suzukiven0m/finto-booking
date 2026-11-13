# Review — PR #4 `feat/db-schema` (D2: schema v1 + migrazioni Alembic)

| | |
|---|---|
| PR | #4 `feat/db-schema` → `master` |
| Commit recensito | `65987f4` — "schema database v1 con migrazioni alembic (D2)" |
| Autore | WSA-1 (Ric) |
| Reviewer | WSA-3 (Facu) |
| Data | 2026-11-13 |
| Baseline | ADR 0001, ADR 0002, **ADR 0003 (accettato 2026-11-13, opzione E)**, `docs/plan.md`, `docs/delivery-plan.md`, brief |
| Verdetto | **Request changes** — 3 bloccanti, 6 da sistemare, 6 opzionali |

> **Stato al 2026-11-13 (dopo il merge di #4).** La PR è stata mergiata così com'era.
> Il seguito dei B-/T- è stato fatto sul branch `plumbing`: migrazione `0003`, ERD,
> dizionario dei dati, test, CI, dipendenze fissate. Dettaglio e verifica eseguita:
> `docs/reviews/plumbing-review.md`. Le righe della tabella §6 restano com'erano
> perché descrivono la PR al momento della review, non il branch successivo.

## 0. Verdetto

Il lavoro è **solido e funziona davvero**: le migrazioni salgono e scendono pulite, i modelli sono allineati alle migrazioni (`alembic check` non trova niente), i test passano, il SQL offline è valido. Su Alembic non c'è niente da correggere.

Il problema non è il codice, è **il momento**: la tabella `reviews` è stata congelata su una forma che il team ha respinto il 13 novembre, quando ADR 0003 è stato accettato all'unanimità sull'opzione E (TripAdvisor). Manca anche l'ERD che D2 richiede.

**Il PR non è mergiato, quindi non serve una migrazione correttiva**: si correggono `0001` e `0002` in place. Ogni giorno che passa questo lavoro costa di più, perché dopo il freeze del 20 novembre le stesse modifiche diventano migrazione + bump del contratto + rigenerazione del mock + tipi del frontend.

## 1. Cosa è giusto (non si tocca)

- **Migrazioni reversibili.** `upgrade head` → `downgrade base` → `upgrade head` è un round-trip pulito. `downgrade` droppa nell'ordine giusto.
- **Modelli ≡ migrazioni.** `alembic check` non rileva drift. È la base per metterlo in CI (O-4).
- **`bookings` rispetta le trappole di `delivery-plan` §0.** `reservation_status` non salvato, `arrival_date` composto da anno/mese/giorno, `week_number` derivato. Sono esattamente le tre cose che il piano segnala.
- **Mapping proprietà corretto.** `Buby Lago ← Resort Hotel` 190 camere, `Buby Montagna ← City Hotel` 230, come `delivery-plan` §0 e §6.
- **`nights` come colonna generata.** Buona scelta: il dato derivato non può divergere.
- **`agent`/`company` nullable** per il `NULL` del CSV. **`children`/`babies` con `server_default="0"`** per i 4 `NA`.
- **ADR 0002 rispettata.** Un solo motore, nessun Mongo, testo grezzo come `TEXT` semplice, niente `pgvector`/`tsvector` finché il RAG è stretch.
- **ADR 0001 rispettata.** SQLAlchemy 2 + Alembic, monorepo `/backend /frontend /data /infra /docs`.

## 2. Bloccante

### B-1 — `reviews` ha la forma sbagliata

`backend/alembic/versions/0002_reviews_requests_kpi.py` righe 15-28. Oggi:

```text
property_id, booking_id (FK → bookings), date, score, text,
language, reviewer_nationality, sentiment, topics
```

ADR 0003 §3 prescrive:

```sql
reviews(id, property_id, ta_hotel_id, post_date, stay_year,
        overall, cleanliness, value, location, rooms, sleep_quality,
        title, body, lang)
-- "Nessuna chiave esterna verso bookings. Il legame è property_id, non la prenotazione."
```

Quattro cose, in ordine di gravità:

1. **`booking_id` va tolto.** La FK alla prenotazione è ciò che l'ADR esclude: un recensore TripAdvisor del 2012 non è l'ospite di una prenotazione del 2016. Tenerla invita a un join che l'ADR dichiara illecito.
2. **Mancano `ta_hotel_id`, `post_date`, `stay_year`, `overall` e le cinque dimensioni.** Sono i due requisiti del brief (punteggio medio + punteggio per dimensione) e l'unica ragione per cui è stata scelta l'opzione E.
3. **Rinomina:** `date` → `post_date`, `text` → `body`, `score` → `overall`, `language` → `lang`. Sono i nomi del corpus: ora costano zero, dopo il freeze costano una migrazione e un loader da correggere.
4. **`sentiment` e `topics` non vanno nella tabella sorgente.** Sono output del modello (D14), non dati di TripAdvisor. Congelarli qui costringe il loader a lasciarli vuoti e il modello a fare `UPDATE` sulla tabella sorgente. Meglio una tabella derivata o una vista.

**`reviewer_nationality` non esiste nel corpus TripAdvisor.** O si toglie, o resta una colonna che nessun loader riempirà mai.

Target per `0002`:

```python
op.create_table(
    "reviews",
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("property_id", sa.Integer(), sa.ForeignKey("properties.id"), nullable=False),
    sa.Column("ta_hotel_id", sa.BigInteger(), nullable=False),
    sa.Column("post_date", sa.Date(), nullable=False),
    sa.Column("stay_year", sa.Integer()),
    sa.Column("overall", sa.Numeric(3, 1)),
    sa.Column("cleanliness", sa.Numeric(3, 1)),
    sa.Column("value", sa.Numeric(3, 1)),
    sa.Column("location", sa.Numeric(3, 1)),
    sa.Column("rooms", sa.Numeric(3, 1)),
    sa.Column("sleep_quality", sa.Numeric(3, 1)),
    sa.Column("title", sa.Text()),
    sa.Column("body", sa.Text()),
    sa.Column("lang", sa.String(20)),
)
# il trend mensile della dashboard reputazione filtra per hotel e data
op.create_index("ix_reviews_property_post_date", "reviews", ["property_id", "post_date"])
```

`property_id` **NOT NULL**: il loader filtra sui due `ta_hotel_id` scelti, quindi una recensione senza proprietà non deve entrare. `ta_hotel_id` resta denormalizzato apposta, per tracciabilità.

### B-2 — manca `properties.ta_hotel_id`

ADR 0003 §1 lo richiede per la tabella di mappatura proprietà. Oggi non c'è né in `0001` né in `models.py`.

```python
# 0001, dentro create_table("properties", ...)
sa.Column("ta_hotel_id", sa.BigInteger(), unique=True),
```

e i due `bulk_insert` lo portano a `None` finché DA-2 non sceglie l'hotel TripAdvisor con più recensioni per ciascuna proprietà. **La scelta va fatta una volta e non cambiata dopo il SAL 1** (ADR 0003 §1).

### B-3 — manca l'ERD, quindi D2 non è chiuso

`docs/delivery-plan.md` §2 definisce D2 come *"PostgreSQL schema v1 + Alembic migration"*, §4 come *"D2 schema v1 + **ERD**"*, e la checklist di freeze chiede *"ERD + migration merged"*. `docs/plan.md` SAL 1 DoD chiede *"PostgreSQL schema v1 (ERD + migrations)"*.

L'ERD non esiste (`find . -iname "*erd*"` → niente). Il posto più economico è un Mermaid dentro un `.md` in `docs/`, così si vede direttamente nella review.

## 3. Da sistemare prima del merge

### T-1 — i test si mettono in `skip` e in CI è un falso verde

`backend/tests/test_schema.py` righe 8-14: se il database non risponde, `pytest.skip`. Provato con una porta morta: **`5 skipped in 0.75s`**, `pytest` esce verde senza aver testato niente.

Fix minimo in un `conftest.py`: in CI il DB *deve* esserci, quindi si fallisce invece di saltare.

```python
import os
import pytest
from sqlalchemy.exc import OperationalError
from app.database import engine

@pytest.fixture(scope="session")
def conn():
    try:
        with engine.connect() as c:
            yield c
    except OperationalError:
        if os.getenv("CI"):
            pytest.fail("database non raggiungibile in CI")
        pytest.skip("db spento")
```

Collegato: `.github/workflows/ci.yml` non esiste ancora (WSA-3, 2.5). È il momento giusto per aggiungerlo con un service `postgres:16`, `alembic upgrade head`, `pytest`, `alembic check`.

### T-2 — indici mancanti sulle foreign key

Postgres non indicizza le FK da solo. L'unica coperta è `bookings.property_id` (dall'indice composito).

| Tabella | FK | Indice |
|---|---|---|
| `bookings` | `property_id` | ✅ `ix_bookings_property_arrival` |
| `kpi_daily` | `property_id` | ✅ `uq_kpi_daily_property_date` |
| `reviews` | `property_id` | ❌ (coperto da B-1) |
| `guest_requests` | `property_id` | ❌ |

Con 20k recensioni e 800 email le dashboard filtrano per hotel: senza indice sono seq-scan. Una riga ciascuno.

### T-3 — `nights` è generata: l'ETL non deve scriverla (handoff a DA-1)

`models.py` e `0001` la definiscono `Computed`. L'errore esatto se qualcuno la inserisce:

```text
ERROR: cannot insert a non-DEFAULT value into column "nights"
DETAIL: Column "nights" is a generated column.
```

Il seed D4 di Daniele **non deve elencare `nights`** nella `INSERT`/`COPY`. Va nel data dictionary.

### T-4 — l'unità di `occupancy` è già decisa dai documenti

`models.py` dice *"room_nights / room_count * 100 (da sentire con Daniele se va in % o 0-1)"*. Non serve chiedere: `delivery-plan` §6 la definisce `room_nights_sold / (ROOMS * days_in_period)`, cioè un rapporto **0-1 senza ×100**. Qui la tabella è giornaliera, quindi `room_nights / room_count`. Basta togliere il dubbio dal commento e scriverlo nel data dictionary. `Numeric(5,2)` va bene per entrambe, quindi non vincola.

### T-5 — dipendenze non pinnate

`backend/requirements.txt` usa solo `>=` e non c'è nessun pin di Python. Oggi funziona (verificato su 3.12 e 3.14), ma prima di CI e Docker una build non è riproducibile. Pinnare la combinazione testata (`sqlalchemy==2.1.8`, `alembic==1.20.1`, `psycopg[binary]==3.3.9`, `pytest==9.2.0`) o al minimo `~=`.

### T-6 — `DATABASE_URL` e `.env` possono divergere in silenzio

`app/config.py` legge solo `DATABASE_URL` con default `buby:buby@localhost:5432/buby`, che combaciano con `infra/docker-compose.yml`. Ma se qualcuno cambia `POSTGRES_USER` nel `.env`, compose cambia e il backend no: l'errore che si vede è "password authentication failed", non "hai due configurazioni". Vale una riga nel README: il contratto è *stessi valori di default, `DATABASE_URL` per sovrascrivere*.

## 4. Opzionale — da decidere insieme, nessuna blocca

| ID | Cosa | Nota |
|---|---|---|
| O-1 | Nessun `CHECK` sui vocabolari chiusi: `location_type` (lake/mountain), `status` (new/draft/sent), `category` | Un `CHECK` costa una riga e impedisce che l'ETL ci scriva spazzatura. Se non si fa, va nel data dictionary |
| O-2 | `properties.hotel_type` è `unique=True` | Diventa una seconda chiave naturale: vieta una terza struttura dello stesso tipo. Con 2 righe è innocuo, ma non è voluto |
| O-3 | `kpi_daily` ha `id` surrogato **e** `unique(property_id, date)` | Lo schetch di §4 la disegna con la chiave naturale, senza `id`. Solo coerenza |
| O-4 | `alembic check` in CI | Verificato che rileva il drift. Copre R4 a costo zero |
| O-5 | `backend/lavoro_svolto.md` | I documenti stanno in `docs/` (ADR 0001). Come guida per i compagni va benissimo, ma non in `backend/` |
| O-6 | `guest_requests.body` è testo libero | Schema a posto; la pseudonimizzazione va fatta in ingestione (O1 del delivery plan). Nessun PII nel repo |

Nota tecnica minore: `alembic/env.py` non imposta `compare_type` né `compare_server_default`. Con Alembic ≥1.12 `compare_type` è `True` di default, quindi il drift di tipo è rilevato; il drift di `server_default` no. Se interessa, una riga in `context.configure`.

## 5. Matrice di conformità — PR #4 contro ogni documento

Legenda: ✅ conforme · 🔴 bloccante · 🟡 da sistemare · 🔵 opzionale · ⚪ fuori scope di questo PR

| Documento | Requisito | PR #4 | |
|---|---|---|---|
| ADR 0001 | SQLAlchemy 2 + Alembic | sì | ✅ |
| ADR 0001 | Monorepo `/backend /frontend /data /infra /docs` | sì | ✅ |
| ADR 0001 | Pydantic v2 nella baseline | assente da `requirements.txt` | ⚪ D5/D12 |
| ADR 0001 | JWT, ruoli `admin`/`manager`/`property_manager` | assente | ⚪ D11, 27 nov |
| ADR 0001 | I documenti stanno in `/docs` | `lavoro_svolto.md` in `backend/` | 🔵 O-5 |
| ADR 0002 | Un solo motore, solo PostgreSQL | sì | ✅ |
| ADR 0002 | Testo grezzo come `TEXT` semplice | sì | ✅ |
| ADR 0002 | Niente `pgvector`/`tsvector` finché il RAG è stretch | sì | ✅ |
| ADR 0003 §1 | `properties.ta_hotel_id` | assente | 🔴 B-2 |
| ADR 0003 §3 | Forma di `reviews`, nessuna FK a `bookings` | forma sintetica | 🔴 B-1 |
| ADR 0003 §3 | `overall` + cinque dimensioni | assenti | 🔴 B-1 |
| ADR 0003 §3 | `sentiment`/`topics` fuori dalla tabella sorgente | presenti | 🔴 B-1 |
| ADR 0003 §6 | `guest_requests` sintetica, 6 categorie | tabella ok, nessun `CHECK` | 🔵 O-1 |
| `plan.md` MVP 1 | Schema + dati reali seedati | solo schema | ⚪ D4 (DA-1) |
| `plan.md` MVP 3 | Punteggio per dimensione | nessuna colonna | 🔴 B-1 |
| `plan.md` MVP 4 | Sentiment + topic multi-label | colonne nel posto sbagliato | 🔴 B-1 |
| `plan.md` SAL 1 DoD | ERD + migrazioni | manca l'ERD | 🔴 B-3 |
| `plan.md` SAL 1 DoD | Data dictionary v1 | assente | ⚪ non è questo PR |
| `delivery-plan` D2 | Schema v1 + migrazione Alembic | sì | ✅ |
| `delivery-plan` §0 | `Buby Lago ← Resort Hotel` 190, `Buby Montagna ← City Hotel` 230 | sì | ✅ |
| `delivery-plan` §0 | `reservation_status` non salvato | sì | ✅ |
| `delivery-plan` §0 | `arrival_date` composto, `week_number` derivato | sì | ✅ |
| `delivery-plan` §4 | Schetch dello schema | ora è la forma ADR 0003 | 🔴 B-1 |
| `delivery-plan` §6 | `occupancy` 0-1, senza ×100 | commento ambiguo | 🟡 T-4 |
| `delivery-plan` §10 R4 | Contract drift | `alembic check` funziona, non è in CI | 🟡 T-1 / 🔵 O-4 |
| `delivery-plan` §10 R5 | Baseline check come test | assente | ⚪ D4 |
| Brief | Contratto dati: schema + formato API + esempi | solo schema | ⚪ D5, 16 nov |
| Brief | Documentazione tecnica + istruzioni di installazione | `lavoro_svolto.md` | 🔵 O-5 |
| Brief | GDPR, anonimizzazione email | `body` libero, pseudonimizzazione in ingestione | 🔵 O-6 |
| Brief | "dati reali preparati dal team dati" | ADR 0003 E = dati reali | ✅ |

## 6. Il loop

Come funziona: io scrivo i punti con un ID, tu rispondi nella colonna tua, pushi, io rilancio la verifica e aggiorno lo stato. Solo `B-` e `T-` tengono aperto il merge.

**Stati:** 🔴 aperto · 🟡 in attesa di risposta · 🟢 chiuso e ri-verificato · 🔵 opzionale · ⚪ fuori scope

| ID | Chi | Stato | Ric dice | Facu risponde |
|---|---|---|---|---|
| B-1 `reviews` → forma ADR 0003 | Ric | 🔴 aperto | | Via `booking_id`, dentro `ta_hotel_id`/`post_date`/`stay_year`/`overall`/5 dimensioni, rinomina `date`→`post_date` `text`→`body` `score`→`overall` `language`→`lang`, fuori `sentiment`/`topics`/`reviewer_nationality`. Target in §2 |
| B-2 `properties.ta_hotel_id` | Ric | 🔴 aperto | | `BigInteger` unique, nullable finché DA-2 non sceglie l'hotel TripAdvisor |
| B-3 ERD | Ric | 🔴 aperto | | Mermaid in `docs/`, basta |
| T-1 `skip` in CI | Ric | 🟡 in attesa | | `conftest.py` con `pytest.fail` se `CI` è impostata |
| T-2 indici FK | Ric | 🟡 in attesa | | `reviews` coperto da B-1, resta `guest_requests.property_id` |
| T-3 `nights` → DA-1 | Ric → Daniele | 🟡 in attesa | | Handoff: il seed non deve elencare `nights` |
| T-4 unità `occupancy` | Ric | 🟡 in attesa | | 0-1 senza ×100, come `delivery-plan` §6 |
| T-5 pin dipendenze | Ric | 🟡 in attesa | | `==` o `~=` sulla combinazione testata |
| T-6 `DATABASE_URL`/`.env` | Ric | 🟡 in attesa | | Una riga nel README |
| O-1 … O-6 | tutti | 🔵 opzionali | | Si decidono insieme, nessuna blocca |

**Mergeable quando:** B-1, B-2, B-3 e T-1…T-6 sono 🟢, la ri-verifica è verde, e l'ERD è in `docs/`.

### Ri-verifica

```bash
bash personal-notes/rereview-pr4.sh            # verifica origin/feat/db-schema
bash personal-notes/rereview-pr4.sh feat/xyz   # verifica un altro branch
```

Alza un Postgres temporaneo, installa le dipendenze in un venv usa-e-getta, applica le migrazioni avanti e indietro, lancia `alembic check` e i test, stampa la matrice e pulisce tutto. Non tocca né il working copy né il database di sviluppo.

> **Nota del 2026-11-13:** la ri-verifica pomeridiana non è stata eseguita — in questo ambiente le porte pubblicate dai container non sono raggiungibili dall'host. I risultati citati sono quelli della verifica del mattino, eseguita sulla macchina dell'autore. **Vanno ri-confermati prima del merge.**

## 7. Versione corta da incollare nel PR

> Ciao Ric, review fatta — e l'ho provata davvero, non solo letta: Postgres 16 in container, `alembic upgrade head`, `downgrade base` e di nuovo `upgrade head`, `alembic check` e `pytest` (5 passed), su Python 3.12 e 3.14. **Le migrazioni sono corrette**: salgono e scendono pulite, i modelli sono allineati, il SQL offline funziona. Su Alembic non ho niente da correggere.
>
> Tre cose bloccano il freeze del 20:
>
> 1. **`reviews` ha la forma sbagliata.** ADR 0003 è stato accettato il 13/11 all'unanimità sull'opzione E, e la §3 dice esplicitamente "nessuna chiave esterna verso bookings" e vuole `ta_hotel_id`, `post_date`, `stay_year`, `overall` e le cinque dimensioni. La tabella ha `booking_id` → `bookings` e nessuna di quelle colonne. **Il PR non è mergiato, quindi non serve una `0003`: correggi `0001` e `0002` in place.** Il target esatto è in `docs/reviews/pr-4-schema-v1.md` §2.
> 2. **Serve `properties.ta_hotel_id`** (ADR 0003 §1).
> 3. **Manca l'ERD.** Il piano mette D2 come "schema v1 + ERD" e la checklist di freeze chiede "ERD + migration merged". Un Mermaid in `docs/` basta.
>
> Poi sei cose piccole, tutte in `docs/reviews/pr-4-schema-v1.md` §3: i test fanno `pytest.skip` se il DB è spento e in CI diventa **5 skipped in verde** (ci metto un `conftest.py` e il workflow, è il mio 2.5); le FK di `guest_requests` non hanno indice; `nights` è generata e il seed di Daniele non deve scriverla; `occupancy` non serve chiederla a Daniele, `delivery-plan` §6 la definisce già 0-1 senza ×100; le dipendenze non sono pinnate; `DATABASE_URL` e `.env` possono divergere in silenzio.
>
> Rispondi per ID nella tabella del §6 e rilancio la verifica.
