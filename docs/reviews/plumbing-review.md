# Agent loop review — branch `plumbing`

| | |
|---|---|
| Branch | `plumbing` (da `master` dopo il merge di #4) |
| Commit | `bfdbb5e` lavoro → `0e4135c` fix pass 2 → `cc0b943` fix pass 3 |
| Scopo | chiudere i B-/T- di `docs/reviews/pr-4-schema-v1.md` dopo il merge della PR #4 |
| Metodo | 3 passate di un reviewer agent indipendente: review → fix → ri-review |
| Verifica | eseguita dal supervisore su Postgres 16 reale (il reviewer è read-only, non ha shell) |

## 0. Come funziona il loop

Il reviewer agent legge il diff e i documenti, non modifica file. Il supervisore
esegue i comandi, applica i fix e rilancia. Ogni passata produce finding con
`file:line`; un finding si chiude solo con evidenza eseguita o con una modifica
verificabile. Le passate successive controllano solo i fix e i difetti nuovi.

| Passata | Finding | Esito |
|---|---|---|
| 1 | R1 + O1…O5 | R1 bloccante, il resto opzionale |
| 2 | O4 wording, commento CI | confermati risolti R1/O1/O2/O3/O5 |
| 3 | 4 P2 (CI, README) | nessun P0/P1, chiuso con note |

## 1. Cosa è stato fatto (i B-/T- della review)

| ID | Cosa chiedeva | Dove è finito |
|---|---|---|
| B-1 | `reviews` alla forma ADR 0003 §3 | migrazione `0003`, `models.py`, test |
| B-2 | `properties.ta_hotel_id` | `0003` + `models.py` |
| B-3 | ERD | `docs/erd.md` (Mermaid) |
| T-1 | `pytest.skip` verde in CI | `conftest.py` fallisce se `CI` è impostata |
| T-2 | indici sulle FK | `0003`, più il test `test_ogni_foreign_key_ha_un_indice` |
| T-3 | `nights` generata, non scritta | commento nel modello + dizionario dei dati |
| T-4 | unità di `occupancy` | commento `rapporto 0-1` + dizionario §3 |
| T-5 | dipendenze non pinnate | `requirements.txt` con `==` |
| T-6 | `DATABASE_URL` vs `.env` | `config.py` deriva da `POSTGRES_*`; README dice quale fonte vince |

In più, per il freeze: `docs/data-dictionary.md` (regole KPI, assunzioni,
baseline) e `.github/workflows/ci.yml` (lint, migrazioni, `alembic check`,
round-trip, downgrade di un gradino).

## 2. Finding delle passate e come sono stati chiusi

### Passata 1 — R1 (bloccante)

Il `downgrade` di `0003` riportava `overall` → `score` come `Numeric(4,2)` ma
**senza `nullable=False`**, mentre `0002` aveva creato `score` NOT NULL. Dopo
`alembic downgrade 0002`, `reviews.score` restava nullable: il downgrade non era
un inverso fedele. Non lo intercettava il round-trip della CI, perché `0002`
droppa la tabella.

Fix: `nullable=False` sull'`alter_column` di `0003` (passata 2 verificata).

### Passata 2 — O4 e commento CI

- Il README lasciava intendere che il backend legga `.env`: non lo fa. Riscritto:
  `docker compose` legge `.env`, il backend legge l'ambiente del processo.
- Il commento dello step CI "Downgrade one step" diceva di provare il ripristino
  dello stato di `0002`, ma si limitava a rieseguire l'upgrade. Ora **asserisce**
  `reviews.score NOT NULL` dopo `downgrade 0002`.

### Passata 3 — 4 P2, nessun bloccante

- La CI asseriva solo `score`; `0003` ripristina NOT NULL anche su `text` e
  `language`. Ora il controllo è su tutte e tre.
- README: "scrivi `DATABASE_URL`" era ambiguo su dove; chiarito che va
  nell'ambiente, non nel `.env`.
- README riga di layout diceva che `infra/` contiene anche CI e Dockerfile: non è
  vero. Corretto, la CI sta in `.github/workflows/`.
- `docs/reviews/pr-4-schema-v1.md` §6 teneva i B-/T- aperti: aggiunta una nota
  che punta a questo documento. Le righe restano com'erano perché fotografano
  la PR #4 al momento della review.

## 3. Verifica eseguita (non solo letta)

Postgres 16 reale, `DATABASE_URL=postgresql+psycopg://buby:buby@127.0.0.1:5432/buby`,
venv `backend/.venv` con le versioni di `requirements.txt`:

```bash
cd backend
export DATABASE_URL=postgresql+psycopg://buby:buby@127.0.0.1:5432/buby

alembic upgrade head          # 0001 → 0002 → 0003
alembic check                 # "No new upgrade operations detected"
pytest -q                     # 11 passed
alembic downgrade base
alembic upgrade head          # round-trip
alembic downgrade 0002        # il gradino che il round-trip non copre
# score / text / language devono essere NOT NULL → asserito, ok
alembic upgrade head
```

Lint: `ruff check backend/` e `isort --check-only backend/`, entrambi verdi con la
config unica in `pyproject.toml`.

Il reviewer agent non ha shell: le sue passate sono **statiche** (lettura del
diff e dei documenti). L'evidenza eseguita è quella sopra, prodotta dal
supervisore. La distinzione è deliberata: il reviewer non deve poter dichiarare
"eseguito" ciò che non ha eseguito.

## 4. Cosa resta aperto

| Cosa | Perché non è chiuso qui |
|---|---|
| `infra/docker-compose.yml` senza servizio backend | il backend non è containerizzato; il README ora lo dice invece di prometterlo |
| `data/raw/` vuoto (B6) | blocco di DA-1, non di questo branch: senza campione non si fa seed |
| `backend/lavoro_svolto.md` ancora in `backend/` | O-5 della review, cosmetico |
| `alembic check` non copre la simmetria del downgrade | coperta dallo step CI dedicato, non da Alembic |

## 5. Verdetto

**OK con note.** B-1/B-2/B-3 e T-1…T-6 chiusi; R1 corretto ed eseguito; nessun
P0/P1 residuo. I quattro P2 della passata 3 sono chiusi. I punti del §4 sono
fuori dal perimetro di questo branch o pre-esistenti.
