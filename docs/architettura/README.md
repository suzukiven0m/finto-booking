# Architettura: indice dei documenti

Questa cartella contiene un documento per ogni elemento del diagramma
[docs/architettura.d2](../architettura.d2). Ogni documento risponde alla stessa
domanda: **perché l'abbiamo disegnato così?** Non basta dire cosa fa un pezzo:
spieghiamo quale problema risolve, quali alternative abbiamo scartato e quali
vincoli (brief, contratto, decisioni del team) hanno guidato la scelta.

## Come leggere il diagramma

Il diagramma è scritto in [D2](https://d2lang.com), un linguaggio testuale per
diagrammi: si legge come codice e si renderizza in SVG. Nell'SVG ogni elemento
è cliccabile e apre il suo documento.

Per renderizzarlo (serve il CLI `d2`, si installa dalla guida ufficiale):

```bash
# installazione (Linux/Mac, senza sudo, in ~/.local)
curl -fsSL https://d2lang.com/install.sh | sh -s -- --prefix "$HOME/.local"

# render una tantum
d2 docs/architettura.d2 docs/architettura.svg

# anteprima live nel browser mentre modifichi
d2 --watch docs/architettura.d2
```

I colori raggruppano i livelli: blu = browser, verde = servizi che rispondono
alle richieste, giallo = pipeline dati, rosso = contratto e CI, viola = processo.
Le linee tratteggiate sono percorsi facoltativi o di sola lettura (sviluppo con
mock, valutazione che legge il gold).

## Gli elementi e i loro documenti

| Elemento nel diagramma | Documento | In una frase |
|---|---|---|
| SPA React (4 schede) | [spa-react.md](spa-react.md) | l'interfaccia che il cliente vede, con le disclosure sempre in vista |
| nginx :8080 | [nginx-proxy.md](nginx-proxy.md) | serve la dashboard e fa da ponte verso l'API, tutto sulla stessa origine |
| FastAPI :8000 | [api-fastapi.md](api-fastapi.md) | le 11 operazioni del contratto, con envelope ed errori uniformi |
| JWT + 3 ruoli | [auth-jwt-ruoli.md](auth-jwt-ruoli.md) | chi sei e cosa puoi fare: gettone firmato, matrice dei ruoli |
| PostgreSQL 16 | [database-postgres.md](database-postgres.md) | le 5 tabelle, i vincoli, la colonna generata, niente FK asserite |
| Alembic 0001-0005 | [migrazioni-alembic.md](migrazioni-alembic.md) | lo schema come passi numerati, riproducibili e reversibili |
| Docker Compose | [docker-compose.md](docker-compose.md) | tre servizi con un comando, immagini senza dati |
| ETL | [etl-pipeline.md](etl-pipeline.md) | dai CSV grezzi alle tabelle pulite, con la deduplica giusta |
| Classificatore email D15 | [classificatore-email.md](classificatore-email.md) | bozze proposte, mai inviate da sole: approva una persona |
| NLP recensioni D14 | [nlp-recensioni.md](nlp-recensioni.md) | sentiment e topic al momento della query, niente tabelle derivate |
| Valutazione e anti-leakage | [valutazione-anti-leakage.md](valutazione-anti-leakage.md) | numeri onesti: weak labels, gold separato, F1 riproducibile |
| openapi.yaml | [contratto-openapi.md](contratto-openapi.md) | l'accordo tra i due team, congelato a v1.0.0 |
| Mirror + Prism | [mock-prism.md](mock-prism.md) | lavorare sul contratto senza backend, senza spacciare il mock per demo |
| Contract test | [contract-tests.md](contract-tests.md) | ogni risposta validata contro lo schema, in CI |
| GitHub Actions | [ci-github-actions.md](ci-github-actions.md) | la rete di sicurezza: lint, migrazioni, seed, test, E2E |
| Processo (SAL, ADR, ledger) | [processo-governance.md](processo-governance.md) | le decisioni scritte e le cose che solo le persone possono fare |

## Da dove partire

Se sei nuovo: [README](../../README.md) per il quadro generale e i passi di
avvio. La guida dettagliata `docs/getting-started.md` (se presente nel tuo
branch) spiega ogni passaggio per esteso. Se vuoi capire una scelta tecnica:
il documento dell'elemento qui sopra, poi l'ADR citato dentro.

I documenti seguono tutti la stessa struttura: cos'è, perché così, com'è fatto
in pratica, limiti e cosa può andare storto, riferimenti. Sono scritti per un
team misto: ogni termine tecnico è spiegato alla prima occorrenza, perché i
compagni di Web Solutions Architect e quelli di Data Analyst partono da
competenze diverse.
