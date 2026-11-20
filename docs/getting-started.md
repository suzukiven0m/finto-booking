# Guida per iniziare

Questa guida porta da zero a un'applicazione funzionante sul tuo computer.
Ogni passaggio spiega prima cosa stai facendo e perché, poi il comando.
Se non hai mai usato Docker, un database o un'API, qui trovi le spiegazioni
minime per capire cosa succede. Per il quadro generale del progetto leggi
prima il [README](../README.md).

## 1. Cosa ti serve e perché

| Strumento | A cosa serve nel progetto |
|---|---|
| Docker con Compose | accende il database PostgreSQL (e, se vuoi, anche API e web) senza installare nulla a mano |
| Python 3.12 | esegue gli script dati (ETL), le migrazioni del database e l'API FastAPI |
| Node.js 22 + npm | esegue la dashboard React in sviluppo e ne costruisce la versione finale |
| git | scarica il repository e gestisce le modifiche |

Un database è un archivio strutturato di tabelle. PostgreSQL è il database che
usiamo. Docker lo impacchetta in un "container", cioè un processo isolato che
si accende e si spegne con un comando, senza sporcare il sistema.

## 2. Scarica il progetto

```bash
git clone <repo-url>
cd finto-booking
```

Dentro trovi `backend/` (API e database), `frontend/` (dashboard), `data/`
(script di pulizia e analisi), `infra/` (Docker), `docs/` (documentazione).

## 3. Concetti minimi (due minuti)

- **Schema**: la forma delle tabelle (colonne, tipi, vincoli). Vive in
  `backend/alembic/versions/` come migrazioni, cioè passi numerati (0001-0005)
  che costruiscono lo schema un pezzo alla volta. `alembic upgrade head`
  applica tutti i passi mancanti.
- **Seed**: caricare i dati dentro le tabelle. Gli script in `data/etl/`
  leggono i CSV e scrivono nel database. Si può caricare il campione ridotto
  (committato nel repo) o il dataset completo (resta in locale/drive cliente).
- **API**: il punto di ingresso programmatico ai dati. La nostra è FastAPI,
  espone 11 operazioni sotto `/api/...` e risponde in JSON.
- **Contratto**: l'accordo scritto tra team dati e team web sul formato delle
  risposte. È `openapi.yaml`, congelato a `v1.0.0`. Il frontend e il backend
  devono rispettarlo: per questo esistono i contract test.
- **JWT**: il gettone che il server rilascia al login e che il client rimanda
  a ogni chiamata protetta. Dimostra chi sei e quale ruolo hai, senza rimandare
  la password ogni volta.
- **ETL**: extract, transform, load. Leggere i dati grezzi, pulirli, caricarli.
  Nel nostro caso include la deduplica sulle 32 colonne originali del CSV.

## 4. Strada A: tutto con Docker (consigliata per provare)

Questa strada accende tre servizi: `postgres` (database), `api` (FastAPI),
`web` (la dashboard servita da nginx, un piccolo server web che fa anche da
ponte verso l'API).

```bash
docker compose -f infra/docker-compose.yml up -d --build
docker compose -f infra/docker-compose.yml ps
```

Il primo comando costruisce le immagini e accende i servizi in background
(`-d`). Il secondo mostra lo stato: `postgres` deve risultare `healthy`.

- La dashboard è su http://localhost:8080.
- L'API è su http://localhost:8000 (raggiungibile anche direttamente).
- Il web server nginx serve la dashboard e gira le chiamate `/api/...`
  all'API: per il browser è tutto sulla stessa origine, niente configurazioni.

Le immagini contengono solo codice, niente dati. Schema e seed sono passi
manuali, così sai sempre cosa c'è nel database.

### 4.1 Applica lo schema

```bash
docker compose -f infra/docker-compose.yml exec api alembic upgrade head
```

`exec` esegue un comando dentro un container già acceso. Qui applica le
migrazioni 0001-0005: alla fine il database ha le 5 tabelle vuote
(`properties`, `bookings`, `reviews`, `guest_requests`, `kpi_daily`).

### 4.2 Prepara l'ambiente Python per il seed

Gli script di caricamento girano sul tuo computer (non dentro l'immagine API)
e raggiungono il database su `localhost:5432`. Serve un ambiente Python con
le dipendenze del progetto:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r ../data/requirements.txt
cd ..
```

Un `venv` è una cartella con un Python isolato: le librerie che installi lì
non toccano il resto del sistema. `requirements.txt` elenca le librerie con
versioni fissate, così tutti abbiamo lo stesso ambiente.

Nota: `data/requirements.txt` include torch e transformers (servono per
l'analisi NLP delle recensioni). Su Linux la versione CPU di torch si installa
dalla index dedicata: se `pip` si lamenta della versione, aggiungi
`--extra-index-url https://download.pytorch.org/whl/cpu`. Per il solo seed
queste librerie non vengono usate, ma installarle evita sorprese dopo.

### 4.3 Carica i dati di esempio

Dalla root del repository, con il venv attivo:

```bash
PYTHONPATH=backend python data/etl/load_bookings.py data/raw/sample_hotel_bookings.csv
PYTHONPATH=backend python data/etl/load_reviews.py
PYTHONPATH=backend python data/etl/gen_emails.py
PYTHONPATH=backend python data/etl/build_kpi_daily.py
PYTHONPATH=backend:data python data/etl/classify_emails.py --persist
```

Cosa fa ogni riga:

1. carica 5.000 prenotazioni di esempio (deduplicate, pulite);
2. carica le 1.638 recensioni TripAdvisor del campione committato;
3. genera le 800 email sintetiche (italiano, 6 categorie, nomi inventati);
4. calcola i KPI giornalieri (occupazione, ricavo, ADR per ogni giorno);
5. classifica le email e scrive categoria, urgenza e bozza di risposta,
   con stato `draft`. Senza questo passo la inbox è vuota di bozze.

`PYTHONPATH=backend` dice a Python dove trovare il pacchetto `app` (la
configurazione del database). Tutti i passi sono idempotenti: rilanciarli
non duplica i dati.

### 4.4 Accedi

Apri http://localhost:8080 e usa uno degli account demo (password `demo`
per tutti, sono default di sviluppo pubblicati, non segreti):

| Account | Ruolo | Cosa può fare |
|---|---|---|
| `admin@buby.travel` | admin | tutto, incluse le modifiche alle richieste ospiti |
| `manager@buby.travel` | manager | tutto, incluse le modifiche alle richieste ospiti |
| `property.manager@buby.travel` | property_manager | legge tutto, non può modificare le richieste ospiti (403) |

Con il campione vedi 3.564 prenotazioni valide e 1.350.503,84 euro di ricavo.
La reputazione mostra le recensioni del 2012 (il trend è etichettato "solo 2012").
La inbox mostra 800 bozze pronte per l'approvazione umana.

Per spegnere tutto:

```bash
docker compose -f infra/docker-compose.yml down
```

Aggiungi `-v` solo se vuoi cancellare anche il volume del database (i dati
caricati spariscono).

## 5. Strada B: sviluppo locale (per lavorare sul codice)

Qui Docker accende solo il database; API e frontend girano come processi
sul tuo computer, così puoi modificarli e ricaricarli al volo.

### 5.1 Database

```bash
docker compose -f infra/docker-compose.yml up -d postgres
```

Solo `postgres`: l'API la avvii tu al passo 5.3 sulla porta 8000, e se il
container `api` fosse acceso sulla stessa porta ci sarebbe un conflitto.

Stringa di connessione: `postgresql://buby:buby@localhost:5432/buby`.
Per cambiare utente, password, database o porta copia `.env.example` in
`infra/.env` (Compose legge il `.env` nella cartella del file compose,
non quello nella root).

### 5.2 Backend: ambiente e schema

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m pytest
```

Il backend legge `DATABASE_URL`; se non è impostata la costruisce dalle
variabili `POSTGRES_*` (gli stessi default del compose). Attenzione:
`docker compose` legge il file `.env`, il backend legge l'ambiente del
processo. Se personalizzi le credenziali, esporta le stesse variabili
anche nel terminale dove avvii il backend.

### 5.3 API

Con il database caricato (passi 4.2-4.3, identici):

```bash
cd backend
uvicorn app.main:app --port 8000
```

Uvicorn è il server che esegue l'app FastAPI. Lascialo acceso in un terminale.
Tutte le 11 operazioni del contratto sono live su http://localhost:8000.

### 5.4 Frontend

In un altro terminale:

```bash
cd frontend
npm install
npm run dev
```

Vite serve la dashboard su http://localhost:5173 e la ricarica a ogni modifica.
Il client punta di default a http://localhost:8000 (l'API vera). Puoi cambiare
bersaglio con la variabile `VITE_API_BASE_URL`.

`avvia.sh` (Mac/Linux) e `avvia.bat` (Windows) avviano database, API e frontend
con un comando solo, se preferisci.

## 6. Il dataset completo (opzionale)

Il CSV completo (119.390 righe lorde) non è nel repository: resta in locale o
sulla drive del cliente. Se ce l'hai, mettilo in `data/raw/hotel_bookings.csv`
e lancia `load_bookings.py` su quel file invece del campione, poi rigenera
KPI e classificazione. I numeri attesi cambiano: 61.777 prenotazioni valide,
218.410 room-night, 22.976.960,13 euro, ADR 105,20, cancellazioni 27,49%.
Procedura completa in [docs/playbooks/solo-dataset.md](playbooks/solo-dataset.md).

Se i tuoi numeri non tornano, il codice è sbagliato: il baseline è un'asserzione
verificata, non un obiettivo da aggiustare. Le regole sono nel
[dizionario dati](data-dictionary.md) §3.

## 7. Test: come si lanciano e cosa aspettarsi

I conteggi qui sotto si riferiscono al **dataset completo** caricato. Con il
solo campione, i test che confrontano il baseline completo saltano (è previsto
e dichiarato, non è un test nascosto).

| Suite | Comando (dalla root, venv attivo) | Atteso |
|---|---|---|
| Backend | `cd backend && python -m pytest` | 140 passed, 1 skipped |
| Data | `PYTHONPATH=backend:data python -m pytest data/tests` | 133 passed, 1 skipped |
| Frontend | `cd frontend && npm test -- --run` | 19 passed |
| Typecheck + build | `cd frontend && npm run typecheck && npm run build` | puliti |

Lo skip è previsto e onesto: un test confronta il baseline del campione e salta
se nel database c'è il dataset completo (e viceversa). Non è un test nascosto.

### 7.1 Se il database non è raggiungibile dal tuo computer

Su alcune macchine (inclusa quella del laboratorio, con VPN attiva) le
connessioni dal sistema host verso le porte pubblicate dai container sono
bloccate. `psql` e `pytest` verso `localhost:5432` falliscono, ma Docker
funziona. La soluzione è un container "sidecar" che condivide la rete di
Postgres: vede il database come se fosse locale, senza passare dalla porta
pubblicata. Il repository è montato in sola lettura, le scritture vanno al
database, non ai file.

```bash
docker run --rm -i --network container:buby-postgres \
  -v "$PWD":/repo:ro -w /repo/backend \
  -e PYTHONPATH=/repo/backend/.venv/lib/python3.12/site-packages:/repo/backend \
  -e PYTEST_ADDOPTS="-p no:cacheprovider" \
  python:3.12-slim sh -c "python -m alembic check && python -m pytest -q"
```

Per i test data si monta la root (`-w /repo`) e si aggiunge `/repo/data` al
`PYTHONPATH`, lanciando `python -m pytest data/tests`. Il baseline completo
richiede il CSV completo montato (`-v "$PWD/data/raw":/repo/data/raw:ro`),
altrimenti quel test salta (è il comportamento previsto).

## 8. Smoke E2E settimanale

Con il database caricato e l'API accesa, questo script percorre le stesse
chiamate che fa la dashboard e verifica i numeri:

```bash
cd backend
uvicorn app.main:app --port 8000 &
cd ..
python backend/tests/e2e_smoke.py
kill %1
```

Controlla login, baseline, recensioni, prenotazioni, inbox, una modifica
approvata e poi ripristinata (alla fine tutte le 800 email devono essere
in stato `draft`, nessuna `sent`), e il 401 senza gettone. In CI gira dopo
il seed del campione, con le assertion sul baseline del campione.

## 9. Mock Prism (solo per lavorare sul contratto)

Prism è un finto server che risponde con gli esempi scritti in `openapi.yaml`.
Serve per provare le forme delle risposte senza backend. **Non è il percorso
demo**: la demo gira sui dati reali.

```bash
cd frontend
VITE_API_BASE_URL=http://localhost:4010 npm run demo
```

## 10. Problemi comuni

| Sintomo | Causa probabile | Rimedio |
|---|---|---|
| `address already in use` sulla 8000 | il container `api` è acceso e anche uvicorn locale vuole la stessa porta | usa `up -d postgres` per la strada B, oppure spegni il container `api` |
| `connection refused` verso localhost:5432 | VPN/firewall blocca le porte pubblicate (sezione 7.1) | usa il sidecar |
| inbox senza bozze | manca il passo D15 | lancia `classify_emails.py --persist` |
| numeri della dashboard diversi dal baseline completo | hai caricato il campione | è corretto: leggi i numeri del campione nel dizionario §3 |
| `alembic check` segnala differenze | schema e modelli non allineati | non modificare migrazioni già mergiate: aggiungine una nuova |
| il web (8080) non chiama l'API | stai usando un bundle vecchio | riconstruisci con `up -d --build web` |

## 11. Dove andare dopo

- [Dizionario dati](data-dictionary.md): ogni campo e ogni regola KPI.
- [Contratto API](api-contract.md): envelope, paginazione, errori, ruoli.
- [Decisioni (ADR)](adr/): perché abbiamo scelto così.
- [Analisi](analysis/): cosa dicono i dati e con quali limiti.
- [Demo script](demo-script.md): la presentazione di 10 minuti, provata due volte.
- [Azioni umane](reviews/human-actions.md): cosa resta da fare alle persone.