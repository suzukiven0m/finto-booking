# GitHub Actions: la rete di sicurezza a ogni PR

## Cos'è

GitHub Actions è il sistema di CI (Continuous Integration) del repository:
a ogni pull request accende un ambiente pulito, installa le dipendenze,
applica le migrazioni, carica i dati di esempio, esegue i test e uno smoke
end-to-end. Se qualcosa si rompe, la PR non è mergiabile. È il giudice
automatico che protegge il contratto e il baseline.

## Perché l'abbiamo disegnato così

La CI è in [ADR 0001](../adr/0001-tech-stack.md). Il laboratorio ha due team
che toccano pezzi diversi: senza una verifica automatica a ogni modifica,
una PR del team web potrebbe rompere un KPI del team dati senza che nessuno
se ne accorga fino alla demo. La CI rende ogni modifica verificata prima del
merge.

Principi di design:

1. **Ambiente pulito e riproducibile.** Un service PostgreSQL vuoto, Python
   3.12, dipendenze fissate con `==`. Senza pin, due ambienti divergono e i
   test passano a uno solo (la lezione del postmortem). Anche i tool di lint
   sono fissati: ruff==0.17.5, isort==9.0.2.
2. **Fail, non skip, quando il database non c'è.** Con `CI=true`, se il DB
   non è raggiungibile i test FALLISCONO invece di saltare. Niente falso
   verde: una CI che salta tutto sembra verde ma non verifica nulla.
3. **Verifiche distruttive su database vuoto.** Round-trip delle migrazioni
   (downgrade base → upgrade head) e inverso a un passo girano sul service
   DB vuoto, mai su dati seedati. Un downgrade sul database con i dati
   distruggerebbe il lavoro.
4. **Ordine corretto dei passi.** Seed del campione, poi D15 `--persist`,
   poi i test. Senza il passo D15 la inbox sarebbe vuota di bozze e i test
   post-D15 fallirebbero; senza i test API dopo il seed, il baseline-campione
   non verrebbe mai verificato (erano due gap che abbiamo corretto).

## Com'è fatto in pratica

`.github/workflows/ci.yml`, due job:

**Job backend:**
- lint (ruff + isort, versioni fissate);
- migrazioni up + `alembic check` (modelli ≡ schema);
- schema test;
- round-trip + downgrade a un passo con verifica NOT NULL;
- seed del campione (bookings, reviews, email, kpi_daily);
- D15 `classify_emails.py --persist`;
- data test;
- API test sul campione (il baseline-campione gira davvero);
- E2E: uvicorn acceso, attesa di boot, `e2e_smoke.py` (login, baseline,
  recensioni, prenotazioni, inbox, PATCH+restore, 401), end-state 800 draft
  e 0 sent, uvicorn spento.

**Job frontend:**
- node 22, `npm ci`, vitest, typecheck, build con
  `VITE_API_BASE_URL=http://localhost:8000` (il bundle punta all'API vera).

C'è anche lo scan di segreti GitGuardian sulle PR. La lezione del compose
(default di sviluppo flaggati): il file di ignore nel repo non è rispettato
dall'integrazione dashboard, e il pattern ri-triggera anche dopo squash; la
strada percorribile è rimuovere il pattern dal contenuto nuovo (vedi
[docker-compose.md](docker-compose.md)).

## Limiti e cosa può andare storto

- La CI verifica sul campione, non sul dataset completo (il CSV completo è
  gitignored, non può stare in CI). I test sul baseline completo saltano in
  CI per progetto: la verifica completa si fa in locale/sidecar e nei loop
  di review.
- La CI non scarica i modelli NLP (~2GB, ore di CPU): sarebbe proibitivo per
  ogni PR. L'eval NLP è riproducibile con un comando documentato, non in CI.
- GitGuardian può bloccare una PR per default di sviluppo pubblicati: è un
  falso positivo noto, gestito con la rimozione del pattern, non con ignore
  silenziosi.

## Riferimenti

- [ADR 0001: stack e CI](../adr/0001-tech-stack.md)
- [Migrazioni Alembic](migrazioni-alembic.md)
- [Contract test](contract-tests.md)
- [Docker Compose](docker-compose.md)
- Codice: `.github/workflows/ci.yml`, `backend/tests/e2e_smoke.py`
