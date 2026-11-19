# Playbook — build the dataset solo (B6 + D3 + D4 + D8 + D9 + kpi_daily)

- **Written:** 2026-11-16, for WSA-3 (Facu). Team unresponsive; DA-1/DA-2/DA-3 deliverables are ownerless in practice.
- **Scope:** everything under `data/` that SAL 1 and the MVP need: bookings on master, ETL + seed with the exact baseline, `kpi_daily`, TripAdvisor mapping + sample + loader, synthetic emails + gold file, tests + CI.
- **NOT scope:** OpenAPI (D5), frontend (D10), NLP models (D14/D15). Those stay with their owners; this playbook only makes their input exist.
- **Every number in §1 was recomputed from the actual CSV today** (not copied from docs). Two doc claims turned out wrong — corrections are flagged. You can trust §1 over any other document.

---

## 0. Rules of engagement (read once, then work)

1. **Work on a branch** `data-solo`, PR into master, CI green before merge. You are now doing other people's graded work — the paper trail (§8) is what keeps it legitimate and keeps the collaboration grade alive.
2. **The baseline is the contract.** €22,976,960.13 is not a target, it is an assertion. Every script ends by checking it. If your numbers differ, your code is wrong — do not "adjust" the baseline.
3. **Decisions get written down the moment you make them**, in `docs/data-dictionary.md` (you're effectively the contract owner now). Undocumented solo decisions are how December explodes.
4. **Never commit:** the full CSV, the 952 MB pickle, anything with real PII. `.gitignore` already enforces `data/raw/*` except `sample_*.csv` — **name every committed sample `sample_*.csv`** or it will be silently ignored.
5. **Schema is frozen-in-4-days.** One schema change is recommended below (occupancy precision, §4.3) — do it *before* Fri Nov 20 or never. Everything else works with the schema as it stands.
6. Time budget: **~2 focused days**. Order matters: bookings first (unblocks the KPI story for SAL 1), TripAdvisor second (reputation story), emails last (needed Nov 17 per plan, consumed Dec 3).

---

## 1. Verified facts (recomputed 2026-11-16 from `origin/fabio:Datasets/hotel_bookings.csv`)

| Fact | Value | Note |
|---|---|---|
| Raw rows / columns | 119,390 / 32 | original Kaggle columns, no enrichment |
| Exact dedup (all 32 cols) | **87,396** rows (31,994 removed) | cancel rate post-dedup **27.49%** |
| Valid (`is_canceled=0, nights>0, adr>0`) | **61,777** | |
| Room-nights | **218,410** | |
| Realized revenue | **€22,976,960.13** | matches docs to the cent |
| ADR | **105.20** | revenue / room-nights |
| Per hotel (post-dedup) | City 53,428 · Resort 33,968 | |
| `children` literal `NA` | 4 rows | **pandas reads them as NaN by default** — no special code needed, just don't pass `keep_default_na=False` |
| `NULL` strings in `agent`/`company`/`country` | 16,340 / 112,593 / 488 | **also auto-NaN by default** |
| Zero-night rows (post-dedup) | 651 | docs' 715 was the raw count |
| `adults=0` (post-dedup) | 385 | docs' 403 was raw. **Keep them** — the baseline filter does not exclude them; dropping rows breaks the baseline |
| `adr <= 0` (post-dedup) | 1,779 | incl. one **-6.38, not canceled** → excluded by `adr>0` |
| The 5,400 ADR typo | **is_canceled=1** | 📌 **Correction to delivery-plan §10:** clipping to [0,1000] is *moot* — the row is canceled and never enters a KPI. Verified: clipped and unclipped revenue are identical. **Store `adr` as-is; do not clip.** Record this decision in the dictionary |

TripAdvisor corpus (`jniimi/tripadvisor-review-rating`), verified on `data1000.pkl` today:

| Fact | Value |
|---|---|
| Columns (16) | `hotel_id, user_id, title, text, overall, cleanliness, value, location, rooms, sleep_quality, stay_year, post_date, freq, review, char, lang` |
| `text` → our `body` | rename on load; `title` stays |
| `post_date` | **already a pandas Timestamp** — no parsing needed |
| scores | float 1.0–5.0; nullable in our schema anyway |
| `lang` | `__label__en` (fits `varchar(20)`) |
| avg review length | ~795 chars → 📌 **Correction to ADR 0003:** the 20k sample CSV will be **~16 MB, not ~3 MB**. Fine for git (<100 MB); just don't be surprised |
| `data1000.pkl` | 1,000 rows from 1,000 *different* hotels — good for smoke-testing the loader, **useless for choosing the top-2 hotels**. You need the full `data.pkl` for the mapping |

📌 **Note 2026-11-19 (audit §7):** the full `data.pkl` is quoted as 952 MB in
this playbook (§0 rule 4, §5.1); the local copy observed on 2026-11-19 is
**368 MB** — provenance unverified (possibly a filtered subset). Neither number
is asserted as canonical. What CI uses is the committed reload-from-CSV path
(`data/raw/sample_tripadvisor.csv` → `data/etl/load_reviews.py`), and it passes.
The ~16 MB sample estimate above was superseded by the executed artifact:
1,638 rows, ~1.6 MB (dictionary «Decisione TripAdvisor»).

Property IDs (fixed by migration `0001`, verified by test): **1 = Buby Lago** (Resort Hotel, 190 rooms) · **2 = Buby Montagna** (City Hotel, 230 rooms).

---

## 2. Phase 0 — get the data (15 min) [B6]

```bash
cd ~/code/finto-booking
git checkout -b data-solo master

# full CSV, local only (gitignored). This is the file the whole baseline depends on.
mkdir -p data/raw data/eval data/etl data/tests
git show origin/fabio:Datasets/hotel_bookings.csv > data/raw/hotel_bookings.csv
wc -l data/raw/hotel_bookings.csv        # 119391 (header + 119390)

# committed sample: 5,000 deduped rows, deterministic. Regenerates byte-identical.
uv run --with pandas python - <<'PY'
import pandas as pd
df = pd.read_csv('data/raw/hotel_bookings.csv').drop_duplicates()
df.sample(5000, random_state=42).sort_index().to_csv('data/raw/sample_hotel_bookings.csv', index=False)
PY
git add data/raw/sample_hotel_bookings.csv   # whitelisted by .gitignore (sample_*.csv)
```

Upload the full CSV to the client drive (policy: full files live there, README says so). Then `data/requirements.txt`: `pandas` + `psycopg[binary]` — **pin whatever version you actually run** (`uv pip freeze | grep -i pandas`), same discipline as `backend/requirements.txt`.

**Pinned sample baseline** (computed today from exactly the file above — your CI test asserts these):

| Metric | Sample value |
|---|---:|
| rows | 5,000 |
| valid bookings | 3,564 |
| room-nights | 12,696 |
| revenue | **1,350,503.84** |
| cancellation rate | 0.2696 |

---

## 3. Phase 1 — bookings ETL + seed (half day) [D3 + D4]

One script, `data/etl/load_bookings.py`. Idempotent (TRUNCATE + reload). Uses psycopg COPY — 87k rows load in seconds. **`nights` is a generated column: it must NOT appear in the column list** (Postgres rejects the whole COPY otherwise).

```python
"""CSV -> bookings. Dedup on the 32 original columns, then load. Idempotent."""
import sys
import pandas as pd
import psycopg
from app.config import DATABASE_URL  # run with backend/.venv + PYTHONPATH=backend

MONTHS = {m: i for i, m in enumerate(
    ["January","February","March","April","May","June","July",
     "August","September","October","November","December"], 1)}

COLS = ["property_id","arrival_date","lead_time","stays_in_weekend_nights",
        "stays_in_week_nights","adults","children","babies","country","customer_type",
        "is_repeated_guest","previous_cancellations","previous_bookings_not_canceled",
        "market_segment","distribution_channel","agent","company","meal",
        "reserved_room_type","assigned_room_type","deposit_type","booking_changes",
        "days_in_waiting_list","required_car_parking_spaces","total_of_special_requests",
        "adr","is_canceled","reservation_status_date"]  # 28 cols: no id, no nights

def clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)              # default NA handling: 'NA' and 'NULL' -> NaN (verified)
    df = df.drop_duplicates()           # 32 original columns. NEVER dedup after adding columns.
    df["children"] = df.children.fillna(0).astype(int)
    df["babies"] = df.babies.fillna(0).astype(int)
    df["property_id"] = df.hotel.map({"Resort Hotel": 1, "City Hotel": 2})
    df["arrival_date"] = pd.to_datetime(dict(
        year=df.arrival_date_year,
        month=df.arrival_date_month.map(MONTHS),
        day=df.arrival_date_day_of_month)).dt.date
    df["reservation_status_date"] = pd.to_datetime(df.reservation_status_date).dt.date
    df["is_canceled"] = df.is_canceled.astype(bool)
    df["is_repeated_guest"] = df.is_repeated_guest.astype(bool)
    for c in ("agent", "company"):      # NaN -> None, else psycopg sends 'nan'
        df[c] = df[c].astype("Int64")
    return df[COLS]

def load(df: pd.DataFrame) -> None:
    url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE bookings RESTART IDENTITY")
        with cur.copy(f"COPY bookings ({','.join(COLS)}) FROM STDIN") as cp:
            for row in df.itertuples(index=False, name=None):
                cp.write_row([None if pd.isna(v) else v for v in row])
        conn.commit()

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/hotel_bookings.csv"
    df = clean(path)
    load(df)
    print(f"loaded {len(df)} rows from {path}")
```

Run + verify against the live DB:

```bash
docker compose -f infra/docker-compose.yml up -d
cd backend && alembic upgrade head && cd ..
PYTHONPATH=backend backend/.venv/bin/python data/etl/load_bookings.py            # full
docker exec buby-postgres psql -U buby -d buby -tc "
WITH v AS (SELECT * FROM bookings
           WHERE NOT is_canceled AND nights > 0 AND adr > 0)
SELECT (SELECT count(*) FROM bookings)                          AS rows,      -- 87396
       (SELECT count(*) FROM v)                                 AS valid,     -- 61777
       (SELECT sum(nights) FROM v)                              AS room_nights,-- 218410
       (SELECT sum(adr*nights) FROM v)                          AS revenue,   -- 22976960.13
       (SELECT round(sum(adr*nights)/sum(nights),2) FROM v)     AS adr;       -- 105.20
"
```

All five numbers match §1 → D3/D4 done. If they don't: 99% it's the dedup (did you dedup before mapping?), the month map, or `nights` sneaking into COLS.

Then reload with the sample and check the sample baseline too:

```bash
PYTHONPATH=backend backend/.venv/bin/python data/etl/load_bookings.py data/raw/sample_hotel_bookings.csv
# rows=5000 valid=3564 room_nights=12696 revenue=1350503.84
```

**Dictionary updates (write them now):** no ADR clipping (canceled typo row, §1); `adults=0` kept; dedup on 32 original columns; pandas default NA conventions.

---

## 4. Phase 2 — `kpi_daily` (2 h) [D7's data half]

### 4.1 Pin the ambiguous rules FIRST (5 min, in the dictionary)

The dictionary's `revenue = adr × nights` is a per-booking rule on a per-day table — ambiguous (status review P1-2). Pin this, verbatim:

> `kpi_daily` counts stay-days of bookings with `is_canceled=0 AND nights>0 AND adr>0` (same filter as the baseline; zero-ADR stays are excluded from occupancy too — declared assumption). For each such booking, each day `arrival_date … arrival_date+nights-1` contributes 1 room-night and `adr` revenue. `occupancy = room_nights/room_count` (0–1), `adr = revenue/room_nights` (NULL on zero-activity days), `revenue_per_available_room = revenue/room_count`. Rows exist for every day of the property's observed range, including zero days. Invariant: `Σ kpi_daily.revenue = 22,976,960.13` and `Σ room_nights = 218,410` on the full dataset.

### 4.2 Build script `data/etl/build_kpi_daily.py`

```python
"""bookings -> kpi_daily. Reads the DB, never the CSV. Idempotent."""
import numpy as np
import pandas as pd
import psycopg
from sqlalchemy import create_engine
from app.config import DATABASE_URL

eng = create_engine(DATABASE_URL)
b = pd.read_sql("""SELECT property_id, arrival_date, nights, adr FROM bookings
                   WHERE NOT is_canceled AND nights > 0 AND adr > 0""", eng)
rooms = pd.read_sql("SELECT id, room_count FROM properties", eng).set_index("id").room_count

b = b.reset_index(drop=True)
stay = b.loc[b.index.repeat(b.nights)].copy()
stay["date"] = stay.arrival_date + pd.to_timedelta(
    stay.groupby(level=0).cumcount(), unit="D")
daily = stay.groupby(["property_id", "date"]).agg(
    room_nights=("adr", "size"), revenue=("adr", "sum")).reset_index()

# full date range per property, zero days included
parts = []
for pid, g in daily.groupby("property_id"):
    idx = pd.date_range(g.date.min(), g.date.max(), freq="D")
    g = g.set_index("date").reindex(idx, fill_value=0).rename_axis("date").reset_index()
    g["property_id"] = pid
    parts.append(g)
daily = pd.concat(parts, ignore_index=True)
daily["occupancy"] = daily.room_nights / daily.property_id.map(rooms)
daily["adr"] = np.where(daily.room_nights > 0,
                        daily.revenue / daily.room_nights.replace(0, np.nan), np.nan)
daily["revenue_per_available_room"] = daily.revenue / daily.property_id.map(rooms)
daily["revenue"] = daily.revenue.round(2)

url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
with psycopg.connect(url) as conn, conn.cursor() as cur:
    cur.execute("TRUNCATE kpi_daily RESTART IDENTITY")
    with cur.copy("COPY kpi_daily (property_id,date,room_nights,revenue,occupancy,"
                  "adr,revenue_per_available_room) FROM STDIN") as cp:
        for r in daily.itertuples(index=False):
            cp.write_row([r.property_id, r.date.date(), int(r.room_nights),
                          float(r.revenue), float(r.occupancy),
                          None if pd.isna(r.adr) else round(float(r.adr), 2),
                          round(float(r.revenue_per_available_room), 2)])
    conn.commit()
print(f"kpi_daily: {len(daily)} rows, revenue {daily.revenue.sum():.2f}, "
      f"room_nights {int(daily.room_nights.sum())}")
# full dataset must print: revenue 22976960.13, room_nights 218410
```

### 4.3 The one schema change to make before Friday (10 min)

`occupancy Numeric(5,2)` stores a 0–1 ratio with 2 decimals = **1-percentage-point quantization** (1 room at Buby Lago = 0.53%). Averages computed from stored values drift. Fix now while migrations are still cheap (status review P1-3):

- `backend/app/models.py`: `occupancy = Column(Numeric(5, 4), nullable=False)`
- new migration `0004_occupancy_precision.py`: `op.alter_column("kpi_daily", "occupancy", type_=sa.Numeric(5,4), existing_type=sa.Numeric(5,2))` (downgrade reverses).
- `alembic check` + pytest + round-trip, update dictionary + ERD. **After Nov 20 this same fix costs a contract bump — do it now or accept 1% granularity forever.**

---

## 5. Phase 3 — TripAdvisor (half day + download) [D8 + ADR 0003 step 1]

### 5.1 Choose the two hotels — ONCE, then never again (ADR 0003 §1)

```bash
uv run --with huggingface_hub --with pandas python - <<'PY'
from huggingface_hub import hf_hub_download
import pandas as pd
p = hf_hub_download("jniimi/tripadvisor-review-rating", repo_type="dataset",
                    filename="data.pkl")          # 952 MB, ~3-5 GB RAM to load. NOT committed.
df = pd.read_pickle(p)
en = df[df.lang == "__label__en"]
top = en.hotel_id.value_counts().head(10)
print(top)                                        # write these counts into the dictionary
PY
```

Decision rule (deterministic, asserted — write it in the dictionary and on the SAL 1 slide):
**largest hotel → Buby Montagna (property 2), second largest → Buby Lago (property 1).**
The link is asserted, not factual — that's ADR 0003's whole deal. Record the chosen IDs and their review counts. **After SAL 1 these IDs are immutable.**

### 5.2 Sample + loader `data/etl/load_reviews.py`

Balanced 10k + 10k, `random_state=42`. If a chosen hotel has <10k English reviews, take all of them and **pin the actual N in the dictionary** — do not silently substitute another hotel.

```python
"""TripAdvisor pickle -> sample CSV -> reviews. Run once; the CSV is the artifact."""
import pandas as pd
import psycopg
from app.config import DATABASE_URL

TA = {1: <ID_LAGO>, 2: <ID_MONTAGNA>}   # fill from 5.1, then never change
DIMS = ["overall","cleanliness","value","location","rooms","sleep_quality"]

def make_sample(pkl_path: str) -> pd.DataFrame:
    df = pd.read_pickle(pkl_path)
    df = df[df.lang == "__label__en"]
    parts = [df[df.hotel_id == ta].sample(min(10_000, len(df[df.hotel_id == ta])),
                                          random_state=42) for ta in TA.values()]
    s = pd.concat(parts)
    s = s.rename(columns={"text": "body"})[
        ["hotel_id","post_date","stay_year","title","body","lang"] + DIMS]
    s.to_csv("data/raw/sample_tripadvisor.csv", index=False)   # sample_* = git-whitelisted
    return s

def load(s: pd.DataFrame) -> None:
    s = s.copy()
    s["property_id"] = s.hotel_id.map({ta: pid for pid, ta in TA.items()})
    url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE reviews RESTART IDENTITY")
        with cur.copy("COPY reviews (property_id,ta_hotel_id,post_date,stay_year,"
                      "overall,cleanliness,value,location,rooms,sleep_quality,"
                      "title,body,lang) FROM STDIN") as cp:
            for r in s.itertuples(index=False):
                cp.write_row([r.property_id, r.hotel_id, r.post_date.date(),
                              int(r.stay_year),
                              *[None if pd.isna(getattr(r, d)) else float(getattr(r, d))
                                for d in DIMS],
                              r.title, r.body, r.lang])
        for pid, ta in TA.items():
            cur.execute("UPDATE properties SET ta_hotel_id=%s WHERE id=%s", (ta, pid))
        conn.commit()

if __name__ == "__main__":
    import sys
    s = make_sample(sys.argv[1]) if len(sys.argv) > 1 else \
        pd.read_csv("data/raw/sample_tripadvisor.csv", parse_dates=["post_date"])
    load(s)
    print(f"reviews loaded: {len(s)}")
```

Notes:
- Develop against `data1000.pkl` first (fast), but it has 1 review per hotel — the loader path works, the mapping/sample path needs the full pickle.
- The committed CSV will be **~16 MB** (§1 correction). Acceptable. Commit it: `git add data/raw/sample_tripadvisor.csv`.
- Reload-from-CSV path must work without the pickle — that's what a fresh clone and CI use.
- Verify: `SELECT property_id, count(*), round(avg(overall),2) FROM reviews GROUP BY 1;` → two rows, ~10k each, averages in 1–5. `SELECT id, ta_hotel_id FROM properties;` → both set.
- Dictionary: chosen IDs + counts, the assignment rule, actual N per hotel, "asserted link" restated. English-only corpus vs Italian demo: record the decision too (accept English, or ABSITA later — ADR 0003 names both).

---

## 6. Phase 4 — synthetic emails (half day) [D9]

800 emails, 6 categories, **Italian** (demo language), template + slot generator, `random_state=42`. The enriched-CSV postmortem (`personal-notes/2026-11-11`) is your design constraint: **25 distinct texts made evaluation meaningless — a lookup table scored 100%.** Aim for ≥8 templates per category × slot variation (names, dates, room types, property, party size, typos/politeness registers) so near-duplicates are rare.

Structure of `data/etl/gen_emails.py`:

```python
import random, csv, datetime as dt
import psycopg
from app.config import DATABASE_URL

rng = random.Random(42)
CATS = ["availability","cancellation","complaint","special_request","billing","info"]
N_PER_CAT = [134, 133, 133, 133, 133, 134]   # = 800
NAMES = ["Mario Rossi","Giulia Bianchi", ...]   # obviously fictional, ≥30 names
# TEMPLATES[cat] = list of ≥8 Italian templates with {name},{date},{property},{rooms},...
# each template carries a fixed urgency: low/medium/high
# e.g. complaint: "Buongiorno, sono {name}, camera {room} dal {date}. {problem}.
#                  Chiedo un rimborso o almeno delle scuse formali."

rows, gold = [], []
for cat, n in zip(CATS, N_PER_CAT):
    for i in range(n):
        t = rng.choice(TEMPLATES[cat])
        body = t.text.format(name=rng.choice(NAMES), date=..., property=rng.choice(
            ["Buby Lago","Buby Montagna"]), ...)
        pid = rng.choice([1, 2])
        received = dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc) + \
                   dt.timedelta(days=rng.randrange(75), hours=rng.randrange(24))
        rows.append((pid, received, body))
        gold.append((len(rows), cat, t.urgency))   # id matches insert order after TRUNCATE

# gold ONLY to data/eval/email_gold.csv — NEVER into the database
with open("data/eval/email_gold.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["id","true_category","true_urgency"]); w.writerows(gold)

url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
with psycopg.connect(url) as conn, conn.cursor() as cur:
    cur.execute("TRUNCATE guest_requests RESTART IDENTITY")
    with cur.copy("COPY guest_requests (property_id,received_at,body) FROM STDIN") as cp:
        for r in rows: cp.write_row(r)
    conn.commit()
```

Hard rules (ADR 0003 §6, dictionary anti-leakage):
- DB gets `property_id, received_at, body` only. `category` and `draft_reply` stay **NULL** — they are the classifier's/assistant's output (D15), `status` defaults to `new`.
- `true_category`/`true_urgency` live **only** in `data/eval/email_gold.csv`. The pipeline never reads that file. Gold ids align with `guest_requests.id` because both start from TRUNCATE RESTART IDENTITY in the same run — if you ever reload emails, regenerate gold in the same run.
- All names/addresses fictional (GDPR O1: no real PII anywhere). Commit the generator + gold file (reproducible with seed 42); the DB rows are derivable.
- Verify: `SELECT count(*) FROM guest_requests;` → 800; `SELECT count(*) FROM guest_requests WHERE category IS NOT NULL;` → 0. Gold: 800 rows, 6 categories.

---

## 7. Phase 5 — tests + CI + smoke (2 h)

### 7.1 `data/tests/test_baseline.py` (the R5 mitigation, finally real)

```python
import os
import pytest
import pandas as pd
from etl.load_bookings import clean   # or import via path; keep it boring

SAMPLE = dict(rows=5000, valid=3564, room_nights=12696, revenue=1350503.84)
FULL   = dict(rows=87396, valid=61777, room_nights=218410, revenue=22976960.13)

def metrics(df):
    df = df.copy()
    df["nights"] = df.stays_in_weekend_nights + df.stays_in_week_nights
    v = df[(df.is_canceled == 0) & (df.nights > 0) & (df.adr > 0)]
    return dict(rows=len(df), valid=len(v), room_nights=int(v.nights.sum()),
                revenue=round(float((v.adr * v.nights).sum()), 2))

def test_sample_baseline():   # always runs, incl. CI — the sample is committed
    assert metrics(clean("data/raw/sample_hotel_bookings.csv")) == SAMPLE

@pytest.mark.skipif(not os.path.exists("data/raw/hotel_bookings.csv"),
                    reason="full CSV local-only (client drive)")
def test_full_baseline():     # runs on your machine; never a false green in CI
    assert metrics(clean("data/raw/hotel_bookings.csv")) == FULL
```

(The sample test is always executable, so the skip can never hide everything — the T-1 lesson.)

### 7.2 CI — extend `.github/workflows/ci.yml`

Add to the existing `backend` job (it already has Postgres + migrations):

```yaml
      - name: Data deps
        run: pip install -r data/requirements.txt
      - name: Seed sample + KPIs
        run: |
          PYTHONPATH=backend python data/etl/load_bookings.py data/raw/sample_hotel_bookings.csv
          PYTHONPATH=backend python data/etl/build_kpi_daily.py
      - name: Data tests
        run: pytest -q data/tests
```

Reviews/emails loaders are exercised locally; wiring them into CI is optional (the TA sample is committed, so it *can* run in CI — add it once Phase 3 is merged, same pattern).

### 7.3 The Wednesday smoke test, solo edition

```bash
docker compose -f infra/docker-compose.yml up -d
cd backend && alembic upgrade head && cd ..
PYTHONPATH=backend backend/.venv/bin/python data/etl/load_bookings.py
PYTHONPATH=backend backend/.venv/bin/python data/etl/build_kpi_daily.py
PYTHONPATH=backend backend/.venv/bin/python data/etl/load_reviews.py
PYTHONPATH=backend backend/.venv/bin/python data/etl/gen_emails.py
# then the §3 SQL: 87396 / 61777 / 218410 / 22976960.13 / 105.20
# and: SELECT count(*) FROM reviews;   -- ~20000
#      SELECT count(*) FROM guest_requests;  -- 800
```

One command sequence, real data, end to end. That is the ritual the plan wanted, done by one person.

---

## 8. Paper trail (30 min, non-negotiable)

You are absorbing three people's deliverables. Protect the work and the grade:

1. **Today, in writing (team channel + email):** "DA-1/DA-2/DA-3 deliverables unresponsive as of Nov 16; I'm executing B6/D3/D4/D8/D9 per `docs/playbooks/solo-dataset.md` on branch `data-solo`. Objections/reclaim by <date>. Decisions I make solo are logged in the data dictionary." Silence after that is consent, documented.
2. **Client status (O5, Friday):** one paragraph — dataset substitution (ADR 0003 E), baseline reproduced, what lands by SAL 1. Copy in `docs/` (the status review flagged O1–O5 as evidence-less; start fixing that).
3. **Dictionary = decision log:** every §-flagged decision (no clipping, adults=0 kept, kpi_daily rules, TA ids + counts, sample Ns, occupancy precision, English corpus) gets a line the day you make it.
4. **PR description:** list which deliverables this closes (B6, D3, D4, D8, D9 + D7 data half) and link the verification output. Merge with CI green. Update `docs/delivery-plan.md` statuses so the next review sees reality.
5. Reassign formally at the next sync even if nobody answers: the plan's cut list (§11) still protects D12/D14/D15/D17/D18 — your work feeds exactly those. D5 (OpenAPI) and D10 (frontend) remain the real SAL 1 blockers; **this playbook does not fix them — escalate them separately.**

---

## 9. Do-not list

- **Don't** dedup after adding/renaming columns (34-col dedup = wrong baseline, the enriched-file trap).
- **Don't** write `nights` in any INSERT/COPY (generated column).
- **Don't** clip ADR, drop `adults=0`, or fold No-Show into cancellations — each silently moves a headline number.
- **Don't** put `true_category`/`true_urgency` in the DB, or `sentiment`/`topics` in `reviews`.
- **Don't** change the two `ta_hotel_id`s after SAL 1. Ever.
- **Don't** commit the full CSV, the pickle, or `mock-db/` (the enriched 34-col file is superseded — leave it local, note it in the dictionary).
- **Don't** edit merged migrations after Friday; new revisions only.
- **Don't** present occupancy/RevPAR as measured, or the review↔booking link as factual — footnote and slide, every time.

---

## 10. Budget & order

| Phase | Deliverable | Time | Unblocks |
|---|---|---|---|
| 0 | B6 sample + local full CSV | 15 min | everything |
| 1 | D3 + D4 bookings + baseline | 3–4 h | KPI story for SAL 1, D12 |
| 2 | kpi_daily + precision fix | 2 h | D7/D12, occupancy/RevPAR dashboards |
| 3 | D8 mapping + sample + loader | 3 h + download | reputation story for SAL 1, D13/D14 |
| 4 | D9 emails + gold | 3–4 h | D15 (Dec 3) — do last if time presses |
| 5 | tests + CI + smoke | 2 h | R4/R5 mitigations, Wednesday ritual |
| 8 | paper trail | 30 min | the grade |

**~2 focused days.** If you only get one day before SAL 1: Phases 0→1→2→3 (skip emails, they're consumed in December) and §8.1–8.2. Walk into Friday with the baseline SQL output and the two TripAdvisor averages on a slide — that is "sample of real data flowing through ETL v0", the SAL 1 DoD item that is currently fiction.