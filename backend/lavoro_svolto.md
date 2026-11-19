Lavoro svolto

12-13 novembre

Ho preparato la struttura del database che usa il progetto, cioè come sono organizzati e collegati i dati.

Il database contiene cinque tabelle:
- Hotel: le due strutture, Buby Lago e Buby Montagna.
- Prenotazioni: prese dal file di dati che abbiamo scelto come fonte.
- Recensioni: le recensioni TripAdvisor dei due hotel.
- Email/Domande degli ospiti: servirà all'assistente che propone le risposte.
- Numeri giornalieri: per ogni hotel e ogni giorno, occupazione, incassi e prezzo medio. Si calcolano dalle prenotazioni.

Ogni tabella è collegata al suo hotel, così si possono vedere i dati di una sola struttura o di entrambe.

Ho fatto in modo che chiunque del gruppo possa creare lo stesso database sul proprio computer con un solo comando. Ho aggiunto anche dei controlli automatici che verificano che sia tutto al suo posto.

16-17 novembre

Ho preparato le prime API, cioè gli indirizzi che la dashboard usa per prendere i dati dal database:
- Hotel.
- Numeri principali: incassi, notti, prezzo medio, cancellazioni e occupazione. Si può scegliere l'hotel e il periodo.
- Numeri giorno per giorno: se si guardano tutti e due gli hotel, ho sommato i due per ogni giorno.
- Login: per ora finto, entra con qualsiasi password.

Ho seguito le regole del dizionario dei dati e ho controllato che con i dati di prova escano gli stessi numeri. Se si sbaglia qualcosa, per esempio un hotel che non esiste, l'API risponde con un errore.

Ho collegato la dashboard alle API e ho aggiunto una pagina di login di prova. Ho aggiunto anche dei controlli automatici che verificano che i numeri siano giusti.

Ho aggiunto avvia.sh (Mac e Linux) e avvia.bat (Windows) per accendere database, API e dashboard con un solo comando. È provvisorio, finché il docker compose non accende anche API e dashboard.

Serve Docker Desktop acceso, Python e Node installati.

1. Accendere il database (dalla cartella finto-booking):
docker compose -f infra/docker-compose.yml up -d
2. Entrare nella cartella del backend e preparare Python (solo la prima volta):
cd backend
python3 -m venv .venv
source .venv/bin/activate (Io ho usato mac, quindi questo comando funziona con quello e Linux. Su Windows usare .venv\Scripts\activate.)
pip install -r requirements.txt
   Le volte dopo basta source .venv/bin/activate.
3. Creare le tabelle:
alembic upgrade head
4. Caricare i dati di prova: seguire il punto 3 del README.
5. Lanciare i controlli:
python -m pytest
   Se è tutto a posto compare 28 passed.
6. Accendere le API:
uvicorn app.main:app --reload
7. Accendere la dashboard (dalla cartella frontend, in un altro terminale):
VITE_API_BASE_URL=http://localhost:8000 npm run dev

Dopo la prima volta basta ./avvia.sh (su Windows avvia.bat) dalla cartella finto-booking.

Per vedere le tabelle a mano su terminale:
docker exec -it buby-postgres psql -U buby -d buby -c '\dt'

E' tutto un working progress quindi qualsiasi cosa può essere modificata o aggiornata, poi quando ci incontriamo facciamo un check e vediamo cosa va bene e cosa no.
