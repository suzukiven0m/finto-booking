## Cosa cambia

<!-- Descrivi la modifica in una o due frasi. -->

## Perché

<!-- Il problema che risolve o il requisito che soddisfa. Riferimenti a finding/ADR se pertinenti. -->

## Come è stato verificato

<!-- Incolla l'output REALE dei test, non "i test passano". Gli skip si dichiarano come skip. -->

- [ ] Backend: `python -m pytest` (output incollato)
- [ ] Data: `pytest data/tests` (output incollato)
- [ ] Frontend: `npm test -- --run` + typecheck + build (se toccato)
- [ ] Lint: ruff + isort puliti
- [ ] Sidecar usato per i test DB (VPN blocca le porte host)

## Checklist

- [ ] Branch dedicato, niente commit diretti su master
- [ ] Documenti invalidati dalla modifica aggiornati nello stesso branch
- [ ] Niente trattini lunghi (em/en dash) nei documenti
- [ ] Contratto congelato rispettato (nessuna modifica a openapi.yaml senza bump)
- [ ] Migrazioni già mergiate non editate
- [ ] Baseline non aggiustato per fare verde
- [ ] Review richiesta a chi NON ha scritto il codice