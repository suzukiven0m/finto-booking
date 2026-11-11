# ADR 0001 — Stack dell'applicazione web

- **Stato:** Accettato (voto del team 2026-11-11)
- **Data:** 2026-11-06
- **Decisori:** 3 Web Solutions Architect + 3 Data Analyst / AI Specialist
- **Correlati:** `docs/plan.md`, `docs/project-bearings.pdf`

## Contesto

Buby Travel (Caso 1 — Turismo) richiede un'applicazione web funzionante con database, API e interfaccia (dashboard, ricerca, visualizzazioni) che utilizzi i **dati reali** preparati dal team dati, oltre ad almeno una componente NLP/AI e a un assistente per le richieste degli ospiti.

Lo stack deve servire due pubblici contemporaneamente:

1. **WSA** — costruire e mantenere backend, frontend, autenticazione, deploy.
2. **Data/AI** — produrre dataset puliti, logica KPI, modelli NLP, previsioni e un assistente LLM.

Il rischio di integrazione dominante è la giuntura tra il lavoro Python del team dati (notebook, pandas, scikit-learn, librerie NLP, SDK LLM) e il runtime dell'applicazione. Il contratto si congela il **2026-11-20 (SAL 1)**, quindi lo stack deve essere produttivo entro ~2 settimane.

## Opzioni considerate

### A. FastAPI + React (SPA TypeScript)

- Backend Python (FastAPI, SQLAlchemy, Pydantic), PostgreSQL, React + Vite + Tailwind + Recharts.
- Gli artefatti dati/NLP girano nello stesso linguaggio e nello stesso ecosistema dell'API.

### B. NestJS + React

- TypeScript end-to-end (NestJS, TypeORM/Prisma, PostgreSQL).
- Ottima ergonomia web; l'AI/NLP richiede un servizio Python o il porting in TypeScript di ogni modello.

### C. Next.js full-stack

- Un unico framework per UI + route API, TypeScript, PostgreSQL.
- Veloce da avviare; i confini server/client e l'integrazione della pipeline dati aggiungono complessità per un team diviso tra due competenze.

## Valutazione

I pesi riflettono i criteri di valutazione del brief (integrazione con dati reali, qualità dell'architettura, collaborazione).

| Criterio | Peso | A. FastAPI + React | B. NestJS + React | C. Next.js |
|---|---:|---:|---:|---:|
| Integrazione dati/AI (Python nativo) | 30% | 5 | 2 | 3 |
| Velocità e familiarità WSA | 20% | 4 | 5 | 4 |
| Chiarezza architetturale / separazione delle responsabilità | 15% | 5 | 5 | 3 |
| Semplicità di deploy e operations | 10% | 4 | 4 | 4 |
| Ecosistema, documentazione, pool di competenze | 10% | 5 | 4 | 5 |
| Aderenza alla valutazione del corso (backend + frontend + AI) | 15% | 5 | 4 | 4 |
| **Punteggio ponderato** | **100%** | **4,70** | **3,75** | **3,65** |

## Raccomandazione

**Opzione A — FastAPI + React.** Motivazioni:

- il team dati vive già in Python; modelli, notebook e codice LLM si integrano senza livello di traduzione;
- separazione netta: SPA React ↔ REST/JSON ↔ FastAPI ↔ PostgreSQL. Ogni workstream possiede un confine;
- il mock server generato da OpenAPI sblocca i WSA dal giorno 3, indipendentemente dai dati reali;
- rischio di integrazione più basso rispetto al congelamento del 20 novembre.

Compromesso accettato: i WSA scrivono Python sul backend invece di TypeScript. Mitigato dalla superficie ridotta di FastAPI e dalla type safety di Pydantic.

## Baseline proposta (se viene scelta A)

| Livello | Scelta |
|---|---|
| Backend | FastAPI, SQLAlchemy 2, Alembic, Pydantic v2 |
| Database | PostgreSQL 16 (+ `pgvector` solo se viene realizzato l'assistente RAG) |
| Frontend | React 18 + TypeScript + Vite + Tailwind + shadcn/ui + Recharts |
| Autenticazione | JWT, ruoli: `admin`, `manager`, `property_manager` |
| Infrastruttura | Docker Compose; GitHub Actions (lint + test); deploy su VM singola o Render/Fly |
| Repository | Monorepo: `/backend`, `/frontend`, `/data`, `/infra`, `/docs` |

## Decisione

> **Deciso dal team il 2026-11-11.**
>
> Opzione scelta: **A — FastAPI + React (SPA TypeScript)**
>
> Voti: WSA 3 / Data 3 (unanime)
>
> Dissenso / condizioni: nessuno

## Conseguenze

- **Positive:** un solo linguaggio tra dati e backend; sviluppo guidato dal contratto; demo efficace.
- **Negative:** i WSA devono avere sufficiente familiarità con Python; frontend e backend sono deploy separati salvo containerizzazione congiunta.
- **Seguito:** se il voto sceglie B o C, registrare in un nuovo ADR il design del bridge per le componenti AI Python prima della fine dello Sprint 1.
