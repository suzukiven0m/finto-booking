"""D15: classificatore email (categoria + urgenza) + bozze di risposta.

Tecnica: lessico/regex derivati dal vocabolario dei template del generatore
(gen_emails.py, seed 42). Corpus sintetico -> F1 atteso elevato; NON e'
evidenza su email reali (vedi honesty statement in docs/analysis/email-assistant.md).

Modalita' di esecuzione:
  - DEFAULT (eval only): legge le 800 email dal DB, classifica, legge il gold
    (email_gold.csv) e scrive data/eval/email_metrics.json + docs/analysis/email-assistant.md.
    Non modifica il DB.
  - --persist: oltre all'eval, scrive category, urgency, draft_reply e status=draft
    nel DB per tutte le 800 email. Run una tantum, idempotente se rilanciato.

Il gold (data/eval/email_gold.csv) lo legge SOLO questo script per l'eval.
Le funzioni di classificazione (email_nlp.py) non lo vedono mai (anti-leakage).

Sidecar (host->container TCP bloccato):
  Eval:
    docker run --rm -i --network container:buby-postgres \\
      -v "$PWD":/repo:ro -v "$PWD/data/eval":/repo/data/eval \\
      -v "$PWD/docs/analysis":/repo/docs/analysis \\
      -w /repo -e PYTHONPATH=/repo/.venv/lib/python3.12/site-packages:/repo/backend:/repo/data \\
      python:3.12-slim python data/etl/classify_emails.py
  Persist:
    docker run --rm -i --network container:buby-postgres \\
      -v "$PWD":/repo:ro -w /repo \\
      -e PYTHONPATH=/repo/.venv/lib/python3.12/site-packages:/repo/backend:/repo/data \\
      python:3.12-slim python data/etl/classify_emails.py --persist
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import psycopg  # pyright: ignore[reportMissingImports]
from etl.email_nlp import (
    CATEGORIES,
    PROPERTY_NAMES,
    URGENCIES,
    classify_category,
    classify_urgency,
    render_draft,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import DATABASE_URL
from app.database import engine
from app.models import GuestRequest

ROOT = Path(__file__).resolve().parents[2]
GOLD = ROOT / "data" / "eval" / "email_gold.csv"
METRICS_OUT = ROOT / "data" / "eval" / "email_metrics.json"
REPORT_OUT = ROOT / "docs" / "analysis" / "email-assistant.md"


# ── DB helpers ────────────────────────────────────────────────────────────────


def _load_emails() -> list[dict]:
    with Session(engine) as session:
        rows = session.execute(
            select(
                GuestRequest.id,
                GuestRequest.body,
                GuestRequest.property_id,
            ).order_by(GuestRequest.id)
        ).all()
    return [{"id": r.id, "body": r.body, "property_id": r.property_id} for r in rows]


# ── classification ────────────────────────────────────────────────────────────


def _classify_all(emails: list[dict]) -> list[dict]:
    results = []
    for e in emails:
        cat = classify_category(e["body"])
        urg = classify_urgency(e["body"], cat)
        draft = render_draft(cat, PROPERTY_NAMES[e["property_id"]])
        results.append(
            {
                "id": e["id"],
                "category": cat,
                "urgency": urg,
                "draft": draft,
            }
        )
    return results


# ── eval ──────────────────────────────────────────────────────────────────────


def _load_gold() -> dict[int, dict]:
    gold: dict[int, dict] = {}
    with GOLD.open() as f:
        for row in csv.DictReader(f):
            gold[int(row["id"])] = {
                "category": row["true_category"],
                "urgency": row["true_urgency"],
            }
    return gold


def _confusion_matrix(y_true: list[str], y_pred: list[str], labels: list[str]) -> list[list[int]]:
    idx = {lbl: i for i, lbl in enumerate(labels)}
    n = len(labels)
    cm = [[0] * n for _ in range(n)]
    for t, p in zip(y_true, y_pred, strict=True):
        if t in idx and p in idx:
            cm[idx[t]][idx[p]] += 1
    return cm


def compute_metrics(predictions: list[dict], gold: dict[int, dict]) -> dict:
    """Calcola macro-F1, P/R/F1 per classe e confusion matrix per categoria e urgenza.

    Funzione pura: accetta predizioni e gold come dict, restituisce metriche.
    Usata anche dai test unit (nessun DB, nessun I/O).
    """
    y_true_cat: list[str] = []
    y_pred_cat: list[str] = []
    y_true_urg: list[str] = []
    y_pred_urg: list[str] = []
    for p in predictions:
        g = gold[p["id"]]
        y_true_cat.append(g["category"])
        y_pred_cat.append(p["category"])
        y_true_urg.append(g["urgency"])
        y_pred_urg.append(p["urgency"])

    def _per_class(
        y_t: list[str], y_p: list[str], labels: list[str]
    ) -> tuple[dict[str, dict], float]:
        stats: dict[str, dict] = {}
        for lbl in labels:
            tp = sum(1 for t, p in zip(y_t, y_p, strict=True) if t == lbl and p == lbl)
            fp = sum(1 for t, p in zip(y_t, y_p, strict=True) if t != lbl and p == lbl)
            fn = sum(1 for t, p in zip(y_t, y_p, strict=True) if t == lbl and p != lbl)
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
            stats[lbl] = {
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1": round(f1, 4),
            }
        # macro su classi con supporto > 0 (sklearn behavior: zero_division=0, average='macro')
        supported = [s for lbl, s in stats.items() if any(t == lbl for t in y_t)]
        macro_f1 = sum(s["f1"] for s in supported) / len(supported) if supported else 0.0
        return stats, round(macro_f1, 4)

    cat_stats, cat_macro = _per_class(y_true_cat, y_pred_cat, CATEGORIES)
    urg_stats, urg_macro = _per_class(y_true_urg, y_pred_urg, URGENCIES)
    cm_cat = _confusion_matrix(y_true_cat, y_pred_cat, CATEGORIES)
    cm_urg = _confusion_matrix(y_true_urg, y_pred_urg, URGENCIES)

    pred_ids = {p["id"] for p in predictions}
    gold_ids = set(gold.keys())

    return {
        "category": {
            "macro_f1": cat_macro,
            "per_class": cat_stats,
            "confusion_matrix": {"labels": CATEGORIES, "matrix": cm_cat},
        },
        "urgency": {
            "macro_f1": urg_macro,
            "per_class": urg_stats,
            "confusion_matrix": {"labels": URGENCIES, "matrix": cm_urg},
        },
        "gold_alignment": {
            "ids_matched": len(pred_ids & gold_ids),
            "ids_pred_only": sorted(pred_ids - gold_ids),
            "ids_gold_only": sorted(gold_ids - pred_ids),
        },
        "n_emails": len(predictions),
    }


# ── persist ───────────────────────────────────────────────────────────────────


def _persist(predictions: list[dict]) -> int:
    """Scrive category, urgency, draft_reply e status=draft nel DB. Idempotente."""
    url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
    written = 0
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        for p in predictions:
            cur.execute(
                "UPDATE guest_requests "
                "SET category=%s, urgency=%s, draft_reply=%s, status='draft' "
                "WHERE id=%s",
                (p["category"], p["urgency"], p["draft"], p["id"]),
            )
            written += cur.rowcount
        conn.commit()
    return written


# ── report ────────────────────────────────────────────────────────────────────


def _cm_table(labels: list[str], matrix: list[list[int]]) -> str:
    """Formatta una confusion matrix come tabella Markdown."""
    header = "| reale \\ predetto | " + " | ".join(labels) + " |"
    sep = "| --- |" + " --- |" * len(labels)
    rows = []
    for i, lbl in enumerate(labels):
        row = f"| **{lbl}** | " + " | ".join(str(matrix[i][j]) for j in range(len(labels))) + " |"
        rows.append(row)
    return "\n".join([header, sep] + rows)


def _write_report(metrics: dict) -> None:
    cat = metrics["category"]
    urg = metrics["urgency"]
    n = metrics["n_emails"]
    ga = metrics["gold_alignment"]

    pc_cat = cat["per_class"]
    pc_urg = urg["per_class"]

    cat_rows = "\n".join(
        f"| {k} | {v['precision']:.4f} | {v['recall']:.4f} | {v['f1']:.4f} |"
        for k, v in pc_cat.items()
    )
    urg_rows = "\n".join(
        f"| {k} | {v['precision']:.4f} | {v['recall']:.4f} | {v['f1']:.4f} |"
        for k, v in pc_urg.items()
    )
    cm_cat = _cm_table(cat["confusion_matrix"]["labels"], cat["confusion_matrix"]["matrix"])
    cm_urg = _cm_table(urg["confusion_matrix"]["labels"], urg["confusion_matrix"]["matrix"])

    report = f"""# Assistente email — analisi D15

**Branch:** fix/wp10-email-assistant · **Script:** `data/etl/classify_emails.py`

---

## 1. Metodo

**Classificatore:** lessicale deterministico basato su regex derivate direttamente
dal vocabolario dei template del generatore (`data/etl/gen_emails.py`, seed 42).

**Giustificazione della tecnica:** il corpus e' sintetico (800 email, 8+ template
per categoria, slot noti). Le regex coprono il vocabolario degli slot
(`BILLS`, `PROBLEMS`, `REQUESTS`, ecc.) e le frasi-chiave di ciascun template.
Il classificatore e' trasparente, riproducibile e non richiede training.

**Urgenza:** regole per categoria derivate dai valori `urgency` dei template,
con override testuale per i casi non-default (es. `problema di salute` ->
cancellation high; `recensione negativa` -> complaint medium).

**Dichiarazione di onesta' (obbligatoria):** l'F1 riportato e'
*sul corpus sintetico che ha generato le stesse regex*. **Non e' evidenza di
performance su email reali.** Il corpus ha 800 email generate da ~48 template
con slot controllati; un classificatore lessicale non generalizza a testi fuori
dal vocabolario del generatore.

---

## 2. Allineamento gold

| Metrica | Valore |
|---|---|
| Email nel DB | {n} |
| ID nel gold | {ga["ids_matched"]} |
| ID solo nel predetto | {len(ga["ids_pred_only"])} |
| ID solo nel gold | {len(ga["ids_gold_only"])} |

Allineamento completo: `ids_matched == n_emails` OK

---

## 3. Risultati — categoria

**Macro-F1 categoria: {cat["macro_f1"]:.4f}**

| Categoria | Precision | Recall | F1 |
|---|---|---|---|
{cat_rows}

### Confusion matrix (categoria)

{cm_cat}

---

## 4. Risultati — urgenza

**Macro-F1 urgenza: {urg["macro_f1"]:.4f}**

| Urgenza | Precision | Recall | F1 |
|---|---|---|---|
{urg_rows}

### Confusion matrix (urgenza)

{cm_urg}

---

## 5. Percorso di upgrade LLM (gated su O2/HA-05)

L'upgrade da classificatore lessicale a LLM (es. GPT-4o, Mistral via API)
e' bloccato sulla decisione umana **HA-05** (chiavi LLM + chi paga, scaduta
2026-11-16, `docs/reviews/human-actions.md`). Finche' HA-05 non e' chiusa
(`done -- data -- link evidenza`), il fallback lessicale e' l'unico componente
attivo.

Passi tecnici *dopo* HA-05:
1. Aggiungere la chiave API in `backend/app/config.py` (env var, non in repo).
2. Sostituire `classify_category` / `classify_urgency` in `email_nlp.py` con
   chiamata LLM (zero-shot o few-shot con gli stessi template come esempi).
3. Rieseguire eval su `email_gold.csv` e aggiornare questo report.
4. Se l'F1 su email reali diverge (atteso), integrare un campione reale nel gold.

---

## 6. Comando riproducibile

```bash
# eval (legge DB + gold, scrive metriche e questo report):
docker run --rm -i --network container:buby-postgres \\
  -v "$PWD":/repo:ro -v "$PWD/data/eval":/repo/data/eval \\
  -v "$PWD/docs/analysis":/repo/docs/analysis \\
  -w /repo -e PYTHONPATH=/repo/.venv/lib/python3.12/site-packages:/repo/backend:/repo/data \\
  python:3.12-slim python data/etl/classify_emails.py

# persist (scrive nel DB, idempotente):
docker run --rm -i --network container:buby-postgres \\
  -v "$PWD":/repo:ro -w /repo \\
  -e PYTHONPATH=/repo/.venv/lib/python3.12/site-packages:/repo/backend:/repo/data \\
  python:3.12-slim python data/etl/classify_emails.py --persist
```

---

*Generato automaticamente da `data/etl/classify_emails.py` -- {n} email su DB buby.*
"""
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(report)


# ── main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="D15 email classifier: eval (default) + opzionale persist nel DB"
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Scrive category/urgency/draft_reply/status=draft nel DB (una tantum, idempotente)",
    )
    args = parser.parse_args()

    print("Carico email dal DB...")
    emails = _load_emails()
    if len(emails) != 800:
        sys.exit(f"Attese 800 email nel DB, trovate {len(emails)}. Rieseguire gen_emails.py.")

    print(f"Classifico {len(emails)} email...")
    predictions = _classify_all(emails)

    print("Carico gold per eval...")
    gold = _load_gold()
    assert len(gold) == 800, f"Gold ha {len(gold)} righe, attese 800."
    metrics = compute_metrics(predictions, gold)

    # allineamento gold
    ga = metrics["gold_alignment"]
    if ga["ids_pred_only"] or ga["ids_gold_only"]:
        print(
            f"ATTENZIONE: ID mismatch -- solo nel predetto: {ga['ids_pred_only']}, "
            f"solo nel gold: {ga['ids_gold_only']}"
        )
        sys.exit(1)
    print(f"Allineamento gold OK: {ga['ids_matched']}/800 ID corrispondono")

    cat_f1 = metrics["category"]["macro_f1"]
    urg_f1 = metrics["urgency"]["macro_f1"]
    print("\n=== RISULTATI ===")
    print(f"Macro-F1 categoria: {cat_f1:.4f}")
    print(f"Macro-F1 urgenza:   {urg_f1:.4f}")

    if not args.persist:
        # solo in eval: scrivi metriche e report su filesystem (sidecar con mount rw)
        METRICS_OUT.parent.mkdir(parents=True, exist_ok=True)
        METRICS_OUT.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
        print(f"Metriche scritte: {METRICS_OUT}")
        _write_report(metrics)
        print(f"Report scritto: {REPORT_OUT}")
        print("\n(eval only -- usa --persist per scrivere nel DB)")
    else:
        print("\nScrivo previsioni nel DB (category/urgency/draft_reply/status=draft)...")
        n = _persist(predictions)
        print(f"Persist completato: {n} righe aggiornate.")


if __name__ == "__main__":
    main()
