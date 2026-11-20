# nginx: il ponte tra dashboard e API

## Cos'è

nginx è un piccolo server web. Nel nostro progetto fa due cose: serve i file
statici della dashboard (HTML, JavaScript, CSS costruiti da Vite) e gira le
chiamate che iniziano con `/api/` verso il servizio API. Questo secondo ruolo
si chiama "reverse proxy": il browser parla con nginx, nginx parla con l'API,
e il browser non deve sapere dov'è l'API.

## Perché l'abbiamo disegnato così

Il problema che risolve è l'origine delle chiamate. Il browser, per sicurezza,
blocca le chiamate verso un dominio o una porta diversi da quelli della pagina
(CORS, Cross-Origin Resource Sharing). Se la dashboard sta su `:8080` e l'API
su `:8000`, servirebbero header CORS e configurazioni in più.

Con nginx tutto sta sulla stessa origine (`:8080`): la pagina e le chiamate
`/api/...` escono dallo stesso posto, e nginx le smista internamente. Niente
CORS in produzione, una configurazione in meno, un comportamento più vicino a
come si deploya davvero un'app del genere.

Abbiamo scartato due alternative:

- Far servire i file statici direttamente da FastAPI: mischia due responsabilità
  (API e serving di file) e rinuncia a cache, header e compressione che nginx
  gestisce bene.
- Usare il proxy di Vite: va bene in sviluppo, ma Vite non è un server di
  produzione. In produzione serve qualcosa di solido.

Il bundle è costruito con `VITE_API_BASE_URL=""` (base vuota). I percorsi nel
client sono già `/api/auth/login`, `/api/kpis/summary`, eccetera: con base vuota
la fetch resta `/api/...`, singola prefix, e nginx la inoltra corretta. Una base
`/api` avrebbe prodotto il doppio prefisso `/api/api/...` (il bug P0 della
review WP14, corretto e verificato a livello di bundle).

## Com'è fatto in pratica

- `frontend/nginx.conf`: la configurazione. Il blocco `location /api/` fa
  `proxy_pass http://api:8000;` (senza slash finale, così il prefisso `/api`
  viene preservato e arriva all'API che ha rotte `/api/*`). Il blocco
  `location /` usa `try_files ... /index.html`: qualunque percorso non trovato
  ricade sulla pagina principale, così le schede funzionano anche ricaricando.
- `frontend/Dockerfile`: build multi-stadio. Primo stadio `node:22-alpine`
  costruisce il bundle (`npm ci`, `npm run build` con la base vuota). Secondo
  stadio `nginx:alpine` copia solo il bundle e la configurazione. L'immagine
  finale è piccola: niente Node dentro, solo nginx e file statici.
- Il servizio `web` in `infra/docker-compose.yml` espone la porta 8080.

## Limiti e cosa può andare storto

- nginx risolve il nome `api` solo dentro la rete Docker Compose. Un
  `nginx -t` lanciato fuori dalla rete fallisce sul DNS dell'upstream: è
  previsto, non è un errore di configurazione. La prova vera è `compose up`.
- Se ricostruisci l'immagine web senza la base vuota corretta, il bundle
  punterà altrove e la dashboard non chiamerà l'API. Il test E2E e la verifica
  del bundle (grep di `localhost:8000` e `/api/api` assenti) lo intercettano.
- nginx non fa autenticazione: la fa l'API. Il proxy inoltra e basta, incluso
  l'header Authorization.

## Riferimenti

- [Docker Compose](docker-compose.md)
- [API FastAPI](api-fastapi.md)
- [SPA React](spa-react.md)
- Codice: `frontend/nginx.conf`, `frontend/Dockerfile`
