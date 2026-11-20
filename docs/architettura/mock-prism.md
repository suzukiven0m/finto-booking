# Mirror e Prism: lavorare sul contratto senza backend

## Cos'è

Sono due pezzi che permettono al team web di lavorare prima che l'API vera
esista. Il **mirror** è una copia byte-identical di `openapi.yaml` dentro
`frontend/mock/`. **Prism** è un finto server che legge quel file e risponde
con gli esempi scritti nel contratto, senza database né logica: un "mock",
cioè una simulazione dichiarata.

## Perché l'abbiamo disegnato così

Il rischio dominante di [ADR 0001](../adr/0001-tech-stack.md) era il punto di
giunzione tra i due team: se i WSA aspettano l'API vera per iniziare, perdono
giorni; se i DA aspettano il frontend per validare il formato, idem. Il
contratto + mock rompe l'attesa: dal giorno 3 i WSA hanno un server che risponde
con le forme concordate, e possono costruire la dashboard mentre i DA
preparano i dati reali.

Il mirror è byte-identical per una ragione precisa: se la copia nel frontend
diverge dal contratto canonico, il team web lavora su una versione sbagliata
senza accorgersene. La regola è `cp openapi.yaml frontend/mock/openapi.yaml`
nello STESSO commit di ogni modifica al contratto, e `diff -q` deve essere
pulito. È un invariante verificato a ogni review.

Prism rispetta anche la sicurezza dichiarata: senza gettone risponde 401,
come farebbe l'API vera. Così il frontend gestisce il 401 fin da subito, non
solo quando arriva l'autenticazione reale.

**Il mock NON è il percorso demo.** Questo è il punto più importante. Il brief
valuta l'integrazione con i dati reali (R7, R18): presentare una demo su mock
spacciandola per integrata sarebbe falso. Per questo:

- Il default del client punta all'API vera (`http://localhost:8000`), non al
  mock (swap D17/WP13).
- Le istruzioni demo nel README non menzionano Prism.
- Prism resta disponibile SOLO per sviluppo sul contratto, attivandolo
  esplicitamente con `VITE_API_BASE_URL=http://localhost:4010`.

Abbiamo scartato fixture scritte a mano (divergono dal contratto senza
controllo) e json-server (non legge OpenAPI, non impone le forme né la
sicurezza dichiarata).

## Com'è fatto in pratica

- `frontend/mock/openapi.yaml`: il mirror.
- Comando mock: `npx --yes @stoplight/prism-cli mock -p 4010 frontend/mock/openapi.yaml`.
- `frontend/package.json`: script `demo` che accende Prism + Vite con la base
  puntata al mock (solo per sviluppo contratto).
- Il bundle di produzione è costruito con base vuota e passa da nginx
  ([nginx-proxy.md](nginx-proxy.md)): niente Prism in produzione.

## Limiti e cosa può andare storto

- Prism risponde con gli esempi, non con dati reali: un endpoint può sembrare
  corretto sul mock e sbagliato sui dati veri. Per questo i contract test
  girano contro l'API reale, non solo contro il mock.
- Se dimentichi il `cp` del mirror dopo una modifica al contratto, `diff -q`
  lo segnala: è la rete che protegge l'invariante.
- Confondere mock e demo è l'errore che il brief punisce: la distinzione è
  documentata nel README, nel demo script e nei report.

## Riferimenti

- [ADR 0001: rischio integrazione](../adr/0001-tech-stack.md)
- [Contratto openapi.yaml](contratto-openapi.md)
- [Contract test](contract-tests.md)
- [SPA React](spa-react.md)
- Codice: `frontend/mock/openapi.yaml`, `frontend/package.json`
