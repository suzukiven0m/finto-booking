# Come contribuire

Questa pagina spiega come lavoriamo sul repository: il flusso delle modifiche,
i test, le regole di stile. Siamo un team misto di due corsi, quindi cerchiamo
di tenere tutto semplice e verificabile.

## Il flusso di una modifica

Non si lavora mai direttamente su `master`. Ogni modifica passa da un branch
e da una pull request (PR), e viene reviewata da qualcuno che NON l'ha scritta.

1. **Crea un branch** da `master` aggiornato:
   ```bash
   git checkout master && git pull
   git checkout -b fix/wpX-descrizione   # oppure docs/..., feat/...
   ```
   Naming: `fix/` per correzioni, `feat/` per funzionalità, `docs/` per
   documentazione. Per i work package della remediation: `fix/wpX-slug`.
2. **Fai la modifica più piccola che risolve il problema.** Niente astrazioni
   "per dopo", niente dipendenze nuove senza una riga di giustificazione.
3. **Aggiorna i documenti che la modifica invalida**, nello stesso branch
   (dizionario, ERD, contratto, ADR, README a seconda dei casi).
4. **Esegui i test** (sotto) e incolla l'output reale nella PR.
5. **Apri la PR** e chiedi la review. Il reviewer è un contesto fresco che non
   ha scritto il codice: controlla correttezza, invarianti, sicurezza, test,
   scope, documenti.
6. **Fix → re-review** (massimo 3 passate). Se una PR è bloccata, si scrive il
   blocker e si passa oltre, non si abbassa l'asticella per chiuderla.
7. **Merge** solo con CI verde e sign-off del reviewer registrato.

## I test

Dalla root, con il venv del backend attivo (vedi [getting-started](docs/getting-started.md)):

```bash
# backend
cd backend && python -m pytest && cd ..
# data
PYTHONPATH=backend:data python -m pytest data/tests
# frontend
cd frontend && npm test -- --run && npm run typecheck && npm run build && cd ..
# lint
backend/.venv/bin/ruff check backend/ data/
backend/.venv/bin/isort --check-only backend/ data/
```

Attenzione: su questa macchina la VPN blocca le porte pubblicate dai container.
I test che toccano il database girano in un **sidecar** (un container che
condivide la rete di postgres), non dall'host verso `localhost:5432`. Il comando
esatto è in [getting-started](docs/getting-started.md) e nei record di review.

Gli skip si dichiarano come skip: un test che salta perché nel DB c'è il
campione invece del completo è previsto, non è un test nascosto. In CI, con
`CI=true`, un database non raggiungibile fa FALLIRE i test, non saltare.

## Regole di stile

- **Documentazione in italiano**, voce studentesca ("abbiamo scelto", "ci siamo
  accorti"), termini tecnici spiegati alla prima occorrenza. Niente tono da
  consulente, niente filler.
- **Niente trattini lunghi** (em dash U+2014, en dash U+2013) nei documenti: usa
  punti, virgole, due punti, parentesi. Il check è automatico in CI di review.
- **Commit in stile conventional**: `feat(api): ...`, `fix(data): ...`,
  `docs: ...`, `style: ...`. Messaggio chiaro, body se serve.
- **Numeri e baseline sono asserzioni**: se un test KPI non torna, il codice è
  sbagliato, non il baseline. Non si aggiusta il baseline per fare verde.

## Il contratto è congelato

`openapi.yaml` è congelato a `v1.0.0` dal SAL 1. Non si modifica senza la procedura
di contract-bump (nuova ADR, bump di `info.version`, migrazione se serve,
mirror risincronizzato, nota al cliente). Le migrazioni già mergiate non si
editano mai: una modifica allo schema è un passo nuovo.

## Azioni umane

Alcune cose non le fa un agent: firmare il catalogo KPI, inviare lo stato al
cliente, pagare le chiavi LLM, creare account di deploy, presentare. Stanno
nel [registro delle azioni umane](docs/reviews/human-actions.md): gli agent
preparano gli artefatti, le persone eseguono e chiudono le righe.

## Struttura del repo

Vedi il [README](README.md) per il layout e la [guida per iniziare](docs/getting-started.md)
per l'avvio. L'architettura è spiegata elemento per elemento in
[docs/architettura/](docs/architettura/README.md).