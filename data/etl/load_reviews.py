"""TripAdvisor -> reviews. La CSV committata e' l'artefatto; il pickle si usa una volta sola.

Perche' serve anche `review.txt` (Li et al. 2013, non committato):
la distribuzione HF `jniimi/tripadvisor-review-rating` non ha l'id dell'hotel.
Nel loro `process.ipynb` la colonna `hotel_id` e' presa da `t['id']`, cioe' l'id
della RECENSIONE (201.295 valori tutti diversi su 201.295 righe). L'id vero
dell'hotel e' `offering_id`, che esiste solo in `review.txt` ed e' stato perso
nel preprocessing. Qui lo si recupera unendo su `id` (risolve il 100% delle
righe, verificato il 2026-11-16) e si tengono le due strutture con piu'
recensioni: e' la regola di ADR 0003 §1, finalmente eseguibile.

    offering 2079052 -> Buby Montagna (property 2), 876 recensioni
    offering  93618  -> Buby Lago     (property 1), 762 recensioni

Ricostruire la CSV (una volta, con i due file raw locali; accetta anche la .zip):

    PYTHONPATH=backend backend/.venv/bin/python data/etl/load_reviews.py \
        data/raw/data.pkl data/raw/review.txt.zip

Caricare dalla CSV committata (fresh clone, CI, nessun pickle):

    PYTHONPATH=backend backend/.venv/bin/python data/etl/load_reviews.py
"""

import json
import sys
import zipfile

import pandas as pd
import psycopg

from app.config import DATABASE_URL

# ta_hotel_id scelti una volta (ADR 0003 §1): dopo il SAL 1 non si cambiano piu'
TA = {1: 93618, 2: 2079052}

SAMPLE = "data/raw/sample_tripadvisor.csv"
DIMS = ["overall", "cleanliness", "value", "location", "rooms", "sleep_quality"]
COLS = ["ta_hotel_id", "post_date", "stay_year", "title", "body", "lang", "review_id"] + DIMS


def make_sample(pkl_path: str, review_txt: str) -> pd.DataFrame:
    """pickle HF + review.txt -> CSV committata. Deterministica."""
    df = pd.read_pickle(pkl_path)
    # hotel_id e' l'id della recensione: serve solo a ritrovare offering_id
    wanted = set(df.hotel_id.astype("int64").tolist())
    id2off = {}
    try:
        with (
            zipfile.ZipFile(review_txt).open("review.txt")
            if review_txt.endswith(".zip")
            else open(review_txt, "rb") as fh
        ):
            for line in fh:
                d = json.loads(line)
                if d["id"] in wanted:
                    id2off[d["id"]] = d["offering_id"]
    except (FileNotFoundError, zipfile.BadZipFile, json.JSONDecodeError) as e:
        raise SystemExit(
            f"review.txt non leggibile ({e}): serve il corpus raw locale (playbook §5)"
        ) from e
    df["ta_hotel_id"] = df.hotel_id.map(id2off)
    df["review_id"] = df.hotel_id
    missing = int(df.ta_hotel_id.isna().sum())

    s = df.loc[df.ta_hotel_id.isin(TA.values())].rename(columns={"text": "body"})
    s = s.sort_values(["ta_hotel_id", "post_date", "review_id"])
    s.to_csv(SAMPLE, index=False, columns=COLS)
    for pid, ta in TA.items():
        print(f"  property {pid}: ta_hotel_id {ta}, {int((s.ta_hotel_id == ta).sum())} recensioni")
    print(f"  righe senza offering_id risolto: {missing}")
    return s[COLS]


def load(s: pd.DataFrame) -> None:
    s = s.copy()
    s["property_id"] = s.ta_hotel_id.map({ta: pid for pid, ta in TA.items()})
    s = s.sort_values(["property_id", "post_date", "review_id"])
    # ordine esplicito = ordine del COPY: l'unpack posizionale sotto e' cosi'
    # corretto a prescindere dall'ordine colonne in ingresso (CSV o pickle)
    order = ["property_id", "ta_hotel_id", "post_date", "stay_year", *DIMS, "title", "body", "lang"]
    s = s.reindex(columns=order)
    url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE reviews RESTART IDENTITY")
        with cur.copy(
            "COPY reviews (property_id,ta_hotel_id,post_date,stay_year,"
            "overall,cleanliness,value,location,rooms,sleep_quality,"
            "title,body,lang) FROM STDIN"
        ) as cp:
            for row in s.itertuples(index=False, name=None):
                property_id, ta_hotel_id, post_date, stay_year, *scores, title, body, lang = row
                cp.write_row(
                    [
                        int(property_id),
                        int(ta_hotel_id),
                        post_date.date(),
                        None if pd.isna(stay_year) else int(stay_year),
                        *[None if pd.isna(v) else float(v) for v in scores],
                        None if pd.isna(title) else title,
                        None if pd.isna(body) else body,
                        None if pd.isna(lang) else lang,
                    ]
                )
        for pid, ta in TA.items():
            cur.execute("UPDATE properties SET ta_hotel_id=%s WHERE id=%s", (ta, pid))
        conn.commit()


if __name__ == "__main__":
    if len(sys.argv) == 3:
        s = make_sample(sys.argv[1], sys.argv[2])
    else:
        s = pd.read_csv(SAMPLE, parse_dates=["post_date"])
    load(s)
    print(f"reviews caricate: {len(s)}")
