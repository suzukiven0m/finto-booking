# ADR 0002 — Architettura di persistenza dei dati

- **Stato:** Proposto (in attesa di voto del team)
- **Data:** 2026-11-06
- **Decisori:** 3 Web Solutions Architect + 3 Data Analyst / AI Specialist
- **Correlati:** `docs/plan.md`, `docs/adr/0001-tech-stack.md`, `docs/project-bearings.pdf`

## Contesto

Il brief (Caso 1 — Buby Travel) distingue due categorie di dati:

- **dati strutturati:** prenotazioni, occupazione, tariffe, stagionalità, canali di vendita;
- **dati non strutturati:** recensioni online, email di richiesta informazioni, messaggi e reclami degli ospiti.

Da questa distinzione nasce una domanda ricorrente: *è necessario utilizzare due database — PostgreSQL per i dati strutturati e MongoDB per quelli non strutturati?*

## Chiarimento del requisito

La parola "non strutturato" descrive **la forma del dato in ingresso alla pipeline**, non il formato di persistenza richiesto dall'applicazione.

Il brief chiede al team dati di:

- elaborare email e testi (classificazione, estrazione di informazioni, sintesi);
- consegnare dataset puliti, data dictionary e output nel formato concordato.

Ciò che l'applicazione interroga è quindi l'**output strutturato** di quella elaborazione: etichette di sentiment, topic, entità estratte, sintesi, embedding e KPI. Il testo grezzo resta un semplice campo `TEXT`.

Il brief, inoltre, **non prescrive alcuna tecnologia di persistenza**: la sezione "Tecnologie" parla genericamente di "database". La scelta è quindi nostra e va motivata.

## Opzioni considerate

### A. Solo PostgreSQL, con due zone logiche

- **Zona raw:** tabelle con colonne `JSONB` / `TEXT` per i payload grezzi (recensioni, email, messaggi).
- **Zona curated:** tabelle relazionali per prenotazioni, KPI ed entità estratte; `pgvector` per gli embedding; full-text search tramite `tsvector` con configurazione `italian`.
- Un solo motore, un solo backup, una sola catena di migrazioni, un solo deploy.

### B. PostgreSQL + MongoDB (polyglot persistence)

- PostgreSQL per i dati relazionali.
- MongoDB per i documenti grezzi (recensioni, email) e per i campi variabili.
- Richiede doppio driver, doppia pipeline di migrazione, sincronizzazione tra i due store e un secondo servizio da distribuire e monitorare.

### C. PostgreSQL + object storage (MinIO / S3)

- PostgreSQL come database di servizio.
- Object storage per i file grezzi (export, PDF, allegati).
- Variante più "pulita" della separazione fisica, ma aggiunge un servizio infrastrutturale.

## Matrice di valutazione

Punteggi da 1 (scarso) a 5 (ottimo).

| Criterio | Peso | A. Solo PostgreSQL | B. PostgreSQL + MongoDB | C. PostgreSQL + Object Storage |
|---|---:|---:|---:|---:|
| Copertura dei requisiti | 25% | 5 | 5 | 5 |
| Semplicità operativa | 20% | 5 | 2 | 3 |
| Rischio di integrazione entro il 4-11 dic | 20% | 5 | 2 | 3 |
| Aderenza al contratto dati (schema congelato al SAL 1) | 15% | 5 | 3 | 4 |
| Costo di apprendimento per il team | 10% | 4 | 3 | 3 |
| Valore per la valutazione / documentazione architetturale | 10% | 4 | 5 | 5 |
| **Punteggio ponderato** | **100%** | **4,80** | **3,30** | **3,85** |

## Quando MongoDB sarebbe giustificato

Va valutato con onestà, perché una di queste condizioni potrebbe applicarsi:

1. **Il corso richiede esplicitamente l'uso di più tecnologie di persistenza.** È l'unica motivazione forte: verificare con il docente prima del voto.
2. **Documenti con schema realmente eterogeneo e nessun contratto dati** — in contraddizione con l'obiettivo del SAL 1, che è congelare lo schema.
3. **Volumi di scrittura molto elevati o necessità di scalabilità orizzontale** — non il nostro caso.
4. **Il team dati rifiuta la normalizzazione e vuole caricare JSON grezzi** — anche in questo caso `JSONB` è più semplice di un secondo server.

## Raccomandazione

**Opzione A — Solo PostgreSQL, con due zone logiche.** Motivazioni:

- copre tutti i requisiti: relazionale, JSON, full-text e vettori;
- elimina un intero servizio da gestire, proteggere, migrare e monitorare;
- riduce il rischio di integrazione nella fase finale (4-11 dicembre);
- rende coerente la separazione strutturato/non strutturato a livello architetturale, senza polyglot persistence.

Se il team desidera una separazione fisica più marcata, l'**Opzione C** è la variante consigliata. L'**Opzione B** va scelta solo se il docente la richiede o se esiste un caso d'uso concreto che la giustifichi.

## Decisione

> **Da completare con il voto del team il ______.**
>
> Opzione scelta: ______
>
> Voti: WSA ___ / Data ___
>
> Dissenso / condizioni: ______

## Conseguenze

- **Positive:** un solo motore, meno superficie operativa, integrazione più semplice, contratto dati più facile da congelare.
- **Negative:** nessuna flessibilità "schema-on-write"; i campi variabili vanno gestiti con `JSONB` e documentati nel data dictionary.
- **Seguito:** se viene scelta l'Opzione B, redigere un ADR successivo che definisca chi possiede MongoDB, come avviene la sincronizzazione e quale sia la fonte di verità.
