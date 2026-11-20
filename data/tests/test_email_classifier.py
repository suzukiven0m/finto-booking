"""Test D15 (WP10): classificatore lessicale email — senza DB, senza gold.

Copertura:
  - classify_category su fixture per categoria (una per template, piu' edge case)
  - classify_urgency su fixture per urgenza (default + override testuale)
  - render_draft: struttura e nome della struttura nella bozza
  - anti-leakage (a): email_nlp.py non referenzia email_gold.csv (import-graph)
  - eval math (b): compute_metrics su fixture sintetiche (macro-F1, confusion matrix)
  - nessun import del gold in questo file di test
"""

from __future__ import annotations

import pytest
from etl.email_nlp import (
    CATEGORIES,
    PROPERTY_NAMES,
    classify_category,
    classify_urgency,
    render_draft,
)

# ── fixture categoria ─────────────────────────────────────────────────────────
# Un caso per template del generatore (gen_emails.py TEMPLATES) + edge case.

FIXTURES_CATEGORY: list[tuple[str, str]] = [
    # billing — slot BILLS + frasi template
    (
        "Buongiorno, sulla carta vedo un addebito di 50 euro che non riconosco. Potete verificare?",
        "billing",
    ),
    (
        "Nella fattura della prenotazione BUBY-2026-1234 c'e' una tassa di soggiorno "
        "che non ci era stata comunicata.",
        "billing",
    ),
    (
        "Alla partenza ho pagato il conto, ma ora trovo un addebito per il minibar "
        "che non abbiamo mai aperto. Non ho firmato nulla del genere.",
        "billing",
    ),
    (
        "Ho ricevuto una differenza di 40 euro. "
        "Potete mandarmi il dettaglio di quello che abbiamo consumato?",
        "billing",
    ),
    (
        "Nel totale c'e' il costo della colazione in un pacchetto che la includeva. "
        "Era incluso nel pacchetto che avevo scelto.",
        "billing",
    ),
    (
        "Mi hanno addebitato un supplemento animali di cui non sapevamo nulla. "
        "Vorrei capire da dove arriva questa cifra prima di procedere per altra via.",
        "billing",
    ),
    (
        "Purtroppo c'e' l'anticipo versato che non compare in fattura. "
        "Se non si risolve dovro' chiedere il chargeback alla carta.",
        "billing",
    ),
    # cancellation — template T1-T8
    (
        "Purtroppo devo annullare la prenotazione BUBY-2026-9999 per la Doppia Classic "
        "dal 15 settembre. Cosa devo fare per non perdere l'anticipo?",
        "cancellation",
    ),
    (
        "La prenotazione BUBY-2026-1234 dal 20 agosto non mi serve piu': "
        "e' possibile cancellarla senza penali?",
        "cancellation",
    ),
    (
        "Ho avuto un problema di salute e non possiamo venire. Posso spostare la data?",
        "cancellation",
    ),
    (
        "Dovrei cancellare il soggiorno. La mia tariffa era non rimborsabile: "
        "c'e' margine per un cambio data?",
        "cancellation",
    ),
    (
        "Annullo la Camera Familiare dal 10 ottobre: il volo e' stato cancellato "
        "e non riusciamo ad arrivare.",
        "cancellation",
    ),
    (
        "Volevo disdire la prenotazione BUBY-2026-5678: possiamo spostarla al mese prossimo?",
        "cancellation",
    ),
    (
        "Mi vedo costretto a rinunciare al soggiorno per la mia famiglia. "
        "Rendete l'acconto sotto forma di voucher?",
        "cancellation",
    ),
    # complaint — slot PROBLEMS
    (
        "Soggiorno dal 5 agosto: purtroppo la camera era sporca "
        "e il bagno non era stato pulito. Chiedo un rimborso.",
        "complaint",
    ),
    (
        "Il condizionatore non funzionava e abbiamo passato la notte al caldo. "
        "Non e' accettabile per un hotel della vostra categoria.",
        "complaint",
    ),
    (
        "C'era rumore in corridoio fino alle due di notte. Nessuno ha risposto "
        "alle nostre richieste in reception.",
        "complaint",
    ),
    (
        "Abbiamo trovato la biancheria da letto macchiata. Pretendo una spiegazione.",
        "complaint",
    ),
    (
        "Il personale della reception e' stato scortese. "
        "Ho pagato per un servizio che non ho ricevuto.",
        "complaint",
    ),
    (
        "La doccia perdeva acqua in tutto il bagno. Scuse formali e rimborso per favore.",
        "complaint",
    ),
    (
        "Ci hanno assegnato una camera diversa da quella prenotata. "
        "Abbiamo dovuto cambiare camera alle undici di sera.",
        "complaint",
    ),
    (
        "L'ascensore era guasto e la nostra camera era al quarto piano.",
        "complaint",
    ),
    (
        "Il wifi non ha funzionato per tutto il soggiorno. "
        "Se non cambia nulla dovro' scrivere una recensione molto negativa.",
        "complaint",
    ),
    # special_request — slot REQUESTS + frasi template
    (
        "Ho prenotato BUBY-2026-1234 e vorrei chiedere una culla per un neonato di otto mesi.",
        "special_request",
    ),
    (
        "Viaggiamo con mia moglie dal 15 agosto: "
        "potete preparare un letto matrimoniale con materasso rigido?",
        "special_request",
    ),
    (
        "Sono Mario Rossi, arrivo il 3 settembre. "
        "Sarebbe possibile avere una colazione senza glutine per una persona celiaca?",
        "special_request",
    ),
    (
        "Prenotazione BUBY-2026-5678: chiedo il check-in anticipato alle undici.",
        "special_request",
    ),
    (
        "Festeggiamo un anniversario il 20 settembre: possiamo avere un tavolo per due "
        "al ristorante?",
        "special_request",
    ),
    (
        "Con la mia famiglia dal 1 ottobre avremmo bisogno di cuscini anallergici.",
        "special_request",
    ),
    (
        "Nella prenotazione avevo chiesto un transfer dall'aeroporto: e' stato registrato?",
        "special_request",
    ),
    (
        "Arriveremo tardi, verso mezzanotte del 15 agosto. "
        "Possiamo avere una cena vegetariana per due in camera?",
        "special_request",
    ),
    # availability — template T1-T8
    (
        "Buongiorno, vorrei sapere se avete disponibilita' per due persone "
        "dal 10 agosto per tre notti.",
        "availability",
    ),
    (
        "Avete camere libere nel weekend del 20 luglio?",
        "availability",
    ),
    (
        "Cercavo una Doppia Classic per due persone dal 5 al 7 agosto. E' ancora disponibile?",
        "availability",
    ),
    (
        "Prima di prenotare vorrei il preventivo per la Matrimoniale Superior.",
        "availability",
    ),
    (
        "Mi servirebbe una Camera Familiare per due notti a partire dal 1 settembre.",
        "availability",
    ),
    (
        "Siamo in due e cerchiamo alloggio dal 15 agosto per quattro notti.",
        "availability",
    ),
    (
        "E' rimasta qualche camera per il ponte del 2 giugno? Saremmo in due.",
        "availability",
    ),
    # info — template T1-T8
    (
        "A che ora e' il check-in a Buby Lago? Arriviamo il 10 agosto.",
        "info",
    ),
    (
        "La Doppia Classic ha l'aria condizionata? Sarei li' dal 15 luglio.",
        "info",
    ),
    (
        "C'e' un parcheggio vicino a Buby Montagna? Arriviamo in auto il 20 agosto.",
        "info",
    ),
    (
        "La colazione e' inclusa nella tariffa del 10 settembre?",
        "info",
    ),
    (
        "Posso lasciare i bagagli prima del check-in il 5 agosto?",
        "info",
    ),
    (
        "Quanti chilometri dista Buby Lago dal centro?",
        "info",
    ),
    (
        "La piscina e' aperta a fine ottobre?",
        "info",
    ),
    (
        "Accettate buoni pasto per il soggiorno dal 10 agosto?",
        "info",
    ),
]

# ── fixture urgenza ───────────────────────────────────────────────────────────
# (testo, categoria, urgenza attesa) — derivato dai valori urgency dei template

FIXTURES_URGENCY: list[tuple[str, str, str]] = [
    # info: sempre low
    ("A che ora e' il check-in?", "info", "low"),
    ("C'e' un parcheggio?", "info", "low"),
    # availability low (default)
    ("Avete camere libere dal 10 agosto per una settimana?", "availability", "low"),
    ("Ho prenotato, e' ancora disponibile?", "availability", "low"),
    # availability medium (weekend o ponte)
    ("Avete posto per due nel weekend del 20 luglio?", "availability", "medium"),
    ("E' rimasta qualche camera per il ponte del 2 giugno?", "availability", "medium"),
    # cancellation medium (default)
    (
        "Purtroppo devo annullare la prenotazione. Cosa devo fare per non perdere l'anticipo?",
        "cancellation",
        "medium",
    ),
    (
        "E' possibile cancellarla senza penali?",
        "cancellation",
        "medium",
    ),
    (
        "Volevo disdire la prenotazione: possiamo spostarla?",
        "cancellation",
        "medium",
    ),
    (
        "Rinuncio al soggiorno. Rendete l'acconto sotto forma di voucher?",
        "cancellation",
        "medium",
    ),
    # cancellation high (problema di salute / volo / non rimborsabile / tutto cambiato)
    (
        "Ho un problema di salute e non possiamo venire.",
        "cancellation",
        "high",
    ),
    (
        "Il volo e' stato cancellato e non riusciamo ad arrivare.",
        "cancellation",
        "high",
    ),
    (
        "La mia tariffa era non rimborsabile: c'e' margine per un cambio data?",
        "cancellation",
        "high",
    ),
    (
        "E' cambiato tutto all'ultimo momento. Fatemi sapere le condizioni.",
        "cancellation",
        "high",
    ),
    # complaint high (default)
    (
        "Il condizionatore non funzionava. Non e' accettabile.",
        "complaint",
        "high",
    ),
    (
        "La biancheria da letto era macchiata. Pretendo una spiegazione.",
        "complaint",
        "high",
    ),
    # complaint medium (recensione negativa)
    (
        "Se non cambia nulla dovro' scrivere una recensione molto negativa.",
        "complaint",
        "medium",
    ),
    # special_request low (default)
    (
        "Vorrei chiedere una culla per un neonato di otto mesi.",
        "special_request",
        "low",
    ),
    (
        "Potete preparare un letto matrimoniale con materasso rigido?",
        "special_request",
        "low",
    ),
    # special_request medium (anniversario / supplemento / mezzanotte / tardi)
    (
        "Festeggiamo un anniversario il 20 settembre: possiamo avere un tavolo?",
        "special_request",
        "medium",
    ),
    (
        "C'e' un supplemento per il posto auto con ricarica elettrica?",
        "special_request",
        "medium",
    ),
    (
        "Arriveremo tardi, verso mezzanotte del 15 agosto.",
        "special_request",
        "medium",
    ),
    # billing high (default)
    (
        "Vedo un addebito di 50 euro che non riconosco. Sulla carta vedo questo.",
        "billing",
        "high",
    ),
    (
        "Nella fattura c'e' una tassa di soggiorno. Chiedo la correzione e il rimborso.",
        "billing",
        "high",
    ),
    (
        "Ho pagato il conto ma ora trovo un addebito per il minibar. Non ho firmato nulla.",
        "billing",
        "high",
    ),
    (
        "Prima di procedere per altra via, vorrei capire da dove arriva questa cifra.",
        "billing",
        "high",
    ),
    (
        "Se non si risolve dovro' chiedere il chargeback alla carta.",
        "billing",
        "high",
    ),
    # billing medium (dettaglio consumato / pacchetto incluso / fattura corretta)
    (
        "Potete mandarmi il dettaglio di quello che abbiamo consumato?",
        "billing",
        "medium",
    ),
    (
        "Era incluso nel pacchetto che avevo scelto.",
        "billing",
        "medium",
    ),
    (
        "Chiedo una fattura corretta: compare un importo non giusto.",
        "billing",
        "medium",
    ),
]


@pytest.mark.parametrize("text,expected", FIXTURES_CATEGORY)
def test_classify_category(text: str, expected: str) -> None:
    assert classify_category(text) == expected


@pytest.mark.parametrize("text,category,expected", FIXTURES_URGENCY)
def test_classify_urgency(text: str, category: str, expected: str) -> None:
    assert classify_urgency(text, category) == expected


def test_render_draft_contiene_nome_struttura() -> None:
    """render_draft deve includere il nome della struttura in ogni bozza."""
    for cat in CATEGORIES:
        for property_name in PROPERTY_NAMES.values():
            draft = render_draft(cat, property_name)
            assert property_name in draft, (
                f"Nome struttura '{property_name}' non trovato nella bozza di {cat}"
            )
            assert len(draft) > 50, f"Bozza troppo corta per categoria {cat}"


def test_render_draft_tutte_le_categorie() -> None:
    """Ogni categoria produce una bozza non vuota."""
    for cat in CATEGORIES:
        draft = render_draft(cat, "Buby Lago")
        assert isinstance(draft, str) and draft.strip(), f"Bozza vuota per categoria {cat}"


def test_pipeline_non_legge_gold() -> None:
    """Anti-leakage (a): email_nlp.py non referenzia email_gold.csv.

    Verifica statica sull'import-graph: il modulo classificatore non deve
    mai leggere o importare il file gold.
    """
    from pathlib import Path

    nlp_path = Path(__file__).resolve().parents[1] / "etl" / "email_nlp.py"
    source = nlp_path.read_text()
    assert "email_gold" not in source, "email_nlp.py referenzia email_gold — anti-leakage violato"
    assert "gold.csv" not in source, "email_nlp.py referenzia gold.csv — anti-leakage violato"


# ── eval math su fixture ──────────────────────────────────────────────────────


def test_compute_metrics_perfetto() -> None:
    """compute_metrics: predizioni perfette -> macro-F1 = 1.0."""
    from etl.classify_emails import compute_metrics

    preds = [
        {"id": 1, "category": "billing", "urgency": "high"},
        {"id": 2, "category": "cancellation", "urgency": "medium"},
        {"id": 3, "category": "info", "urgency": "low"},
    ]
    gold = {
        1: {"category": "billing", "urgency": "high"},
        2: {"category": "cancellation", "urgency": "medium"},
        3: {"category": "info", "urgency": "low"},
    }
    m = compute_metrics(preds, gold)
    assert m["category"]["macro_f1"] == 1.0
    assert m["urgency"]["macro_f1"] == 1.0
    assert m["gold_alignment"]["ids_matched"] == 3


def test_compute_metrics_un_errore() -> None:
    """compute_metrics: un errore di categoria riduce macro-F1 < 1.0."""
    from etl.classify_emails import compute_metrics

    preds = [
        {"id": 1, "category": "billing", "urgency": "high"},
        {"id": 2, "category": "info", "urgency": "medium"},  # sbagliato (atteso: cancellation)
        {"id": 3, "category": "info", "urgency": "low"},
    ]
    gold = {
        1: {"category": "billing", "urgency": "high"},
        2: {"category": "cancellation", "urgency": "medium"},
        3: {"category": "info", "urgency": "low"},
    }
    m = compute_metrics(preds, gold)
    assert m["category"]["macro_f1"] < 1.0
    # urgency e' ancora corretta
    assert m["urgency"]["macro_f1"] == 1.0


def test_compute_metrics_confusion_matrix_diagonale() -> None:
    """compute_metrics: predizioni perfette -> confusion matrix diagonale."""
    from etl.classify_emails import compute_metrics

    labels = ["availability", "cancellation", "billing"]
    preds = [{"id": i + 1, "category": lbl, "urgency": "low"} for i, lbl in enumerate(labels)]
    gold = {i + 1: {"category": lbl, "urgency": "low"} for i, lbl in enumerate(labels)}
    m = compute_metrics(preds, gold)
    cm = m["category"]["confusion_matrix"]["matrix"]
    # i label presenti nella confusion matrix includono TUTTE le categorie (CATEGORIES)
    # i label nel gold sono solo 3 su 6, gli altri avranno 0 ovunque
    for i, lbl in enumerate(m["category"]["confusion_matrix"]["labels"]):
        for j, lbl2 in enumerate(m["category"]["confusion_matrix"]["labels"]):
            if lbl in labels and lbl2 in labels:
                expected = 1 if lbl == lbl2 else 0
                assert cm[i][j] == expected, f"cm[{lbl}][{lbl2}] = {cm[i][j]}, atteso {expected}"
