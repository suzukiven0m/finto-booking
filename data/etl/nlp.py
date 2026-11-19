"""NLP recensioni (D14): sentiment, topics e sintesi mensile, al momento della query.

Decisione pre-freeze S8 (dizionario «Decisioni pre-freeze», ADR 0003 §5): gli
output del modello NON si scrivono nel DB — niente tabelle derivate in v1, un
re-run non fa UPDATE sulla sorgente. Qui solo funzioni (pure + caricamento
modelli); il run completo e' data/etl/run_review_nlp.py, che legge le recensioni
in sola lettura e scrive i suoi artefatti in data/eval/.

Modelli preaddestrati, nessun training (ADR 0003 §5):
- sentiment: cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual,
  multilingue, 3 classi (negative/neutral/positive);
- topics: facebook/bart-large-mnli, zero-shot NLI multi-label sui 6 topic
  dell'ADR — il corpus e' solo inglese (dizionario §1), un modello NLI inglese
  e' appropriato e non serve addestrare un classificatore.
Revision dei pesi fissate: stesso codice + stessi pesi = stessi numeri.

transformers/torch si importano solo dentro i loader: i test CI e chi chiama
queste funzioni senza modelli non devono ne' scaricare ne' importare la pipeline.
"""

import re
from typing import cast

import pandas as pd

SEED = 42

SENTIMENT_MODEL = "cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual"
SENTIMENT_REVISION = "82107f4ccba672c9ab1eee538e727e462cad21de"
TOPICS_MODEL = "facebook/bart-large-mnli"
TOPICS_REVISION = "d7645e127eaf1aefc7862fd59a17a5aa8558b8ce"

# 6 topic di ADR 0003 §5, nell'ordine dell'ADR. Il topic "value" si presenta al
# modello NLI come "value for money": senza "for money" l'etichetta e' ambigua.
TOPICS = ("cleanliness", "staff", "location", "breakfast", "noise", "value")
TOPIC_LABELS = {
    "cleanliness": "cleanliness",
    "staff": "staff",
    "location": "location",
    "breakfast": "breakfast",
    "noise": "noise",
    "value": "value for money",
}
HYPOTHESIS_TEMPLATE = "This review discusses {}."

# Soglie per-topic calibrate il 2026-11-19 su una probe di 20 recensioni
# (id % 82 = 7, 120 giudizi di menzione annotati a mano sul testo visto dal
# modello): per ogni topic la soglia che massimizza F1, arrotondata dentro il
# plateau ottimo. Una soglia unica 0.5 non basta: gli score NLI sono gonfiati
# (es. "value for money" ~0.93 senza alcun cenno al prezzo, location ~0.79 su
# recensioni che non parlano di posizione). F1 sulla probe (ottimistico: n
# piccolo, stesso corpus, annotatore unico): cleanliness 0.889, staff 0.929,
# location 0.880, breakfast 0.909, noise 0.933, value 0.857. Restano falsi
# negativi che nessuna soglia recupera (menzioni esplicite a score 0.21/0.35):
# la prevalenza dei topic e' un segnale debole, non una misura esatta.
TOPIC_THRESHOLDS = {
    "cleanliness": 0.7,
    "staff": 0.55,
    "location": 0.7,
    "breakfast": 0.5,
    "noise": 0.9,
    "value": 0.85,
}
TOPIC_PROBE_F1 = {
    "cleanliness": 0.889,
    "staff": 0.929,
    "location": 0.88,
    "breakfast": 0.909,
    "noise": 0.933,
    "value": 0.857,
}

# Limiti di token. Sentiment: 512 e' il limite del modello (xlm-roberta).
# Topics: 256 e' un tetto di runtime, non del modello (bart-large arriva a
# 1024): sul processore del run (i5-10210U, 4 core) la passata zero-shot fp32
# costa ~1.3 s/coppia e 1024 token sarebbero ~8 h; 256 tronca il 25.6% dei
# body (mediana 152 token: la maggioranza resta intera) e dimezza il costo.
# Il troncamento e' esplicito (truncate_body) perche' la pipeline zero-shot
# ignora max_length e tronca da sola a 1024.
SENTIMENT_MAX_TOKENS = 512
TOPICS_MAX_TOKENS = 256

# Dimensioni reali (weak label) per topic. staff/breakfast non hanno una
# dimensione nel corpus: si riporta solo la prevalenza. noise -> sleep_quality
# e' un'assunzione dichiarata (il rumore perturba il sonno, non c'e' un voto
# "rumore" nel corpus Li et al. 2013).
DIMENSIONS = ("overall", "cleanliness", "value", "location", "rooms", "sleep_quality")
TOPIC_DIMENSION = {
    "cleanliness": "cleanliness",
    "staff": None,
    "location": "location",
    "breakfast": None,
    "noise": "sleep_quality",
    "value": "value",
}

SENTENCE_MIN_WORDS = 4
SENTENCE_MAX_WORDS = 40
LEAD_BIAS = 0.01


def load_sentiment_pipeline():
    from transformers import pipeline

    return pipeline(
        # nome canonico del task: "sentiment-analysis" e' un alias runtime, ma
        # gli overload tipizzati di pipeline() sono keyed sul nome canonico
        "text-classification",
        model=SENTIMENT_MODEL,
        revision=SENTIMENT_REVISION,
        top_k=None,
        device=-1,
    )


def sentiment_from_scores(scores: list[dict]) -> dict:
    """Output grezzo del modello (3 classi) -> label + punteggio continuo.

    score = P(positive) - P(negative) in [-1, 1]: e' la forma continua che si
    correla con i voti reali 1-5 (la sola probabilita' della classe vincente
    non e' monotona rispetto al voto).
    """
    by = {d["label"]: float(d["score"]) for d in scores}
    return {"label": max(by, key=lambda k: by[k]), "score": by["positive"] - by["negative"]}


def sentiment(body: str, pipe) -> dict:
    """Query-time: un body, label + score. `pipe` da load_sentiment_pipeline()."""
    return sentiment_from_scores(
        pipe(body, truncation=True, max_length=SENTIMENT_MAX_TOKENS)[0]
    )


def truncate_body(body: str, tokenizer, max_tokens: int) -> tuple[str, bool]:
    """Body -> (testo entro max_tokens, troncato?). Tokenizzazione unica.

    ids[:max_tokens] con skip_special_tokens in decode equivale alla
    truncation del tokenizer: deterministico, nessuna dipendenza dal modello.
    """
    ids = tokenizer(body)["input_ids"]
    if len(ids) <= max_tokens:
        return body, False
    return tokenizer.decode(ids[:max_tokens], skip_special_tokens=True), True


def load_topics_pipeline():
    from transformers import pipeline

    return pipeline(
        "zero-shot-classification", model=TOPICS_MODEL, revision=TOPICS_REVISION, device=-1
    )


def assign_topics(
    scores: dict[str, float], thresholds: dict[str, float] = TOPIC_THRESHOLDS
) -> list[str]:
    """Punteggi NLI per topic canonico -> topic sopra la propria soglia, ordine ADR."""
    return [t for t in TOPICS if scores.get(t, 0.0) >= thresholds[t]]


def topics_from_output(out: dict, thresholds: dict[str, float] = TOPIC_THRESHOLDS) -> list[str]:
    """Output zero-shot (labels/scores del modello) -> topic canonici."""
    inverse = {label: topic for topic, label in TOPIC_LABELS.items()}
    scores = {inverse[label]: s for label, s in zip(out["labels"], out["scores"], strict=True)}
    return assign_topics(scores, thresholds)


def topics(body: str, pipe, thresholds: dict[str, float] = TOPIC_THRESHOLDS) -> list[str]:
    """Query-time: un body, multi-label. `pipe` da load_topics_pipeline()."""
    out = pipe(
        body,
        candidate_labels=list(TOPIC_LABELS.values()),
        multi_label=True,
        hypothesis_template=HYPOTHESIS_TEMPLATE,
    )
    return topics_from_output(out, thresholds)


def split_sentences(body: str) -> list[str]:
    """Split estrattivo su . ! ? — niente dipendenze extra, il corpus e' prosa semplice."""
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", body.strip()) if s.strip()]


def monthly_summary(
    reviews: pd.DataFrame, property_id: int, month: str, k: int = 3
) -> dict | None:
    """Sintesi ESTRATTIVA per proprieta' e mese (es. "2012-01"): niente LLM.

    `reviews` deve avere id, property_id, post_date (datetime), body e
    sentiment_score (il punteggio continuo di sentiment_from_scores). Selezione
    lead-bias su frasi pesate dal sentiment della recensione: punteggio =
    sentiment_score - LEAD_BIAS * posizione, filtro di lunghezza, deduplica
    testuale, prime k. Deterministica a parita' di input. None se il mese e' vuoto.
    """
    g = reviews.loc[
        (reviews.property_id == property_id)
        & (reviews.post_date.dt.strftime("%Y-%m") == month)
    ]
    if g.empty:
        return None
    candidates = []
    for r in g.sort_values("id").itertuples():
        for i, sentence in enumerate(split_sentences(r.body)):
            words = len(sentence.split())
            if SENTENCE_MIN_WORDS <= words <= SENTENCE_MAX_WORDS:
                candidates.append(
                    {
                        "text": sentence,
                        "review_id": int(r.id),
                        "post_date": r.post_date.date().isoformat(),
                        "score": round(float(r.sentiment_score) - LEAD_BIAS * i, 6),
                    }
                )
    candidates.sort(key=lambda c: (-c["score"], c["review_id"], c["text"]))
    seen: set[str] = set()
    picked = []
    for c in candidates:
        if c["text"].lower() in seen:
            continue
        seen.add(c["text"].lower())
        picked.append(c)
        if len(picked) == k:
            break
    return {
        "property_id": property_id,
        "month": month,
        "n_reviews": int(len(g)),
        "sentences": picked,
    }


def _corr(x: pd.Series, y: pd.Series) -> dict:
    """Spearman + Pearson su coppie complete. n<3 o serie costante -> None."""
    pair = pd.concat([x, y], axis=1).dropna()
    n = int(len(pair))
    out = {"n": n, "spearman": None, "pearson": None}
    if n < 3 or pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
        return out
    a, b = pair.iloc[:, 0], pair.iloc[:, 1]
    for method in ("spearman", "pearson"):
        rho = a.corr(b, method=method)
        out[method] = None if pd.isna(rho) else round(float(rho), 4)
    return out


def compute_metrics(pred: pd.DataFrame, reviews: pd.DataFrame) -> dict:
    """Valutazione weak-label: predizioni vs voti REALI del corpus (ADR 0003 §5).

    pred: id, property_id, sentiment_label, sentiment_score, topics (stringa
    separata da ";", vuota se nessun topic). reviews: id + le dimensioni reali
    (DIMENSIONS). Nessun numero qui viene dal modello: sono correlazioni e
    prevalenze calcolate sulle etichette deboli, che il modello non ha generato.
    """
    df = pred.merge(reviews[["id", *DIMENSIONS]], on="id", validate="one_to_one")
    topic_sets = df.topics.map(lambda s: set(s.split(";")) if s else set())

    def block(g: pd.DataFrame, sets: pd.Series) -> dict:
        labels = {
            lab: int((g.sentiment_label == lab).sum())
            for lab in ("negative", "neutral", "positive")
        }
        correlations = {
            dim: _corr(g.sentiment_score, cast("pd.Series", g[dim])) for dim in DIMENSIONS
        }
        prevalence = {
            t: round(float(sets.map(lambda s, t=t: t in s).mean()), 4) for t in TOPICS
        }
        patterns = []
        for topic, dim in TOPIC_DIMENSION.items():
            if dim is None:
                continue
            mentioned = sets.map(lambda s, topic=topic: topic in s)
            yes, no = g.loc[mentioned, dim], g.loc[~mentioned, dim]
            mean_yes = None if yes.dropna().empty else round(float(yes.mean()), 3)
            mean_no = None if no.dropna().empty else round(float(no.mean()), 3)
            patterns.append(
                {
                    "topic": topic,
                    "dimension": dim,
                    "n_mentioned": int(mentioned.sum()),
                    "n_not_mentioned": int((~mentioned).sum()),
                    "mean_dim_mentioned": mean_yes,
                    "mean_dim_not_mentioned": mean_no,
                    "delta": (
                        None
                        if mean_yes is None or mean_no is None
                        else round(mean_yes - mean_no, 3)
                    ),
                }
            )
        return {
            "label_counts": labels,
            "correlations": correlations,
            "prevalence": prevalence,
            "dimension_patterns": patterns,
        }

    pooled = block(df, topic_sets)
    per_property = {
        str(pid): block(g, topic_sets.loc[g.index]) for pid, g in df.groupby("property_id")
    }

    def per(key: str) -> dict:
        return {p: b[key] for p, b in per_property.items()}

    return {
        "sentiment": {
            "score_definition": (
                "P(positive) - P(negative) in [-1, 1]; label = argmax delle 3 classi"
            ),
            "label_counts": {
                "pooled": pooled["label_counts"],
                "per_property": per("label_counts"),
            },
            "correlations": {
                "pooled": pooled["correlations"],
                "per_property": per("correlations"),
            },
        },
        "topics": {
            "technique": "zero-shot NLI multi-label (facebook/bart-large-mnli)",
            "hypothesis_template": HYPOTHESIS_TEMPLATE,
            "thresholds": TOPIC_THRESHOLDS,
            "threshold_calibration": {
                "probe_n": 20,
                "selection": "soglia per-topic di massimo F1 sulla probe, dentro il plateau ottimo",
                "probe_f1": TOPIC_PROBE_F1,
                "caveat": "probe piccola, stesso corpus, annotatore unico: F1 ottimistico",
            },
            "dimension_map": TOPIC_DIMENSION,
            "prevalence": {
                "pooled": pooled["prevalence"],
                "per_property": per("prevalence"),
            },
            "dimension_patterns": {
                "pooled": pooled["dimension_patterns"],
                "per_property": per("dimension_patterns"),
            },
        },
    }
