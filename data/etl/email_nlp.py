"""Email NLP (D15): classificatore lessicale + template bozze risposta (italiano).

Tecnica: regex derivate dal vocabolario dei template e degli slot del generatore
(data/etl/gen_emails.py, seed 42). Corpus sintetico 8+ template/categoria con
slot noti → F1 atteso elevato. NON generalizzabile a email reali.
Zero training, zero LLM, zero lettura del gold (anti-leakage ADR 0003 §6).

Funzioni esportate (pure, nessun I/O):
  classify_category(text) -> str   — una delle 6 categorie
  classify_urgency(text, category) -> str  — low / medium / high
  render_draft(category, property_name) -> str  — bozza in italiano
"""

from __future__ import annotations

import re

CATEGORIES = ["availability", "cancellation", "complaint", "special_request", "billing", "info"]
URGENCIES = ["low", "medium", "high"]
PROPERTY_NAMES = {1: "Buby Lago", 2: "Buby Montagna"}

# ── category patterns ─────────────────────────────────────────────────────────
# Ordine: dal segnale più specifico al più generico.
# billing: vocabolario finanziario univoco (addebito, fattura, tassa di soggiorno,
#   chargeback, minibar, anticipo versato, supplemento animali) — slot BILLS del generatore
_PAT_BILLING = re.compile(
    r"addebito|fattura|tassa di soggiorno|chargeback|sulla carta|"
    r"addebitato|anticipo versato|supplemento animali|minibar|"
    r"differenza di \d|questa cifra|la cifra|"
    r"ho pagato il conto.*ora trovo|non ho firmato nulla|"
    r"incluso nel pacchetto",
    re.IGNORECASE,
)

# cancellation: annull*/cancell*/disdire/rinunciare/voucher/non possiamo venire
_PAT_CANCEL = re.compile(
    r"\bannull|\bcancell|\bdisdire\b|\brinunciare\b|\bvoucher\b|non possiamo venire",
    re.IGNORECASE,
)

# complaint: slot PROBLEMS del generatore + frasi escalation
# (tutti i template complaint contengono uno degli slot PROBLEMS)
_PAT_COMPLAINT = re.compile(
    r"bagno non era stato pulito|condizionatore non funzionava|"
    r"rumore in corridoio|colazione.*scarsa|biancheria.*macchiata|"
    r"personale.*scortese|doccia perdeva|camera.*diversa.*prenotat|"
    r"ascensore.*guasto|wifi non ha funzionato|"
    r"non [eè][''\s]{0,2}accettabile|pretendo|scuse formali|"
    r"nessuno ha risposto|ho pagato per un servizio che non ho ricevuto",
    re.IGNORECASE,
)

# special_request: slot REQUESTS del generatore + frasi richiesta
_PAT_SPECIAL = re.compile(
    r"\bculla\b|materasso rigido|colazione senza glut|"
    r"check-in anticip|transfer dall|cuscini anallerg|"
    r"cena vegetar|ricarica elettr|posto auto.*ricaric|"
    r"tavolo per due|un tavolo per|"
    r"vorrei chiedere|avremmo bisogno|potete preparare|"
    r"e['']['\s]? stato registrato",
    re.IGNORECASE,
)

# availability: disponibil*/camere libere/preventivo/cerchiamo alloggio
_PAT_AVAIL = re.compile(
    r"disponibil|camere libere|avete posto|e['']['\s]? rimasta qualche camera|"
    r"\bpreventivo\b|ancora disponibile|cerchiamo alloggio|prima di prenotare|"
    r"mi servirebbe una|mi servirebbe.*camera",
    re.IGNORECASE,
)

# info: informazioni pratiche su struttura/servizi (default finale)
_PAT_INFO = re.compile(
    r"a che ora.*check-in|check-in.*a che ora|"
    r"ha l[''`]aria condizionata|"
    r"\bparcheggio\b|"
    r"colazione.*inclusa|inclusa.*nella tariffa|"
    r"lasciare.*bagagli|"
    r"quanti chilometri|"
    r"\bpiscina\b|"
    r"buoni pasto",
    re.IGNORECASE,
)

# ordine priorità: da vocabolario più esclusivo a più generico
_CATEGORY_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("billing", _PAT_BILLING),
    ("cancellation", _PAT_CANCEL),
    ("complaint", _PAT_COMPLAINT),
    ("special_request", _PAT_SPECIAL),
    ("availability", _PAT_AVAIL),
    ("info", _PAT_INFO),
]


def classify_category(text: str) -> str:
    """Restituisce la categoria dell'email (una delle 6 previste)."""
    for cat, pat in _CATEGORY_RULES:
        if pat.search(text):
            return cat
    return "info"  # fallback: info è il tipo più generico


# ── urgency patterns ──────────────────────────────────────────────────────────
# Strategia: valore di default per categoria + override testuale.
# Derivato dai valori urgency dei template (gen_emails.py TEMPLATES[*][*].urgency).

# availability medium: richiesta per weekend o ponte (template T5, T8)
_URG_AVAIL_MED = re.compile(
    r"weekend|ponte del|rimasta qualche camera per il ponte",
    re.IGNORECASE,
)

# cancellation high: salute, volo cancellato, tariffa non rimborsabile, tutto cambiato (T3,T4,T5,T8)
_URG_CANCEL_HIGH = re.compile(
    r"problema di salute|volo.*cancellat|non rimborsabile|cambiato tutto",
    re.IGNORECASE,
)

# complaint medium: minaccia recensione negativa = urgency più bassa (T7)
_URG_COMPL_MED = re.compile(r"recensione.*negativa|se non cambia", re.IGNORECASE)

# special_request medium: anniversario, supplemento, arrivo tardi notte (T5,T6,T8)
_URG_SPEC_MED = re.compile(
    r"anniversario|supplemento|mezzanotte|arriveremo tardi",
    re.IGNORECASE,
)

# billing medium: richiesta dettaglio o pacchetto incluso, non contestazione urgente (T4,T5,T6)
_URG_BILL_MED = re.compile(
    r"dettaglio.*consumat|consumat.*dettaglio|mandarmi il dettaglio|"
    r"incluso nel pacchetto|fattura corretta",
    re.IGNORECASE,
)


def classify_urgency(text: str, category: str) -> str:
    """Restituisce l'urgenza: low / medium / high.

    Default per categoria (derivato dalla distribuzione dei template):
      info           → low  (tutti i template: low)
      availability   → low  (6/8 low, 2/8 medium — override testuale)
      special_request→ low  (5/8 low, 3/8 medium — override testuale)
      cancellation   → medium (5/8 medium, 3/8 high — override testuale)
      complaint      → high  (7/8 high, 1/8 medium — override testuale)
      billing        → high  (5/8 high, 3/8 medium — override testuale)
    """
    if category == "info":
        return "low"
    if category == "availability":
        return "medium" if _URG_AVAIL_MED.search(text) else "low"
    if category == "cancellation":
        return "high" if _URG_CANCEL_HIGH.search(text) else "medium"
    if category == "complaint":
        return "medium" if _URG_COMPL_MED.search(text) else "high"
    if category == "special_request":
        return "medium" if _URG_SPEC_MED.search(text) else "low"
    if category == "billing":
        return "medium" if _URG_BILL_MED.search(text) else "high"
    return "low"


# ── draft reply templates ─────────────────────────────────────────────────────
# Template per categoria, in italiano, con {property} come segnaposto.
# Tono: cortese, non impegnativo (HITL: lo staff rivede prima di inviare).

_DRAFT_TEMPLATES: dict[str, str] = {
    "availability": (
        "Gentile ospite,\n\n"
        "grazie per averci contattato. "
        "Siamo lieti di verificare la disponibilità per il periodo da lei indicato "
        "presso {property}.\n\n"
        "La ricontatteremo al più presto con le informazioni richieste e, "
        "se possibile, con un preventivo personalizzato.\n\n"
        "Cordiali saluti,\n"
        "Il team di {property}"
    ),
    "cancellation": (
        "Gentile ospite,\n\n"
        "abbiamo ricevuto la sua richiesta e ci dispiace "
        "non poterla accogliere come previsto presso {property}.\n\n"
        "Stiamo verificando le condizioni della sua prenotazione e la "
        "ricontatteremo al più presto per confermare la procedura e "
        "le eventuali opzioni disponibili.\n\n"
        "Cordiali saluti,\n"
        "Il team di {property}"
    ),
    "complaint": (
        "Gentile ospite,\n\n"
        "la ringraziamo per averci segnalato il problema riscontrato "
        "durante il suo soggiorno presso {property}.\n\n"
        "Ci scusiamo sinceramente per il disagio. "
        "Abbiamo preso atto della sua segnalazione e valuteremo la situazione "
        "con la massima attenzione, ricontattandola al più presto.\n\n"
        "Cordiali saluti,\n"
        "Il team di {property}"
    ),
    "special_request": (
        "Gentile ospite,\n\n"
        "grazie per averci comunicato le sue esigenze. "
        "Faremo del nostro meglio per soddisfare la sua richiesta "
        "durante il soggiorno presso {property}.\n\n"
        "La ricontatteremo per confermare la disponibilità e i dettagli del servizio.\n\n"
        "Cordiali saluti,\n"
        "Il team di {property}"
    ),
    "billing": (
        "Gentile ospite,\n\n"
        "grazie per averci segnalato la questione relativa alla fatturazione. "
        "Abbiamo preso in carico la sua richiesta e stiamo verificando "
        "i dettagli con il nostro ufficio amministrativo.\n\n"
        "La ricontatteremo al più presto con una risposta e, "
        "se necessario, con la correzione dovuta.\n\n"
        "Cordiali saluti,\n"
        "Il team di {property}"
    ),
    "info": (
        "Gentile ospite,\n\n"
        "grazie per averci contattato. "
        "Siamo a sua disposizione per fornirle tutte le informazioni di cui necessita "
        "su {property}.\n\n"
        "Non esiti a contattarci per ulteriori chiarimenti.\n\n"
        "Cordiali saluti,\n"
        "Il team di {property}"
    ),
}


def render_draft(category: str, property_name: str) -> str:
    """Restituisce la bozza di risposta per la categoria e la struttura indicate."""
    template = _DRAFT_TEMPLATES.get(category, _DRAFT_TEMPLATES["info"])
    return template.format(property=property_name)
