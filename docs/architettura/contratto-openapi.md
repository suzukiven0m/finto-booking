# openapi.yaml: il contratto tra i due team

## Cos'è

`openapi.yaml` è il contratto dati del progetto, scritto in OpenAPI 3.0.3 (un
formato standard per descrivere API REST). Elenca le 11 operazioni, i parametri,
le forme delle risposte (gli "schema"), gli esempi e le regole di autenticazione.
È la "single source of truth": frontend e backend devono rispettarlo, e i test
verificano che lo facciano. Il brief lo chiede esplicitamente: "contratto dati:
schema, formato dell'API, esempi di risposta".

## Perché l'abbiamo disegnato così

Il laboratorio mette due team a lavorare in parallelo: i WSA costruiscono
l'app, i DA preparano i dati. Senza un accordo scritto, ognuno indovina il
formato dell'altro e la settimana di integrazione diventa una settimana di
riscrittura. Il contratto è l'accordo che permette di lavorare separati e
integrare dopo.

Per questo il contratto si **congela** al SAL 1 (20 novembre 2026, cliente
presente), versione `v1.0.0`, con un tag git. Da quel momento, qualsiasi
modifica segue il **contract-bump protocol**: nuova ADR che spiega perché si
riapre il freeze, bump di `info.version`, migrazione dedicata se serve,
risincronizzazione del mock, nota al cliente in `docs/client-comms.md`. Niente
modifiche silenziose.

Prima del freeze abbiamo corretto i difetti trovati dall'audit (era il momento
giusto, dopo sarebbe costato un bump davanti al cliente):

- **S1**: il testo di `occupancy_avg` diceva "media dei rapporti giornalieri"
  (0.6534) ma l'esempio pinned era pooled (0.6558). Abbiamo corretto il testo
  alla formula pooled, che coincide con esempio e implementazione.
- **S2**: summary (coorte di arrivo) e daily (giorni di soggiorno) differiscono
  ai bordi dell'intervallo. Abbiamo fissato entrambe le semantiche nelle
  descrizioni e aggiunto una footnote nella UI: la differenza è voluta.
- **S3**: aggregazione daily con `property_id` null = una riga per data, somme
  delle due proprietà, capacità combinata 420.
- **WP8a**: gli esempi delle cinque dimensioni in `reviews/summary` erano
  scritti a mano e non coincidevano con nessuna statistica del corpus reale
  (verificato riga per riga contro il sorgente). Li abbiamo corretti ai valori
  eseguiti, prima del freeze.
- **WP7a**: la matrice dei ruoli (decisa dall'operatore) è scritta nelle
  descrizioni, così l'implementazione D11 non inventa semantica.

Gli esempi pinned sono asserzioni di baseline: un endpoint che restituisce
numeri diversi è sbagliato, non è l'esempio a dover cambiare. Il lint Redocly
dà 0 errori e 4 warning inerenti (server localhost, niente licenza, una rotta
senza 4xx naturale).

Abbiamo scartato uno schema code-first (generato dal codice): drifting facile,
e i DA non leggerebbero un contratto espresso in TypeScript. Abbiamo scartato
gRPC/protobuf: il team ragiona in REST e la demo è nel browser.

## Com'è fatto in pratica

- `openapi.yaml` nella root: il contratto canonico.
- `frontend/mock/openapi.yaml`: mirror byte-identical (vedi
  [mock-prism.md](mock-prism.md)).
- `docs/api-contract.md`: le convenzioni in prosa (envelope, paginazione,
  errori, auth, disclosure).
- I contract test (vedi [contract-tests.md](contract-tests.md)) validano ogni
  risposta contro gli schema.

## Limiti e cosa può andare storto

- Il contratto è in inglese (è il formato macchina standard): la documentazione
  in italiano lo spiega, ma lo YAML resta inglese perché congelato. Tradurlo
  sarebbe una modifica di contratto.
- Un freeze non impedisce le modifiche: le incanala. La disciplina è umana
  (nessuno edita lo YAML senza bump), rinforzata dai test e dal mirror.
- Gli esempi illustrativi (channels, seasonality) sono dichiarati tali: i
  totali sono pinned, i valori per segmento/mese no. Non vanno confusi con
  gli esempi pinned del baseline.

## Riferimenti

- [Contratto API: convenzioni](../api-contract.md)
- [Dizionario dati §3: regole e baseline](../data-dictionary.md)
- [Mock e Prism](mock-prism.md)
- [Contract test](contract-tests.md)
- [Processo e governance](processo-governance.md)
- Codice: `openapi.yaml`
