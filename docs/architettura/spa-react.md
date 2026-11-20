# SPA React: l'interfaccia a quattro schede

## Cos'è

È la pagina web che il cliente vede nel browser. "SPA" sta per Single Page
Application: una sola pagina HTML che carica JavaScript e poi cambia contenuto
senza ricaricare tutto da capo. Noi mostriamo quattro schede (Dashboard,
Reputazione, Ricerca, Inbox) dentro la stessa pagina.

## Perché l'abbiamo disegnato così

La scelta dello stack (React 18, TypeScript, Vite, Tailwind, Recharts) è
registrata in [ADR 0001](../adr/0001-tech-stack.md). I motivi pratici:

- Il team WSA conosceva già l'ecosistema JavaScript. React era la scelta con
  meno attrito, non la più "moderna".
- TypeScript ci dà un controllo gratis sul contratto: i tipi in `api/types.ts`
  rispecchiano le forme dichiarate in `openapi.yaml`. Se un campo cambia nome
  o tipo, il compilatore se ne accorge prima che lo veda l'utente.
- Vite ricarica la pagina a ogni modifica in sviluppo (feedback immediato) e
  costruisce il bundle finale per la produzione.
- Recharts disegna i grafici (trend giornaliero, trend reputazione) senza
  scrivere SVG a mano.

Abbiamo scartato Vue e Angular (meno familiarità nel team), Next.js (il server
side rendering non ci serve: i dati arrivano dall'API, non dal server della
pagina) e un router come react-router (per quattro schede basta uno stato
`useState<Tab>`, una dipendenza in meno).

La sessione (il gettone JWT, spiegato in [auth-jwt-ruoli.md](auth-jwt-ruoli.md))
sta in `sessionStorage`: sopravvive al ricaricamento della pagina ma sparisce
quando chiudi la scheda. Abbiamo preferito questo a `localStorage` perché per
una demo è più pulito: niente gettoni che restano nel browser per giorni.

## Com'è fatto in pratica

- `frontend/src/App.tsx`: le quattro schede, l'header con logout, il footer
  con le disclosure.
- `frontend/src/pages/`: Reputazione, Ricerca, Inbox.
- `frontend/src/api/client.ts`: le funzioni tipizzate che chiamano l'API,
  la gestione del 401 (gettone scaduto) che riporta al login.
- `frontend/src/api/types.ts`: le forme delle risposte, allineate al contratto.
- `frontend/src/session.ts` e `AuthGate.tsx`: login, sessione, logout.

Tre scelte di design che vale la pena capire:

1. **Le disclosure sono in fondo a ogni scheda**, non solo nella dashboard.
   Sono contenuto valutato: proprietà fittizie, legame asserito, capacità
   assunta, email sintetiche. Il footer è fratello del contenuto principale,
   quindi compare sempre.
2. **Il trend reputazione è etichettato "solo 2012"** con una nota che spiega
   che le prenotazioni coprono 2015-2017 e non c'è nessun mese in comune
   (finding S4 dell'audit). Non vogliamo che qualcuno legga il trend come
   causa dell'occupazione. Il trend mensile si calcola lato client scaricando
   tutte le pagine di `/api/reviews` (circa 9 richieste da 200): il contratto
   congelato non ha un endpoint mensile, e questa scelta è documentata.
3. **La inbox non invia mai da sola.** Il pulsante "invia" fa una PATCH
   esplicita solo da stato `draft`; lo stato `sent` è terminale (azioni
   disabilitate). Il ruolo `property_manager` non vede i pulsanti di scrittura
   e riceve un messaggio 403 se prova a chiamare l'API. È il principio HITL
   (human in the loop): propone la macchina, approva una persona.

Il client punta di default a `http://localhost:8000` (l'API vera). Nella build
Docker la base è vuota (`VITE_API_BASE_URL=""`): i percorsi sono già `/api/...`,
quindi le chiamate restano sulla stessa origine e passano dal proxy nginx.
Abbiamo imparato questo a nostre spese: una base `/api` sommata a percorsi già
`/api/...` produceva `/api/api/...` e ogni chiamata dava 404 (il P0 della
review WP14, poi corretto).

## Limiti e cosa può andare storto

- I test sono 19, in ambiente node con fetch simulato. Non abbiamo test di
  componenti nel browser (manca jsdom): la logica nuova è coperta dai test
  sul client API, la resa visiva si verifica a mano. È un limite dichiarato.
- Il trend scarica 9 pagine in sequenza con un unico stato di caricamento:
  a volume demo va bene, con molti più dati servirebbe un endpoint aggregato
  (che oggi richiederebbe un contract-bump).
- Se cambi le forme in `types.ts` senza aggiornare il contratto (o viceversa)
  i test lo segnalano, ma solo dove ci sono assertion: la disciplina resta
  umana.

## Riferimenti

- [ADR 0001: stack tecnologico](../adr/0001-tech-stack.md)
- [Contratto API](../api-contract.md)
- [Dizionario dati §3: regole KPI e baseline](../data-dictionary.md)
- [Analisi reputazione NLP](../analysis/reputation-nlp.md)
- Codice: `frontend/src/`
