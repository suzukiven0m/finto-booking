# Glossario

I termini tecnici che ricorrono nel progetto, spiegati in due righe. Siamo un
team misto (Web Solutions Architect e Data Analyst / AI Specialist): chi viene
dal web conosce JWT e proxy ma magari non macro-F1, chi viene dai dati conosce
Spearman ma magari non envelope. Questo glossario pareggia le competenze.
Ogni voce dice dove il termine si usa nel repo.

## A

**ADR (Architecture Decision Record)**
Un documento che registra una decisione importante: contesto, alternative,
scelta, conseguenze. Tenere le alternative scartate rende la scelta difendibile.
Si usa in: `docs/adr/0001-0004`.

**ADR (Average Daily Rate)**
Attenzione, stesso acronimo, significato diverso: è il ricavo medio per notte
venduta (ricavo / room-night). Si usa in: dizionario dati §3, dashboard.

**Anti-leakage**
L'insieme di regole che impediscono alle etichette vere (gold) di finire dove
il modello può vederle: se succedesse, la valutazione sarebbe una tautologia.
Si usa in: `data/eval/`, classificatore email, NLP recensioni.

**API**
Il punto di ingresso programmatico ai dati: indirizzi (endpoint) che rispondono
a richieste HTTP con dati JSON. Si usa in: `backend/app/`, contratto.

## B

**Baseline**
I numeri di riferimento verificati che ogni endpoint KPI deve riprodurre
(61.777 prenotazioni valide, 22.976.960,13 euro, ecc.). Se un endpoint dà numeri
diversi, il codice è sbagliato, non il baseline. Si usa in: dizionario §3, test.

## C

**Canale (market segment)**
Il segmento di vendita di una prenotazione (Online TA, Direct, Groups, ecc.).
Lo "share" dei canali è la frazione di prenotazioni, non di ricavo. Si usa in:
dizionario §3, analisi domanda/prezzi.

**CI (Continuous Integration)**
Il sistema che a ogni pull request accende un ambiente pulito ed esegue lint,
migrazioni, test ed E2E: se qualcosa si rompe, la PR non si merge. Si usa in:
`.github/workflows/ci.yml`.

**Colonna generata**
Una colonna che il database calcola da sola da altre colonne (qui `nights`):
non si scrive mai nel caricamento, così non può divergere. Si usa in:
`bookings`, migrazione 0001.

**Confusion matrix (matrice di confusione)**
Una tabella che mostra, per ogni classe, quante predizioni sono corrette e
quante confuse con altre classi. Dice DOVE il modello sbaglia, non solo quanto.
Si usa in: `data/eval/email_metrics.json`.

**Container**
Un processo isolato che impacchetta un'app con le sue dipendenze, così gira
uguale ovunque. Docker lo accende e spegne con un comando. Si usa in:
`infra/docker-compose.yml`.

**Contract-bump**
La procedura per modificare il contratto dopo il freeze: nuova ADR, bump del
numero di versione, migrazione se serve, risincronizzazione del mock, nota al
cliente. Niente modifiche silenziose. Si usa in: `docs/api-contract.md`.

**Contratto dati**
L'accordo scritto tra team dati e team web sul formato di schema e API
(`openapi.yaml`). Permette di lavorare in parallelo e integrare dopo. Si usa
in: `openapi.yaml`, mirror frontend.

## D

**Deduplica**
Rimuovere le righe identiche. Qui va fatta sulle 32 colonne ORIGINALI del CSV,
prima di aggiungerne altre: farla dopo dà un baseline diverso. Si usa in:
`data/etl/load_bookings.py`, dizionario assunzione 4.

**Disclosure**
Le dichiarazioni di onestà su cosa è vero e cosa no (strutture fittizie,
legame asserito, capacità assunta, email sintetiche, recensioni solo 2012).
Sono contenuto valutato, sempre in vista. Si usa in: README, footer UI, slide.

## E

**Endpoint**
Un indirizzo dell'API, per esempio `/api/kpis/summary`, che risponde a una
richiesta. Noi ne esponiamo 11. Si usa in: `backend/app/`, contratto.

**Envelope**
La forma uniforme delle risposte: le liste `{data, meta}`, gli errori
`{error{code, message}}`. Il frontend se la aspetta ovunque. Si usa in:
`docs/api-contract.md`, API.

**ETL (Extract, Transform, Load)**
Leggere dati grezzi, pulirli, caricarli nel database. Sono gli script del team
dati. Si usa in: `data/etl/`.

## F

**Foreign key (chiave esterna)**
Un vincolo che collega una riga a un'altra tabella. Qui `reviews` NON ha una
foreign key verso `bookings`: il legame è asserito, non fattuale. Si usa in:
`docs/erd.md`, dizionario §2.

**Freeze (congelamento)**
Il momento (SAL 1) in cui schema e contratto si fissano a `v1.0.0`: da lì ogni
modifica costa un contract-bump. Si usa in: tag git, `docs/sal1/`.

## G

**Gold file**
Il file con le etichette vere (`data/eval/email_gold.csv`), usato SOLO per
valutare, mai letto dalla pipeline. Si usa in: valutazione email.

## H

**HITL (Human In The Loop)**
Il principio per cui propone la macchina ma approva una persona: le bozze
email stanno in `draft`, nessuna parte da sola. Si usa in: inbox, classificatore.

## I

**Idempotente**
Uno script che puoi rilanciare senza duplicare i dati o rompere nulla. Tutti
gli script ETL lo sono. Si usa in: `data/etl/`.

## J

**JSON**
Il formato testuale con cui l'API scambia dati (chiavi e valori, leggibile).
Si usa in: tutte le risposte API.

**JWT (JSON Web Token)**
Il gettone firmato che il server rilascia al login e il client rimanda a ogni
chiamata protetta: dimostra identità e ruolo senza rimandare la password.
Si usa in: `backend/app/auth.py`, frontend sessione.

## L

**Lead time**
Quanti giorni prima dell'arrivo è stata fatta la prenotazione. Lo usiamo per
analizzare la domanda e le cancellazioni. Si usa in: analisi domanda/prezzi.

## M

**Macro-F1**
La media dell'F1 di ogni classe, dove l'F1 bilancia precision e recall. "Macro"
significa che ogni classe pesa uguale, anche se rara. Si usa in:
`data/eval/email_metrics.json` (categoria 0.9901, urgenza 0.9659).

**Migrazione**
Un passo numerato che modifica lo schema del database (crea tabelle, aggiunge
colonne). Si applicano in ordine e non si editano mai dopo il merge. Si usa in:
`backend/alembic/versions/0001-0005`.

**Mock**
Una simulazione dichiarata: Prism risponde con gli esempi del contratto senza
backend. Serve per sviluppare, NON è la demo (che gira su dati reali). Si usa
in: `frontend/mock/`, Prism.

## O

**Occupazione (occupancy)**
Il rapporto tra room-night vendute e camere disponibili, 0-1 (mai percentuale).
Qui è contro capacità ASSUNTA (190/230), non misurata. Si usa in: dizionario §3,
dashboard.

## P

**Proxy (reverse proxy)**
Un server che gira le chiamate verso un altro servizio: nginx manda `/api/...`
all'API, così browser e API stanno sulla stessa origine. Si usa in:
`frontend/nginx.conf`.

**PR (Pull Request)**
La proposta di modifica che si reviewa e si merge: il nostro flusso è builder,
reviewer indipendente, fix, merge. Si usa in: GitHub, CONTRIBUTING.

## R

**RevPAR (Revenue Per Available Room)**
Ricavo per camera disponibile (ricavo / camere / giorni). Come l'occupazione,
contro capacità assunta. Si usa in: dizionario §3, dashboard.

**Room-night**
Una camera occupata per una notte: l'unità base dei KPI di occupazione.
Si usa in: dizionario §3, baseline.

**Ruolo**
Il profilo di permesso dell'utente: admin, manager, property_manager. Tutti
leggono; solo admin/manager modificano le richieste ospiti. Si usa in:
`backend/app/auth.py`, contratto.

## S

**Schema**
La forma delle tabelle del database (colonne, tipi, vincoli). Si usa in:
`backend/app/models.py`, `docs/erd.md`.

**Seed**
Caricare i dati nelle tabelle. Si può caricare il campione (nel repo) o il
dataset completo (locale). Si usa in: `data/etl/`, getting-started.

**Sentiment**
L'orientamento emotivo di un testo (positivo/negativo/neutro) con un punteggio.
Lo calcoliamo con un modello multilingue preaddestrato. Si usa in: NLP recensioni.

**Sidecar**
Un container che condivide la rete di Postgres per raggiungere il database
quando la VPN blocca le porte pubblicate dall'host. Si usa in: getting-started,
test.

**SPA (Single Page Application)**
Una sola pagina HTML che cambia contenuto via JavaScript senza ricaricare.
La nostra dashboard ha quattro schede. Si usa in: `frontend/src/`.

**Spearman (correlazione di)**
Una misura di quanto due grandezze crescono insieme, basata sui ranghi (0 =
nessuna relazione, 1 = perfetta). La usiamo per sentiment vs voti reali.
Si usa in: `data/eval/review_nlp_metrics.json` (0.5517 pooled).

## V

**venv (ambiente virtuale Python)**
Una cartella con un Python isolato e le sue librerie: non tocca il sistema.
Si usa in: `backend/.venv`, getting-started.

## W

**Weak label (etichetta debole)**
Un riferimento indiretto per valutare: qui i voti reali degli ospiti come
proxy del sentiment, non etichette annotate a mano. Onesto per costruzione.
Si usa in: NLP recensioni, valutazione.

## Z

**Zero-shot**
Classificare senza addestramento sulle categorie: si dà al modello il testo e
le etichette candidate, e lui valuta quanto ciascuna si applica. Si usa in:
topic delle recensioni (bart-large-mnli).