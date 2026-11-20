# ADR 0004 — Target di deploy (D18)

- **Stato:** Proposto, in attesa di account umani (HA-10) — **nessun voto del team**
- **Data:** 2026-11-20
- **Decisori:** 3 Web Solutions Architect + 3 Data Analyst / AI Specialist (ratifica pendente)
- **Scadenza decisione:** 2026-11-13 (delivery-plan §2) — **scaduta**, registrata overdue in HA-10
- **Correlati:** `docs/delivery-plan.md` §2/§8, `docs/reviews/2026-11-19-shepherd-audit.md` §8.10 (R10/R15), `docs/reviews/human-actions.md` HA-10, `docs/adr/0001-tech-stack.md`, `docs/adr/0002-data-storage.md`

## Contesto

D18 (delivery-plan §2, «Never cut» §11) chiede deploy + URL pubblico per il
grading; la demo finale del 18 dic gira **in locale**, mai su un'istanza free
cold-started (delivery-plan §2: «the demo runs on local docker compose»).
Il target «Render (API) + Vercel (SPA) + Neon (Postgres), free tiers» era da
decidere entro il 13 nov: nessuna decisione registrata finché questo ADR non
esiste (audit §8.10: «deploy decision has no record»).

Stato tecnico pronto per il deploy (WP14, verificato il 2026-11-20):
`infra/docker-compose.yml` con postgres + **api** + **web**; `backend/Dockerfile`
(python:3.12-slim, uvicorn) e `frontend/Dockerfile` (node:22-alpine build →
nginx:alpine, proxy `/api` → api:8000, SPA fallback) buildano entrambi;
`docker compose config -q` OK. Migrazioni e seed restano passi manuali
documentati (README «Run with Docker»): le immagini non contengono dati.

**Gate umani (non attraversabili da un agent):** creazione account, eventuale
spesa, deploy pubblico. HA-10 è overdue (decisione 13 nov; account entro
D18, 17 dic). Questo ADR **propone** il target e prepara gli artefatti;
l'esecuzione e la registrazione della decisione finale sono umane.

## Opzioni considerate

### A. Render (API) + Vercel (SPA) + Neon (Postgres) — free tier

Il target già nominato dal delivery-plan §2.

- Render esegue `backend/Dockerfile` così com'è; env `DATABASE_URL` verso Neon
  (`postgresql+psycopg://…`), nessun cambio al codice. Neon è Postgres
  standard: schema/migrazioni Alembic e seed documentati girano identici.
- Vercel serve la SPA statica. Il bundle è buildato con
  `VITE_API_BASE_URL=""` (base vuota: le path del client sono già `/api/*`,
  fetch same-origin a prefisso unico): su Vercel serve una rewrite
  `/api/* → https://<render-service>/api/*` (vercel.json, artefatto da
  preparare al momento del deploy). Same-origin = **nessuna modifica CORS al
  backend** (l'app consente solo localhost:5173/5174; l'alternativa
  «bundle punta diretto a Render» richiederebbe un cambio app = fuori scope).
- Pro: zero operations (TLS, URL, build automatiche), costo zero, tre servizi
  gestiti dai rispettivi provider; è il target del piano, nessuna sorpresa al grading.
- Contro: **cold start** (i free tier dormono: istanza da scaldare 10 min
  prima di ogni check esterno, delivery-plan §2); tre account umani da creare
  e registrare (HA-10); limiti di ore/risorse del free tier; il seed del DB
  pubblico va lanciato a mano verso Neon (comandi README, dataset completo
  dalla drive del cliente — nessun dato cliente nel repo, dizionario §4).

### B. VM singola (processi nativi o docker manuali)

- Pro: un solo host, niente cold start, controllo totale.
- Contro: provisioning/TLS/reverse-proxy/backup/aggiornamenti tutti manuali;
  procurement della VM è spesa/account = gate umano comunque; single point of
  failure; non è il target del piano (deliverable «D1 deploy» nasce con
  compose). Più lavoro operativo di A a parità di risultato pubblico.

### C. compose-on-VM (stesso `infra/docker-compose.yml` su una VM)

- Pro: **identico alla demo locale** — un solo artefatto, riproducibile,
  niente cold start; il passo da locale a pubblico è `docker compose up -d
  --build` sulla VM.
- Contro: la VM va procurata (gate umano/spesa); TLS e reverse proxy verso
  le porte 8080/8000 restano manuali (nginx/caddy + certificati); esposizione
  porte e aggiornamenti di sicurezza a carico del team. Resta un'opzione
  valida se i free tier di A si rivelano inadatti al grading.

## Raccomandazione (proposta, non accettata)

**Opzione A** per l'URL pubblico: è il target già scritto nel delivery-plan,
minimo lavoro operativo, costo zero, e gli artefatti WP14 (Dockerfile +
compose) la supportano senza modifiche al codice. **La demo resta locale in
ogni caso** (compose o host venv, `docs/demo-script.md`): i free tier dormono
e un cold start in diretta è il rischio R15 dell'audit.

**Fallback: opzione C** se i free tier non reggono il check di grading — stesso
compose, nessuna riscrittura. Opzione B scartata: più operations a parità di
risultato, e il procurement è comunque un gate umano.

Passi di esecuzione (umani, dopo la creazione account HA-10):

1. Neon: creare il DB, lanciare migrazioni + seed documentati con
   `DATABASE_URL` puntato a Neon (README «Run with Docker», passo seed).
2. Render: nuovo web service dal repo, Dockerfile `backend/Dockerfile`,
   env `DATABASE_URL` (Neon) — i default JWT/demo sono pubblicati, non segreti
   (`docs/api-contract.md`); utenti veri = protocollo S7/contract-bump.
3. Vercel: deploy frontend con `VITE_API_BASE_URL=""` + rewrite `/api/*`
   verso il servizio Render (artefatto da preparare al deploy).
4. Scaldare l'istanza 10 min prima di ogni check esterno; registrare l'URL
   pubblico in HA-10 e nel report finale.

**Sicurezza:** i default di sviluppo sono pubblicati (S7, `docs/api-contract.md`); un deploy reale DEVE impostare `POSTGRES_PASSWORD` e `JWT_SECRET` via env.

## Stato della decisione

**Proposto, in attesa di account umani.** Nessun voto del team è avvenuto:
lo stato non è «Accettato». La decisione di target (scaduta il 13 nov) e la
creazione degli account (entro D18) sono registrate in **HA-10**
(`docs/reviews/human-actions.md`, overdue): le chiude un umano con evidenza
linkata, non un agent. L'URL pubblico resta **pending human**; la demo del
18 dic è locale indipendentemente da questo ADR.