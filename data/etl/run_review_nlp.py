"""Run NLP (D14) su TUTTE le recensioni del DB. Sola lettura: nessun output nel DB (S8).

Legge `reviews` con una SELECT (mai guest_requests, mai il gold delle email),
calcola sentiment + topics + sintesi mensili e scrive SOLO artefatti in data/eval/:
review_nlp_predictions.csv, review_nlp_metrics.json, review_summaries.json.
Il contratto congelato non espone questi output: l'esposizione API e' un
contract-bump successivo (decisione di scope WP9, dizionario «Decisioni pre-freeze»).

Crash-resiliente: le due passate scrivono CSV parziali (uno per fase, append per
batch) e --resume salta gli id gia' presenti. Il CSV finale e' il merge dei due
parziali, riscritto a ogni completamento. I parziali restano su disco (gitignored)
cosi' un resume dopo il completamento e' un no-op che rigenera solo metriche e
sintesi. Le fasi sono sequenziali, un modello per volta: fp32, ~1.7 GB di pesi
ciascuno, tenerli entrambi residenti su una macchina da 8 GB farebbe swap.

Deterministico: seed 42, revision dei pesi fissate in etl/nlp.py, CPU fp32,
4 thread (misurati: piu' thread peggiorano su 4 core/8 thread), batch fissi,
topics in batch ordinati per lunghezza (meno padding). Con --resume la
composizione dei batch puo' cambiare: le riduzioni fp32 possono variare ~1e-6,
label e topic (soglie distanti dai bordi) no. NON e' un passo di CI: ~2 GB di
pesi al primo download sarebbero proibitivi a ogni run; i test CI coprono la
logica non-modello (data/tests/test_review_nlp.py).

Run completo (host→container TCP bloccato: sidecar con la rete di Postgres, repo
in sola lettura, data/eval scrivibile, cache HF dell'host montata — pesi gia'
scaricati). Lancio in background con log, per non tenere aperta una shell per
ore (runtime: stima iniziale ~4 h per topics; misurato 2 h 21 min, sentiment
~20 min, su i5-10210U):

    nohup docker run --rm -i --network container:buby-postgres \
      -v "$PWD":/repo:ro -v "$PWD/data/eval":/repo/data/eval \
      -v "$HOME/.cache/huggingface":/root/.cache/huggingface \
      -w /repo -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 \
      -e PYTHONPATH=/repo/.venv/lib/python3.12/site-packages:/repo/backend:/repo/data \
      python:3.12-slim python data/etl/run_review_nlp.py \
      > /tmp/wp9-run.log 2>&1 &

    # ripresa dopo un crash (stesso comando con --resume in coda):
    #   ... python data/etl/run_review_nlp.py --resume

Prerequisiti: .venv con data/requirements.txt + backend/requirements.txt
(uv venv --python 3.12 .venv; per torch serve --index-strategy unsafe-best-match,
vedi data/requirements.txt), pesi in cache (snapshot_download delle due revision
in etl/nlp.py). Senza cache: togliere le due variabili OFFLINE.
"""

import argparse
import gc
import json
import os
import random
import time
from typing import cast

import numpy as np
import pandas as pd
import torch
import transformers
from etl import nlp
from sqlalchemy import create_engine

from app.config import DATABASE_URL

EVAL = "data/eval"
PRED_CSV = f"{EVAL}/review_nlp_predictions.csv"
SENT_PARTIAL = f"{EVAL}/review_nlp_sentiment.partial.csv"
TOPICS_PARTIAL = f"{EVAL}/review_nlp_topics.partial.csv"
SENT_BATCH = 32  # body per forward
TOPICS_BATCH = 6  # body per forward = 36 coppie NLI (6 topic per body)
THREADS = 4


def read_done_ids(path: str) -> set[int]:
    """Id gia' scritti in un CSV parziale (vuoto se il file non esiste)."""
    if not os.path.exists(path):
        return set()
    return set(pd.read_csv(path, usecols=["id"]).id)


def append_rows(path: str, rows: pd.DataFrame) -> None:
    """Append per batch: header solo alla prima scrittura."""
    rows.to_csv(path, mode="a", header=not os.path.exists(path), index=False)


def run_sentiment(reviews: pd.DataFrame, resume: bool) -> float:
    t0 = time.perf_counter()
    if not resume and os.path.exists(SENT_PARTIAL):
        os.remove(SENT_PARTIAL)
    pipe = nlp.load_sentiment_pipeline()
    todo = reviews[~reviews.id.isin(read_done_ids(SENT_PARTIAL))]
    print(
        f"sentiment: {len(todo)} body da fare ({len(reviews) - len(todo)} gia' fatti)", flush=True
    )
    tok = pipe.tokenizer
    for start in range(0, len(todo), SENT_BATCH):
        batch = todo.iloc[start : start + SENT_BATCH]
        raw = pipe(
            batch.body.tolist(),
            batch_size=SENT_BATCH,
            truncation=True,
            max_length=nlp.SENTIMENT_MAX_TOKENS,
        )
        sent = [nlp.sentiment_from_scores(r) for r in raw]
        append_rows(
            SENT_PARTIAL,
            pd.DataFrame(
                {
                    "id": batch.id.to_numpy(),
                    "sentiment_label": [s["label"] for s in sent],
                    "sentiment_score": [round(s["score"], 6) for s in sent],
                    "truncated": [
                        len(tok(b)["input_ids"]) > nlp.SENTIMENT_MAX_TOKENS for b in batch.body
                    ],
                }
            ),
        )
        print(f"sentiment {min(start + SENT_BATCH, len(todo))}/{len(todo)}", flush=True)
    del pipe
    gc.collect()
    return time.perf_counter() - t0


def run_topics(reviews: pd.DataFrame, resume: bool) -> float:
    t0 = time.perf_counter()
    if not resume and os.path.exists(TOPICS_PARTIAL):
        os.remove(TOPICS_PARTIAL)
    pipe = nlp.load_topics_pipeline()
    todo = reviews[~reviews.id.isin(read_done_ids(TOPICS_PARTIAL))].copy()
    print(f"topics: {len(todo)} body da fare ({len(reviews) - len(todo)} gia' fatti)", flush=True)
    tok = pipe.tokenizer
    capped = [nlp.truncate_body(b, tok, nlp.TOPICS_MAX_TOKENS) for b in todo.body]
    todo["capped"] = [c for c, _ in capped]
    todo["truncated"] = [t for _, t in capped]
    todo["n_tokens"] = [len(tok(c)["input_ids"]) for c in todo.capped]
    # batch di lunghezza simile = meno padding; ordinamento deterministico
    todo = todo.sort_values(["n_tokens", "id"])
    for start in range(0, len(todo), TOPICS_BATCH):
        batch = todo.iloc[start : start + TOPICS_BATCH]
        zout = cast(
            "list[dict]",
            pipe(
                batch.capped.tolist(),
                candidate_labels=list(nlp.TOPIC_LABELS.values()),
                multi_label=True,
                hypothesis_template=nlp.HYPOTHESIS_TEMPLATE,
                batch_size=TOPICS_BATCH * len(nlp.TOPICS),
            ),
        )
        append_rows(
            TOPICS_PARTIAL,
            pd.DataFrame(
                {
                    "id": batch.id.to_numpy(),
                    "topics": [";".join(nlp.topics_from_output(o)) for o in zout],
                    "truncated": batch.truncated.to_numpy(),
                }
            ),
        )
        print(f"topics {min(start + TOPICS_BATCH, len(todo))}/{len(todo)}", flush=True)
    del pipe
    gc.collect()
    return time.perf_counter() - t0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--resume", action="store_true", help="salta gli id gia' presenti nei CSV parziali"
    )
    args = parser.parse_args()

    t0 = time.perf_counter()
    random.seed(nlp.SEED)
    np.random.seed(nlp.SEED)
    torch.manual_seed(nlp.SEED)
    transformers.set_seed(nlp.SEED)
    torch.set_num_threads(THREADS)

    # sola lettura: l'unica query e' questa SELECT su reviews
    eng = create_engine(DATABASE_URL)
    reviews = pd.read_sql(
        "SELECT id, property_id, post_date, overall, cleanliness, value, location,"
        " rooms, sleep_quality, body FROM reviews ORDER BY id",
        eng,
    )
    reviews["post_date"] = pd.to_datetime(reviews["post_date"])
    reviews[list(nlp.DIMENSIONS)] = reviews[list(nlp.DIMENSIONS)].astype(float)
    null_bodies = int(reviews.body.isna().sum())
    if null_bodies:
        raise SystemExit(f"{null_bodies} body NULL: il corpus deve essere completo (N=1638)")
    print(f"recensioni lette: {len(reviews)} (body nulli: {null_bodies})", flush=True)

    print("sentiment:", nlp.SENTIMENT_MODEL, flush=True)
    sent_seconds = run_sentiment(reviews, args.resume)
    print("topics:", nlp.TOPICS_MODEL, flush=True)
    topics_seconds = run_topics(reviews, args.resume)

    # keep_default_na=False: un body senza topic e' stringa vuota, non NaN
    sent = pd.read_csv(SENT_PARTIAL, keep_default_na=False)
    top = pd.read_csv(TOPICS_PARTIAL, keep_default_na=False)
    pred = (
        reviews[["id", "property_id", "post_date"]]
        .merge(sent, on="id", validate="one_to_one")
        .merge(top[["id", "topics"]], on="id", validate="one_to_one")
        .sort_values("id")
    )
    pred["post_date"] = pred.post_date.dt.strftime("%Y-%m-%d")
    pred = pred[["id", "property_id", "post_date", "sentiment_label", "sentiment_score", "topics"]]
    pred.to_csv(PRED_CSV, index=False)

    scored = reviews.assign(sentiment_score=pred.sentiment_score.to_numpy())
    months = sorted(scored.post_date.dt.strftime("%Y-%m").unique())
    summaries = [
        s
        for pid in sorted(scored.property_id.unique())
        for m in months
        if (s := nlp.monthly_summary(scored, int(pid), m)) is not None
    ]
    with open(f"{EVAL}/review_summaries.json", "w") as fh:
        json.dump({"k": 3, "summaries": summaries}, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    def trunc_stats(partial: pd.DataFrame, max_tokens: int) -> dict:
        n = int(partial.truncated.sum())
        return {
            "max_tokens": max_tokens,
            "n_truncated": n,
            "rate": round(n / len(partial), 4),
        }

    metrics = {
        "coverage": {
            "reviews_total": int(len(reviews)),
            "bodies_processed": int(len(pred)),
            "null_bodies": null_bodies,
        },
        "models": {
            "sentiment": {"name": nlp.SENTIMENT_MODEL, "revision": nlp.SENTIMENT_REVISION},
            "topics": {"name": nlp.TOPICS_MODEL, "revision": nlp.TOPICS_REVISION},
        },
        "libraries": {
            "transformers": transformers.__version__,
            "torch": torch.__version__,
            "pandas": pd.__version__,
        },
        "seed": nlp.SEED,
        "inference": {
            "device": "cpu",
            "dtype": "float32",
            "threads": THREADS,
            "sentiment_batch_bodies": SENT_BATCH,
            "topics_batch_bodies": TOPICS_BATCH,
            "topics_batch_order": "lunghezza token crescente (meno padding)",
            "phases": "sequenziali, un modello per volta (RAM)",
        },
        "truncation": {
            "sentiment": trunc_stats(sent, nlp.SENTIMENT_MAX_TOKENS),
            "topics": trunc_stats(top, nlp.TOPICS_MAX_TOKENS),
        },
        "runtime_seconds": {
            "sentiment": round(sent_seconds, 1),
            "topics": round(topics_seconds, 1),
            "total": round(time.perf_counter() - t0, 1),
            "note": "questa invocazione; con --resume non include le passate precedenti",
        },
        **nlp.compute_metrics(pred, reviews),
        "caveats": [
            "S4: recensioni solo 2012, prenotazioni 2015-2017: zero mesi in comune, "
            "nessuna analisi congiunta; comparazione solo a livello di proprieta'.",
            "Corpus solo inglese, N=1638, due proprieta': statistiche descrittive, "
            "non inferenza su una popolazione.",
            "Etichette deboli: i voti reali 1-5 non sono stati generati dal modello; "
            "correlazione non e' accuratezza.",
            "Output query-time (S8): mai scritti nel DB; il run legge reviews in sola lettura.",
            "Topics: troncati a 256 token per runtime (il modello arriverebbe a 1024); "
            "soglie calibrate su probe di 20 recensioni, F1 ottimistico.",
        ],
    }
    with open(f"{EVAL}/review_nlp_metrics.json", "w") as fh:
        json.dump(metrics, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"artefatti scritti in {EVAL}/ (predictions, metrics, summaries)", flush=True)
    print(
        f"copertura: {len(pred)}/{len(reviews)} body, runtime {metrics['runtime_seconds']}",
        flush=True,
    )
    pooled = metrics["sentiment"]["correlations"]["pooled"]
    for dim, c in pooled.items():
        print(f"  sentiment vs {dim}: spearman={c['spearman']} pearson={c['pearson']} (n={c['n']})")


if __name__ == "__main__":
    main()
