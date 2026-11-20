# ETL: dai CSV grezzi alle tabelle pulite

## Cos'è

ETL sta per Extract, Transform, Load: leggere dati grezzi, pulirli e
trasformarli, caricarli nel database. Nel nostro progetto sono script Python
in `data/etl/`, ognuno con un compito preciso. Sono il lavoro del team dati
(DA): senza di loro le tabelle sarebbero vuote o sporche, e i KPI sbagliati.

## Perché l'abbiamo disegnato così

Abbiamo scelto script standalone (niente framework come Airflow o dbt) perché
il laboratorio ha una pipeline lineare e riproducibile, non un flusso da
orchestrare. Ogni script si lancia con `PYTHONPATH=backend python data/etl/...`,
legge la configurazione del database dalla stessa `app.config` del backend
(una sola fonte di verità per la connessione) ed è idempotente: rilanciarlo
non duplica i dati. Questo li rende eseguibili sia a mano sia in CI.

Le decisioni di pulizia sono registrate nel [dizionario dati](../data-dictionary.md)
(assunzioni 4 e 5) e nel [playbook solo-dataset](../playbooks/solo-dataset.md).
Le più importanti:

- **Deduplica sulle 32 colonne ORIGINALI, prima di aggiungere o rinominare
  colonne.** Sembra un dettaglio, è la trappola principale: il file "arricchito"
  a 34 colonne (con testo recensione ed email per riga) dà un baseline DIVERSO
  (103,05 euro/notte e 25,99 milioni invece di 105,20 e 22,98). Deduplicare
  dopo aver aggiunto colonne cambia il risultato. Riferimento: colonne originali.
- **NA di pandas default**: i letterali "NA" e "NULL" diventano NaN
  automaticamente; children/babies NaN → 0; agent/company NaN → NULL nel
  database (non la stringa "nan").
- **adults=0 si tengono** (385 righe post-dedup): il filtro baseline non le
  esclude, toglierlo rompe il baseline.
- **Nessun clipping di adr**: il typo 5400,0 è su una riga cancellata, non
  entra mai in un KPI; clippare o no dà lo stesso ricavo (verificato). I valori
  si salvano così come sono.

## Com'è fatto in pratica

Cinque script, in ordine di dipendenza:

1. `load_bookings.py`: legge il CSV (campione o completo), deduplica, pulisce,
   carica `bookings`. La colonna `nights` è generata dal database, non scritta.
2. `load_reviews.py`: carica le recensioni TripAdvisor. Il mapping proprietà
   usa l'`offering_id` recuperato da `review.txt` (nella distribuzione HF la
   colonna `hotel_id` è in realtà l'id della recensione, non dell'hotel: senza
   questo join il mapping sarebbe impossibile). I due id scelti (93618, 2079052)
   sono immutabili dopo il SAL 1.
3. `gen_emails.py`: genera le 800 email sintetiche (italiano, 6 categorie,
   seed 42, almeno 8 template per categoria × slot). Il database riceve solo
   `property_id, received_at, body`: categoria e bozze restano NULL finché D15
   non le produce. Nomi inventati (GDPR). Perché tanti template? Il postmortem
   del dataset arricchito aveva 25 testi distinti: la valutazione diventava
   una lookup table al 100%. Varietà = valutazione onesta.
4. `build_kpi_daily.py`: espande ogni prenotazione valida nei suoi giorni di
   soggiorno (da arrivo ad arrivo+nights-1), una riga per hotel e giorno,
   inclusi i giorni a zero. Stesso filtro del baseline. Invariante verificato:
   Σ ricavo = 22.976.960,13 euro, Σ room-night = 218.410.
5. `classify_emails.py --persist`: il classificatore D15 (vedi
   [classificatore-email.md](classificatore-email.md)).

Il CSV completo (119.390 righe lorde) è gitignored: resta in locale/drive.
Nel repo c'è solo il campione da 5.000 righe, così un clone fresco seeda in CI
senza download enormi. I due baseline (campione e completo) sono entrambi
documentati e testati.

## Limiti e cosa può andare storto

- Se carichi il campione, i numeri della dashboard sono quelli del campione
  (3.564 valide, 1.350.503,84 euro), non del completo. Non è un bug: è scritto
  nel dizionario e nel demo script.
- La deduplica sulle colonne sbagliate dà un baseline diverso senza dare
  errore: è il tipo di sbaglio più insidioso, per questo è un'assunzione
  vincolante e un test.
- Gli script dipendono dall'ordine (bookings prima di kpi_daily, emails prima
  di classify). Lanciarli fuori ordine dà tabelle vuote o errori di chiave.

## Riferimenti

- [Dizionario dati: assunzioni 4 e 5, baseline](../data-dictionary.md)
- [ADR 0003: sorgenti dati](../adr/0003-data-sources.md)
- [Playbook solo-dataset](../playbooks/solo-dataset.md)
- [Database PostgreSQL](database-postgres.md)
- [Classificatore email](classificatore-email.md)
- Codice: `data/etl/`
