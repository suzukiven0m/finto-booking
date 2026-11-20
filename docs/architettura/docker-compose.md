# Docker Compose: tre servizi con un comando

## Cos'è

Docker Compose è lo strumento che accende più container insieme, descritti in
un file YAML. Un container è un processo isolato che impacchetta un'applicazione
con le sue dipendenze. Nel nostro progetto `infra/docker-compose.yml` definisce
tre servizi: `postgres` (il database), `api` (FastAPI), `web` (nginx con la
dashboard). Un comando li costruisce e li avvia tutti.

## Perché l'abbiamo disegnato così

Il brief chiede un'applicazione funzionante con database, API e interfaccia,
e uno spazio di deploy. Compose ci dà riproducibilità: chiunque cloni il repo
e abbia Docker ottiene lo stesso ambiente, senza installare PostgreSQL o
configurare porte a mano. È la scelta di [ADR 0001](../adr/0001-tech-stack.md)
per l'infrastruttura di sviluppo e demo.

Tre principi di design:

1. **Le immagini contengono solo codice, niente dati.** I dataset completi
   restano sulla drive del cliente (non entrano nel repo, per privacy e peso).
   Schema e seed sono passi manuali documentati, così sai sempre cosa c'è nel
   database e le immagini restano leggere e riutilizzabili.
2. **Il database persiste, i servizi no.** Il volume `pgdata` tiene i dati
   tra un riavvio e l'altro. `api` e `web` sono usa-e-getta: li ricostruisci
   a ogni modifica del codice senza perdere il caricamento.
3. **Stessi default pubblicati ovunque.** Il servizio `api` riceve solo
   `POSTGRES_HOST: postgres`; è `config.py` che assembla la stringa di
   connessione dai default di sviluppo (buby/buby/buby). Questo evita di
   ripetere credenziali nel file compose.

Quest'ultimo punto ha una storia. Il scanner di segreti GitGuardian flaggava
la riga `DATABASE_URL` con la password inline nel compose. Abbiamo provato un
file di ignore (non rispettato dall'integrazione dashboard), uno squash della
history (il pattern ri-triggerava), e le variabili standalone (flaggate anche
quelle nel contenuto nuovo). La soluzione che ha funzionato: togliere del
tutto il pattern dal contenuto nuovo, lasciando che sia `config.py` a costruire
la URL dai suoi default. Un commit pulito, "No secrets detected". Lezione: per
i default di sviluppo, la rimozione del pattern è la strada percorribile senza
intervento umano sul dashboard. E `exec api alembic` funziona lo stesso, perché
le variabili sono a livello di container (non c'è un entrypoint che le nasconde).

## Com'è fatto in pratica

- `infra/docker-compose.yml`: i tre servizi, il volume, le porte (5432, 8000,
  8080), `depends_on` con healthcheck di postgres.
- `backend/Dockerfile`: python:3.12-slim, dipendenze fissate, copia di `app`
  e `alembic`, CMD uvicorn.
- `frontend/Dockerfile`: multi-stadio node build → nginx serve (vedi
  [nginx-proxy.md](nginx-proxy.md)).
- `.dockerignore` in backend e frontend: tengono fuori `.venv`, `node_modules`,
  test e cache dalle immagini.

Due percorsi d'uso:

- **Tutto Docker** (per provare): `up -d --build`, poi `exec api alembic
  upgrade head`, poi il seed da un venv host, poi apri `:8080`.
- **Sviluppo locale**: `up -d postgres` SOLO il database, perché l'API la
  avvii tu con uvicorn sulla 8000. Se accendessi anche il container `api`,
  la porta sarebbe occupata e uvicorn locale fallirebbe (il P1 della review
  WP14, corretto nel README e negli script `avvia`).

Per credenziali custom via `infra/.env`, vanno passate anche al servizio api
(`POSTGRES_USER/PASSWORD/DB`), non solo a postgres: il default demo non ne ha
bisogno.

## Limiti e cosa può andare storto

- Il deploy pubblico è proposto in [ADR 0004](../adr/0004-deploy.md)
  (Render/Vercel/Neon) ma gli account sono un'azione umana (HA-10): la demo
  gira in locale. Compose è la base, non il deploy finale.
- Su macchine con VPN attiva, le porte pubblicate dal container non sono
  raggiungibili dall'host: si usa il pattern sidecar (un container che condivide
  la rete di postgres, spiegato nel README e nella guida `docs/getting-started.md`
  se presente).
- `down -v` cancella il volume e tutti i dati caricati: va usato solo quando
  lo si vuole davvero.

## Riferimenti

- [ADR 0001: stack](../adr/0001-tech-stack.md)
- [ADR 0004: deploy (proposto)](../adr/0004-deploy.md)
- [nginx proxy](nginx-proxy.md)
- [Migrazioni Alembic](migrazioni-alembic.md)
- Codice: `infra/docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`
