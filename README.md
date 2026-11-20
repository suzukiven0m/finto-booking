# Buby Travel (finto-booking)

Questo repository è il nostro progetto di laboratorio per il caso 1 (Turismo)
di Buby Group. Siamo un team misto di due corsi: Data Analyst / AI Specialist
(DA) e Web Solutions Architect (WSA). I DA preparano e analizzano i dati, i WSA
costruiscono database, API e interfaccia web. Il punto dell'esercizio è proprio
questo: due team con competenze diverse che si accordano su un contratto dati
e consegnano un prodotto funzionante.

Se è la prima volta che apri il progetto, leggi questa pagina e poi la
[guida per iniziare](docs/getting-started.md): lì c'è ogni passaggio spiegato
per bene, anche se non hai mai usato Docker o un'API.

## Di cosa si tratta

Buby Travel gestisce hotel sul lago e in montagna. Il cliente ci ha chiesto tre
cose:

1. capire quali fattori influenzano la soddisfazione e la reputazione degli ospiti;
2. prevedere la domanda e supportare le decisioni sui prezzi;
3. dare alla direzione una dashboard su occupazione e reputazione, con un
   assistente che aiuta a rispondere alle richieste degli ospiti.

Noi abbiamo costruito un'applicazione web che mostra i KPI di occupazione e
ricavo, una pagina reputazione basata sulle recensioni, una ricerca sulle
prenotazioni e una inbox dove l'assistente propone bozze di risposta che una
persona approva prima di inviare. I dati arrivano da un database PostgreSQL,
passano per un'API FastAPI e finiscono in una dashboard React.

Il contratto tra i due team (schema del database + formato dell'API) è
congelato alla versione `v1.0.0` dal SAL 1 del 20 novembre 2026. Da quel momento
ogni modifica al contratto segue una procedura scritta (nuova decisione, nuovo
numero di versione, migrazione dedicata). Lo spiegiamo in
[docs/api-contract.md](docs/api-contract.md).

## Cosa è vero e cosa no (da leggere prima di tutto)

Il cliente non ci ha mai consegnato dati suoi. Abbiamo sostituito i dati con
sorgenti pubbliche e dichiarate. Queste affermazioni sono vincolanti: le
ripetiamo nella dashboard, nelle slide e nel report finale.

- Le due strutture "Buby Lago" e "Buby Montagna" sono **fittizie**: sono la
  mappatura 1:1 dei due tipi di hotel del dataset pubblico (Resort e City).
- Le prenotazioni sono **reali** ma vengono da un dataset portoghese del
  2015-2017 (Kaggle, Hotel Booking Demand), non da Buby.
- Le recensioni sono **reali** (corpus TripAdvisor, Li et al. 2013) ma il legame
  con le prenotazioni è **asserito a livello di proprietà**, non fattuale: una
  recensione del 2012 non è l'ospite di una prenotazione del 2016.
- Le recensioni sono **tutte del 2012**, le prenotazioni coprono 2015-2017:
  **non esiste nessun mese in comune**. Quindi non facciamo analisi congiunte
  per mese e non leggiamo il trend reputazione come causa dell'occupazione.
- Il corpus recensioni è **solo inglese**, 1.638 recensioni (762 + 876).
- Le email degli ospiti sono **sintetiche** (800, generate da noi, nomi
  inventati): servono per dimostrare l'assistente, non sono corrispondenza vera.
- La capacità delle strutture (190 e 230 camere) è **assunta**, ricavata dai
  picchi osservati: occupazione e RevPAR non sono misure, e lo diciamo sempre.

Nessun dato personale e nessun dataset completo entra nel repository: in
`data/raw/` ci sono solo campioni ridotti (il `.gitignore` lo impone).

## Cosa fa l'applicazione

Quattro schede, tutte con le disclosure in fondo alla pagina:

- **Dashboard**: KPI di occupazione, ricavo, ADR, cancellazioni, grafico
  giornaliero. I numeri seguono le regole scritte nel
  [dizionario dati](docs/data-dictionary.md).
- **Reputazione**: voti medi reali (overall + cinque dimensioni), volume
  recensioni, trend mensile etichettato "solo 2012".
- **Ricerca**: filtri e paginazione sulle prenotazioni.
- **Inbox**: l'assistente classifica le email e propone bozze. Una persona
  modifica e approva: nessuna email parte da sola (HITL, human in the loop).

L'API espone 11 operazioni con autenticazione JWT e tre ruoli. Il classificatore
email e l'analisi del sentiment delle recensioni sono componenti AI con
valutazione onesta: i numeri e i limiti sono in [docs/analysis/](docs/analysis/).

## Come è organizzato il repository

```text
finto-booking/
├── backend/     app FastAPI, schema, migrazioni, test   (WSA)
├── frontend/    dashboard React + Vite                 (WSA)
├── data/        ETL, generatori, analisi, test          (DA)
├── infra/       docker-compose (Postgres + API + web)   (WSA)
├── docs/        piani, decisioni, contratto, dizionario, analisi, review
└── .github/     CI (lint, migrazioni, test, E2E)
```

## Per iniziare (versione breve)

Serve Docker con Compose. Dalla root del repository:

```bash
docker compose -f infra/docker-compose.yml up -d --build
docker compose -f infra/docker-compose.yml exec api alembic upgrade head
```

Poi carica i dati di esempio e le bozze dell'assistente (i passaggi completi,
con la spiegazione di ogni comando, sono nella [guida per iniziare](docs/getting-started.md)):

```bash
PYTHONPATH=backend backend/.venv/bin/python data/etl/load_bookings.py data/raw/sample_hotel_bookings.csv
PYTHONPATH=backend backend/.venv/bin/python data/etl/load_reviews.py
PYTHONPATH=backend backend/.venv/bin/python data/etl/gen_emails.py
PYTHONPATH=backend backend/.venv/bin/python data/etl/build_kpi_daily.py
PYTHONPATH=backend:data backend/.venv/bin/python data/etl/classify_emails.py --persist
```

Apri http://localhost:8080 e accedi con `manager@buby.travel`, password `demo`.
Con il campione da 5.000 prenotazioni la dashboard mostra 3.564 prenotazioni
valide e 1.350.503,84 euro di ricavo. I numeri del dataset completo sono diversi
e sono scritti nel dizionario dati: la guida spiega come caricare il dataset
intero se ce l'hai in locale.

## Numeri di riferimento

Il baseline è un'asserzione, non un obiettivo: se un endpoint restituisce numeri
diversi, il codice è sbagliato. Dataset completo (87.396 righe dopo deduplica):

| Metrica | Valore |
|---|---:|
| Prenotazioni valide | 61.777 |
| Room-night | 218.410 |
| Ricavo realizzato | 22.976.960,13 euro |
| ADR | 105,20 euro |
| Cancellation rate | 27,49% |

Campione committato (5.000 righe): 3.564 valide, 12.696 room-night,
1.350.503,84 euro, cancellation 26,96%. Tutte le regole di calcolo sono in
[docs/data-dictionary.md](docs/data-dictionary.md) §3.

## Test e CI

A oggi: backend 140 passed + 1 skipped, data 133 passed + 1 skipped, frontend
19 passed (più typecheck e build). Lo skip è previsto: un test sul baseline
completo salta quando nel database c'è il campione, e viceversa. La CI su ogni
PR esegue lint, migrazioni, round-trip su database vuoto, seed del campione,
classificatore email, test e uno smoke E2E che accende l'API vera e verifica le
stesse chiamate che fa la dashboard.

## Documentazione

- [Guida per iniziare](docs/getting-started.md): installazione e primo avvio, spiegati passo passo.
- [Dizionario dati](docs/data-dictionary.md): ogni campo, ogni regola KPI, le assunzioni.
- [ERD](docs/erd.md): lo schema del database in un diagramma.
- [Contratto API](docs/api-contract.md): convenzioni, autenticazione, ruoli, disclosure.
- [Decisioni (ADR)](docs/adr/): perché abbiamo scelto stack, persistenza, sorgenti dati, deploy.
- [Analisi](docs/analysis/): reputazione NLP, assistente email, domanda e prezzi, report finale.
- [Piani](docs/plan.md) e [delivery-plan](docs/delivery-plan.md): chi fa cosa e quando.
- [SAL 1](docs/sal1/): slide, catalogo KPI da firmare, stato settimanale per il cliente.
- [Demo script](docs/demo-script.md) e [rehearsal](docs/reviews/2026-11-20-demo-rehearsals.md).
- [Review e audit](docs/reviews/): il percorso di verifica, finding per finding.
- [Azioni umane](docs/reviews/human-actions.md): le cose che solo le persone possono fare (firmare, inviare, pagare).

## Stato del progetto e prossimi passi

Il minimo richiesto dal brief è funzionante su dati reali: dati puliti e
documentati, componente di analisi KPI, componente di elaborazione testi/email,
app web con database, API, dashboard, ricerca e autenticazione. Il deploy
pubblico è proposto in [ADR 0004](docs/adr/0004-deploy.md) ma gli account sono
un'azione umana: la demo gira in locale.

Restano azioni umane, tracciate nel [registro](docs/reviews/human-actions.md):
firmare il catalogo KPI, inviare lo stato settimanale al cliente, notificare il
lavoro svolto in solo e riassegnare formalmente i workstream, decidere chiavi
LLM e costi (il percorso LLM dell'assistente è pronto ma bloccato lì), creare
gli account di deploy. Lo stato completo della remediation è in
[docs/reviews/2026-11-20-remediation-status.md](docs/reviews/2026-11-20-remediation-status.md).