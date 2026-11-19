"""Test della logica NON-modello di D14 (WP9): girano in CI senza scaricare pesi.

Il run completo (data/etl/run_review_nlp.py) non e' un passo di CI: ~2 GB di
pesi HuggingFace per esecuzione sarebbero proibitivi; qui si coprono mapping
topic/soglie, troncamento, selezione estrattiva e matematica delle metriche.
Il test sulla CSV completa si salta dove il file non c'e' (pattern di
test_baseline.py: il run NLP e' solo locale, la CSV e' gitignored).
"""

import os

import pandas as pd
import pytest
from etl import nlp
from etl import run_review_nlp as runner


class StubTokenizer:
    """Tokenizer finto: una parola = un token. Niente transformers, niente pesi."""

    def __call__(self, text, **kwargs):
        return {"input_ids": text.split()}

    def decode(self, ids, **kwargs):
        return " ".join(ids)


def test_sentiment_from_scores():
    scores = [
        {"label": "negative", "score": 0.8},
        {"label": "neutral", "score": 0.1},
        {"label": "positive", "score": 0.1},
    ]
    out = nlp.sentiment_from_scores(scores)
    assert out["label"] == "negative"
    assert out["score"] == pytest.approx(-0.7)


def test_assign_topics_soglie_per_topic():
    # ogni topic confrontato con la PROPRIA soglia; >= include il bordo
    scores = {t: th for t, th in nlp.TOPIC_THRESHOLDS.items()}
    assert nlp.assign_topics(scores) == list(nlp.TOPICS)  # ordine ADR, bordi inclusi
    scores["noise"] = nlp.TOPIC_THRESHOLDS["noise"] - 0.01
    assert "noise" not in nlp.assign_topics(scores)
    # una soglia unica 0.5 lascerebbe passare il noise gonfiato
    assert nlp.assign_topics({"noise": 0.8}) == []
    assert nlp.assign_topics({}) == []  # chiavi mancanti = score 0


def test_topics_from_output_mapping():
    out = {
        "labels": ["value for money", "staff", "cleanliness", "location", "breakfast", "noise"],
        "scores": [0.9, 0.9, 0.9, 0.1, 0.9, 0.1],
    }
    # "value for money" -> value; ordine ADR a prescindere dall'ordine del modello
    assert nlp.topics_from_output(out) == ["cleanliness", "staff", "breakfast", "value"]


def test_truncate_body():
    tok = StubTokenizer()
    assert nlp.truncate_body("corto testo", tok, 10) == ("corto testo", False)
    body = " ".join(f"w{i}" for i in range(300))
    capped, truncated = nlp.truncate_body(body, tok, 256)
    assert truncated is True
    assert capped == " ".join(f"w{i}" for i in range(256))


def test_split_sentences():
    assert nlp.split_sentences("Una. Due! Tre? Quattro") == ["Una.", "Due!", "Tre?", "Quattro"]
    assert nlp.split_sentences("   ") == []


def _reviews(rows):
    return pd.DataFrame(rows, columns=["id", "property_id", "post_date", "body", "sentiment_score"])


def test_monthly_summary_selezione():
    reviews = _reviews(
        [
            (1, 1, pd.Timestamp("2012-01-05"), "The staff were wonderful. The staff were wonderful. Short.", 0.9),  # noqa: E501
            (2, 1, pd.Timestamp("2012-01-20"), "The location was perfect for us.", 0.5),
            (3, 1, pd.Timestamp("2012-01-25"), "The room was very noisy at night.", -0.2),
            (4, 2, pd.Timestamp("2012-01-10"), "Another property entirely here.", 0.99),
        ]
    )
    out = nlp.monthly_summary(reviews, 1, "2012-01")
    assert out is not None
    assert out["n_reviews"] == 3  # la property 2 e' esclusa
    texts = [s["text"] for s in out["sentences"]]
    # deduplica (la ripetizione di r1 sparisce), filtro lunghezza ("Short."),
    # ordine per sentiment: r1 > r2 > r3
    assert texts == [
        "The staff were wonderful.",
        "The location was perfect for us.",
        "The room was very noisy at night.",
    ]
    assert out["sentences"][0]["review_id"] == 1
    assert nlp.monthly_summary(reviews, 1, "2012-01") == out  # deterministica
    assert nlp.monthly_summary(reviews, 1, "2013-01") is None  # mese vuoto


def test_monthly_summary_lead_bias_e_k():
    reviews = _reviews(
        [
            (1, 1, pd.Timestamp("2012-02-01"), "First sentence wins here. Second sentence loses here.", 0.8),  # noqa: E501
            (2, 1, pd.Timestamp("2012-02-02"), "A different good sentence here.", 0.8),
        ]
    )
    out = nlp.monthly_summary(reviews, 1, "2012-02", k=1)
    assert out is not None
    # lead bias: a parita' di sentiment della recensione, la frase 0 batte la 1;
    # a parita' di punteggio, review_id minore
    assert out["sentences"][0]["text"] == "First sentence wins here."
    full = nlp.monthly_summary(reviews, 1, "2012-02", k=3)
    assert full is not None and len(full["sentences"]) == 3


def test_corr():
    x, y = pd.Series([1.0, 2, 3, 4]), pd.Series([1.0, 4, 9, 16])
    out = nlp._corr(x, y)
    assert out == {"n": 4, "spearman": 1.0, "pearson": 0.9844}
    assert nlp._corr(pd.Series([1.0, 2]), pd.Series([3.0, 4]))["spearman"] is None  # n<3
    assert nlp._corr(pd.Series([1.0, 1, 1]), pd.Series([1.0, 2, 3]))["pearson"] is None


def _fixture():
    dims = ["overall", "cleanliness", "value", "location", "rooms", "sleep_quality"]
    reviews = pd.DataFrame(
        [
            (1, 1, 5, 5, 4, 4, 4, 5),
            (2, 1, 2, 2, 3, 3, 2, 1),
            (3, 1, 4, 4, 4, 5, 4, 4),
            (4, 2, 1, 1, 2, 2, 1, 2),
            (5, 2, 3, 3, 3, 3, 3, 3),
            (6, 2, 5, 5, 5, 5, 5, 5),
        ],
        columns=["id", "property_id", *dims],
    )
    pred = pd.DataFrame(
        [
            (1, 1, "positive", 0.9, "cleanliness;staff"),
            (2, 1, "negative", -0.8, "noise"),
            (3, 1, "positive", 0.5, "location;value"),
            (4, 2, "negative", -0.9, "cleanliness;noise"),
            (5, 2, "neutral", 0.0, ""),
            (6, 2, "positive", 0.8, "value"),
        ],
        columns=["id", "property_id", "sentiment_label", "sentiment_score", "topics"],
    )
    return pred, reviews


def test_compute_metrics():
    pred, reviews = _fixture()
    m = nlp.compute_metrics(pred, reviews)
    assert m["sentiment"]["label_counts"]["pooled"] == {
        "negative": 2,
        "neutral": 1,
        "positive": 3,
    }
    assert m["sentiment"]["label_counts"]["per_property"]["1"] == {
        "negative": 1,
        "neutral": 0,
        "positive": 2,
    }
    prev = m["topics"]["prevalence"]["pooled"]
    assert prev["cleanliness"] == 0.3333 and prev["noise"] == 0.3333
    assert prev["breakfast"] == 0.0 and prev["value"] == 0.3333
    assert m["topics"]["thresholds"] == nlp.TOPIC_THRESHOLDS
    # pattern: cleanliness menzionata su recensioni con voto cleanliness 5 e 1
    pat = {p["topic"]: p for p in m["topics"]["dimension_patterns"]["pooled"]}
    assert pat["cleanliness"]["n_mentioned"] == 2
    assert pat["cleanliness"]["mean_dim_mentioned"] == 3.0
    assert pat["cleanliness"]["mean_dim_not_mentioned"] == 3.5
    assert pat["cleanliness"]["delta"] == -0.5
    # noise -> sleep_quality (assunzione dichiarata): 1 e 2 vs 5,4,3,5
    assert pat["noise"]["delta"] == -2.75
    assert "staff" not in pat and "breakfast" not in pat  # nessuna dimensione
    corr = m["sentiment"]["correlations"]["pooled"]["overall"]
    assert corr["n"] == 6 and corr["spearman"] == 0.9856


def test_runner_helpers_resume(tmp_path):
    path = str(tmp_path / "partial.csv")
    assert runner.read_done_ids(path) == set()
    rows = pd.DataFrame({"id": [1, 2], "topics": ["staff", ""]})
    runner.append_rows(path, rows)
    runner.append_rows(path, pd.DataFrame({"id": [3], "topics": ["noise"]}))
    assert runner.read_done_ids(path) == {1, 2, 3}
    back = pd.read_csv(path, keep_default_na=False)
    assert len(back) == 3 and back.topics.iloc[1] == ""  # header unico, vuoti non NaN


@pytest.mark.skipif(
    not os.path.exists("data/eval/review_nlp_predictions.csv"),
    reason="CSV completa solo locale: run NLP gitignored, non e' un passo di CI",
)
def test_predictions_copertura():
    df = pd.read_csv("data/eval/review_nlp_predictions.csv", keep_default_na=False)
    assert len(df) == 1638
    assert df.id.is_unique
    assert set(df.sentiment_label) <= {"negative", "neutral", "positive"}
    assert (df.sentiment_label != "").all()
    for topics in df.topics:
        names = topics.split(";") if topics else []
        assert names == [t for t in nlp.TOPICS if t in names]  # solo canonici, ordine ADR