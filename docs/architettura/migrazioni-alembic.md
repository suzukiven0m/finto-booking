# Alembic: lo schema come passi numerati

## Cos'è

Alembic è lo strumento che gestisce le migrazioni del database. Una migrazione
è un passo numerato che modifica lo schema: crea una tabella, aggiunge una
colonna, mette un vincolo. Invece di scrivere lo schema "a mano" ogni volta,
scriviamo passi incrementali (0001, 0002, ...) che Alembic applica in ordine.
`alembic upgrade head` porta il database all'ultimo passo; `downgrade` torna
indietro.

## Perché l'abbiamo disegnato così

Alembic è lo strumento naturale dell'ecosistema SQLAlchemy (la scelta di
[ADR 0001](../adr/0001-tech-stack.md)). I motivi:

- **Riproducibilità**: un database vuoto diventa lo schema v1 con un comando,
  identico per tutti e in CI. Niente "sul mio computer funziona".
- **Reversibilità**: ogni passo ha una sua inversa (downgrade). Possiamo verificare
  che tornare indietro ripristini davvero lo stato precedente, non solo che
  "non dia errore".
- **Drift detector**: `alembic check` confronta i modelli SQLAlchemy con lo
  schema reale e segnala se divergono. In CI è un guardrail: se qualcuno
  cambia un modello senza migrazione, la build si ferma.

La disciplina più importante: **le migrazioni già mergiate non si editano
mai**. Dopo il freeze dello schema, una modifica è un passo NUOVO (0006, ...),
non una riscrittura di 0003. Questo perché il database di chi ha già applicato
i passi non può "riavvolgere" una migrazione cambiata sotto di lui. È la stessa
logica del contratto congelato.

La 0005 è l'esempio giusto: aggiunge `guest_requests.urgency` (varchar(10),
nullable, CHECK low/medium/high) PRIMA del freeze, perché la valutazione D15
usa `true_urgency` e l'output predetto aveva bisogno di una casa nello schema
(decisione S8). Farlo dopo il freeze avrebbe richiesto un contract-bump.

## Com'è fatto in pratica

- `backend/alembic/versions/0001_properties_bookings.py` ... `0005_guest_requests_urgency.py`.
- `backend/alembic/env.py`: legge `DATABASE_URL` dalla config e applica i passi.
- `backend/alembic.ini`: configurazione (script_location, prepend_sys_path).

I test di verifica (in CI e nel loop di review):

1. **Round-trip**: `downgrade base` poi `upgrade head` su un database vuoto.
   Dimostra che i passi si applicano e si annullano senza errori.
2. **Inverso a un passo**: `downgrade 0004` e controllo che le colonne tornate
   NOT NULL lo siano davvero (non basta che il comando non fallisca).
3. **alembic check**: modelli ≡ schema.

Questi giri si fanno su un database SCRATCH (creato e distrutto), mai sul
database seedato: un downgrade sul database con i dati distruggerebbe il
lavoro. In CI il service database è vuoto, quindi è sicuro.

## Limiti e cosa può andare storto

- Alembic autogenera le migrazioni dai modelli, ma la generazione non è
  perfetta (vincoli, nomi, default): ogni migrazione va letta e corretta a
  mano. Il check finale è la rete, non l'autogenerate.
- Se applichi i passi su un database e poi editi una migrazione già applicata,
  Alembic non se ne accorge (il numero di versione nella tabella alembic_version è lo
  stesso): lo schema reale diverge silenziosamente. Per questo la regola
  "non editare il mergiato" è disciplina umana, rinforzata dalla CI su DB vuoto.
- La colonna generata `nights` non va mai in una COPY: la calcola il database.
  Includerla in un caricamento dà errore.

## Riferimenti

- [ADR 0001: stack](../adr/0001-tech-stack.md)
- [Database PostgreSQL](database-postgres.md)
- [Dizionario dati: decisioni pre-freeze](../data-dictionary.md)
- [CI GitHub Actions](ci-github-actions.md)
- Codice: `backend/alembic/`
