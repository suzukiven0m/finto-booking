# Contract test: ogni risposta validata contro lo schema

## Cos'è

I contract test sono verifiche automatiche che confrontano le risposte vere
dell'API con le forme dichiarate in `openapi.yaml`. Per ognuna delle 11
operazioni controllano: la risposta rispetta lo schema (campi, tipi, required),
l'envelope è corretto (`{data, meta}` per le liste, `{error{...}}` per gli
errori), gli esempi pinned coincidono dove previsto, i codici di errore sono
quelli dichiarati. Girano in CI a ogni PR.

## Perché l'abbiamo disegnato così

Il contratto si congela al SAL 1, ma il codice continua a cambiare. Senza un
controllo automatico, dopo il freeze qualcuno potrebbe modificare una risposta
e rompere il contratto senza accorgersene (drift). I contract test sono la
rete che intercetta il drift: se una risposta non rispetta più lo schema, la
build si ferma. È la mitigazione del rischio R4 dell'audit.

Abbiamo scelto una validazione **hand-rolled** (scritta da noi) con `pyyaml`
per leggere lo YAML e `jsonschema` per validare, invece di uno strumento di
fuzzing come schemathesis. Il motivo è concreto: schemathesis genera richieste
casuali, incluse PATCH che scrivono sul database seedato, mutando lo stato
HITL delle richieste ospiti (draft→sent) in modo imprevedibile. Inoltre è una
dipendenza pesante. Una validazione deterministica per operazione copre tutto
il contratto senza effetti collaterali sui dati. Abbiamo scartato anche Dredd
(poco mantenuto) e curl manuali (non in CI, non ripetibili).

## Com'è fatto in pratica

- `backend/tests/test_contract.py`: il file dei contract test.
- Carica `openapi.yaml`, risolve i `$ref` (i riferimenti interni agli schema),
  e per ogni operazione valida la risposta reale contro lo schema dichiarato.
- Gli esempi pinned (baseline summary, reviews/summary per proprietà) sono
  confrontati con i valori attesi, con guardie per dataset completo vs campione
  (un test sul baseline completo salta se nel DB c'è il campione: è previsto,
  dichiarato come skip, non nascosto).
- Dipendenze fissate: `pyyaml`, `jsonschema` con `==`.

Due correzioni correlate (WP8):

- **Job CI frontend aggiunto**: prima la CI non testava il frontend. Ora c'è
  un job con node 22, `npm ci`, vitest, typecheck, build.
- **Step API-tests post-seed**: prima i test schema giravano PRIMA del seed,
  quindi il test baseline-campione API non girava mai in CI (database vuoto).
  Ora uno step dopo il seed lancia i test API sul campione, così quel baseline
  viene davvero verificato.

## Limiti e cosa può andare storto

- La validazione hand-rolled copre le forme e gli esempi che scriviamo noi:
  non esplora combinazioni di input impreviste come farebbe il fuzzing. È un
  compromesso consapevolmente scelto (niente scritture casuali sul DB).
- I contract test validano la FORMA, non la correttezza semantica di ogni
  numero: per i KPI ci sono i test baseline dedicati e la regola "un endpoint
  che non restituisce il baseline è sbagliato".
- Se lo schema cambia senza bump, i test possono passare sul nuovo schema
  mentre il contratto congelato è violato: la disciplina del freeze resta
  umana, i test proteggono dal drift del codice rispetto allo YAML corrente.

## Riferimenti

- [Contratto openapi.yaml](contratto-openapi.md)
- [API FastAPI](api-fastapi.md)
- [CI GitHub Actions](ci-github-actions.md)
- [Dizionario dati §3: baseline](../data-dictionary.md)
- Codice: `backend/tests/test_contract.py`
