Lavoro svolto

Ho preparato la struttura del database che usa il progetto, cioè come sono organizzati e collegati i dati.

Il database contiene cinque tabelle:
- Hotel: le due strutture, Buby Lago e Buby Montagna.
- Prenotazioni: prese dal file di dati che abbiamo scelto come fonte.
- Recensioni: per ora vuota, la riempiremo quando avremo votato ADR 003, quindi quando avremo deciso come gestire le recensioni generate.
- Email/Domande degli ospiti: per ora vuota, servirà all'assistente che propone le risposte.
- Numeri giornalieri: per ogni hotel e ogni giorno, occupazione, incassi e prezzo medio. Si calcoleranno dalle prenotazioni.

Ogni tabella è collegata al suo hotel, così si possono vedere i dati di una sola struttura o di entrambe.

Ho fatto in modo che chiunque del gruppo possa creare lo stesso database sul proprio computer con un solo comando. Ho aggiunto anche dei controlli automatici che verificano che sia tutto al suo posto.

Serve Docker Desktop acceso e Python installato.

1. Accendere il database (dalla cartella finto-booking):
docker compose -f infra/docker-compose.yml up -d
2. Entrare nella cartella del backend e preparare Python (solo la prima volta):
cd backend
python3 -m venv .venv
source .venv/bin/activate (Io ho usato mac, quindi questo comdando funziona con quello e Linux. Su Windows usare .venv\Scripts\activate.)
pip install -r requirements.txt
   Le volte dopo basta source .venv/bin/activate. 
3. Creare le tabelle:
alembic upgrade head
4. Lanciare i controlli:
python -m pytest
   Se è tutto a posto compare 5 passed.

Per vedere le tabelle a mano su terminale:
docker exec -it buby-postgres psql -U buby -d buby -c '\dt'

E' tutto un working progress quindi qualsiasi cosa può essere modificata o aggiornata, poi quando ci incontriamo facciamo un check e vediamo cosa va bene e cosa no.