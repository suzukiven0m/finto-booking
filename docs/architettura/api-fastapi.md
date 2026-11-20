# FastAPI: le 11 operazioni del contratto

## Cos'è

FastAPI è il framework Python con cui scriviamo l'API, cioè il punto di
ingresso programmatico ai dati. Un "endpoint" è un indirizzo (per esempio
`/api/kpis/summary`) che risponde a una richiesta HTTP con dati in formato
JSON. Noi esponiamo 11 operazioni, tutte dichiarate nel contratto
`openapi.yaml`.

## Perché l'abbiamo disegnato così

La scelta è in [ADR 0001](../adr/0001-tech-stack.md). FastAPI ci è sembrato
giusto per tre motivi:

- È Python, come gli script del team dati. Un solo linguaggio nel backend e
  nella pipeline significa meno attrito quando un DA deve capire come un KPI
  viene servito, o un WSA deve leggere una query.
- Genera documentazione automatica delle rotte e valida gli input con Pydantic
  (una libreria che controlla forme e tipi dei dati in ingresso).
- È leggero e asincrono, adatto a un servizio che legge molto dal database.

Abbiamo scartato Django (più pesante, con un ORM e un admin che non ci
servono), Flask (meno documentazione automatica) e un backend Node (avrebbe
diviso il team in due linguaggi).

Per le query usiamo SQLAlchemy Core con `text()` e parametri legati: scriviamo
SQL esplicito (le regole KPI sono nel dizionario e vogliamo vederle nella
query) ma senza rischio di SQL injection, perché i valori passano come
parametri, non concatenati nella stringa. Le uniche f-string nel SQL compongono
frammenti WHERE costanti, mai input utente. Abbiamo preferito questo a un ORM
"magico" che nasconde la query: per KPI con finestre e aggregazioni, vedere il
SQL è un vantaggio, non un limite.

## Com'è fatto in pratica

- `backend/app/main.py`: crea l'app, monta i router, registra gli handler
  degli errori, configura CORS per lo sviluppo locale.
- `backend/app/kpis.py`: summary, daily, channels, seasonality.
- `backend/app/reviews.py`, `bookings.py`, `guest_requests.py`, `auth.py`:
  le altre operazioni.
- `backend/app/errors.py`: l'envelope di errore uniforme.

Tre convenzioni che valgono per tutte le 11 operazioni:

1. **Envelope uniforme.** Le liste rispondono `{data: [...], meta: {page,
   page_size, total, total_pages}}`. Gli errori rispondono `{error: {code,
   message, details?}}` con codici coerenti (401, 403, 404, 422, 500). Il
   frontend si aspetta questa forma ovunque.
2. **Autenticazione a livello di router.** Ogni rotta protetta dipende da
   `get_current_user` (verifica il gettone JWT); la PATCH sulle richieste
   ospiti dipende anche da `require_write_role` (matrice dei ruoli). Le rotte
   `/api/properties` e `/api/auth/login` sono aperte per scelta di contratto.
3. **Formule KPI dal dizionario, non inventate.** L'occupazione media è
   "pooled" (Σ room-night / (Σ camere × giorni)), il summary conta la coorte
   di arrivo, il daily conta i giorni di soggiorno: ai bordi dell'intervallo
   i totali differiscono di proposito (finding S2, 19 giorni e 105.263,50 euro
   oltre il 31 agosto 2017). La stagionalità usa medie per mese dell'anno, mai
   totali grezzi (2015 e 2017 sono anni parziali). Lo share dei canali è la
   frazione di prenotazioni, non di ricavo. `reviews/summary` restituisce i
   voti reali degli ospiti, NON output di modelli.

## Limiti e cosa può andare storto

- La PATCH sulle richieste ospiti è "leggi, controlla, scrivi" senza lock di
  riga: con un solo operatore demo va bene, in concorrenza teorica due
  modifiche potrebbero sovrapporsi. È un limite dichiarato (P2 della review
  WP8), non un bug riproducibile nel contesto d'uso.
- Il fallback per corpus vuoto in `reviews/summary` restituirebbe punteggi
  0.0, in violazione del minimo 1 dello schema: irraggiungibile con i dati
  seedati (le proprietà hanno sempre recensioni), ma anotato come edge latente.
- Se una formula KPI cambia, va aggiornata nel dizionario PRIMA del codice:
  il contratto e i test pinned sono l'asserzione, non il contrario.

## Riferimenti

- [Contratto API](../api-contract.md)
- [Dizionario dati §3](../data-dictionary.md)
- [Autenticazione e ruoli](auth-jwt-ruoli.md)
- [Contract test](contract-tests.md)
- Codice: `backend/app/`
