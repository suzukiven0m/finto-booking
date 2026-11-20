# PostgreSQL: le cinque tabelle e i loro vincoli

## Cos'è

PostgreSQL è il database relazionale dove vivono tutti i dati strutturati.
"Relazionale" significa che i dati stanno in tabelle (righe e colonne) collegate
tra loro da chiavi. Noi usiamo la versione 16, dentro un container Docker.
Lo schema (la forma delle tabelle) è alla versione v1, congelato al SAL 1.

## Perché l'abbiamo disegnato così

La scelta di un solo PostgreSQL per tutto è in [ADR 0002](../adr/0002-data-storage.md).
Il brief distingue dati strutturati (prenotazioni) e non strutturati (testi di
recensioni ed email) ma non prescrive una tecnologia. Un solo motore che tiene
sia le tabelle numeriche sia i testi (colonne TEXT) è la soluzione più semplice
che il team sapesse governare: niente sincronizzazione tra due database, niente
competenze extra.

Abbiamo scartato SQLite (non gestisce bene scritture concorrenti e ruoli),
MongoDB (il team ragiona in SQL e i KPI sono join e aggregazioni naturali per
un relazionale) e un database separato per i testi (sovradimensionato). Le
feature "option A" di ADR 0002 (zona raw JSONB, full-text search italiana con
tsvector, pgvector) erano descrizione dell'opzione, non impegni: non le abbiamo
costruite (finding S10), e una FTS italiana su un corpus inglese sarebbe stata
sbagliata comunque.

Le cinque tabelle e le scelte che contano:

- **properties**: le due strutture fittizie. La capacità (190 e 230 camere)
  sta in `room_count`, non in un file di costanti: è un dato della struttura,
  e i KPI la leggono da lì (correzione WP4 a un riferimento obsoleto).
- **bookings**: una riga del CSV, cancellata o no. `nights` è una colonna
  GENERATA dal database (somma dei due campi notte): non la scriviamo mai nel
  loader, così non può divergere. Niente CHECK di intervallo sui numerici
  (finding S9): teniamo le righe grezze d'archivio così come sono (1 adr
  negativo, 1.778 adr zero, 385 adults zero); il filtro baseline le esclude
  dai KPI. Mettere CHECK ora avrebbe respinto righe che il team ha scelto di
  conservare, e clippare i valori cambierebbe il baseline.
- **reviews**: recensioni TripAdvisor. **Nessuna foreign key verso bookings**:
  il legame è asserito a livello di proprietà ([ADR 0003](../adr/0003-data-sources.md)),
  non fattuale. Una FK vera dichiarerebbe un join che non esiste (una recensione
  del 2012 non è l'ospite di una prenotazione del 2016). `property_id` è NOT
  NULL (deviazione documentata dallo sketch ADR): una recensione senza
  proprietà non è collegabile a nessun KPI.
- **guest_requests**: le 800 email sintetiche. `category`, `draft_reply`,
  `urgency` restano NULL finché il classificatore D15 non le produce. CHECK
  sui vocabolari chiusi: stato `new/draft/sent`, urgenza `low/medium/high`
  (colonna aggiunta con la migrazione 0005, pre-freeze, decisione S8).
- **kpi_daily**: una riga per hotel e giorno, giorni di soggiorno. `occupancy`
  è `numeric(5,4)`, rapporto 0-1 (mai percentuale): la precisione a 4 decimali
  è la correzione 0004 (con 2 si quantizzava a punti percentuali interi).

Tutte le foreign key sono indicizzate (un test lo verifica): senza indice,
ogni join e ogni controllo di integrità sarebbe una scansione completa.

## Com'è fatto in pratica

- `backend/app/models.py`: le classi SQLAlchemy che descrivono le tabelle.
- `backend/alembic/versions/0001-0005`: i passi che costruiscono lo schema.
- `docs/erd.md`: il diagramma entità-relazione.
- `docs/data-dictionary.md` §2: ogni campo, tipo, nullabilità, regola.

## Limiti e cosa può andare storto

- La capacità è assunta (ricavata dai picchi osservati), non misurata:
  occupazione e RevPAR non sono misure reali. È una disclosure vincolante,
  non un difetto nascosto.
- Niente CHECK di intervallo significa che il database accetta righe "sporche":
  la pulizia è responsabilità della ETL e del filtro baseline, non dello schema.
  È una scelta consapevole (conservare l'archivio grezzo).
- Il legame recensioni-prenotazioni resta asserito: nessuna query deve mai
  fare un join per singola prenotazione tra le due tabelle.

## Riferimenti

- [ADR 0002: persistenza](../adr/0002-data-storage.md)
- [ADR 0003: sorgenti dati](../adr/0003-data-sources.md)
- [Dizionario dati §1 e §2](../data-dictionary.md)
- [ERD](../erd.md)
- [Migrazioni Alembic](migrazioni-alembic.md)
- Codice: `backend/app/models.py`, `backend/alembic/versions/`
