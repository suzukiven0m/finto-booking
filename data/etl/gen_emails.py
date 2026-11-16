"""Genera 800 email sintetiche (italiano) + il file gold. Idempotente, seed 42.

- nel DB (guest_requests) va SOLO property_id, received_at, body: category e
  draft_reply restano NULL, li produce l'assistente (D15).
- true_category/true_urgency vivono SOLO in data/eval/email_gold.csv, che la
  pipeline non legge mai. Gli id combaciano perche' entrambi partono da
  TRUNCATE RESTART IDENTITY nella stessa esecuzione: se ricarichi le email,
  rigenera anche il gold, nello stesso run.
- nessun dato reale: nomi e indirizzi sono inventati (GDPR).

8+ template per categoria x saluti/chiusure/date/camere/slot: i testi quasi
duplicati sono rari (lezione del postmortem del 2026-11-11 sul dataset
arricchito, dove 25 testi distinti rendevano la valutazione inutile).

Gira col venv del backend:  PYTHONPATH=backend backend/.venv/bin/python data/etl/gen_emails.py
"""

import csv
import datetime as dt
import random
from collections import namedtuple

import psycopg

from app.config import DATABASE_URL

Template = namedtuple("Template", "text urgency")

rng = random.Random(42)

CATS = ["availability", "cancellation", "complaint", "special_request", "billing", "info"]
N_PER_CAT = [134, 133, 133, 133, 133, 134]  # = 800

NAMES = [
    "Mario Rossi",
    "Giulia Bianchi",
    "Luca Ferrari",
    "Anna Esposito",
    "Marco Russo",
    "Sara Romano",
    "Paolo Colombo",
    "Chiara Ricci",
    "Andrea Marino",
    "Elena Greco",
    "Stefano Bruno",
    "Francesca Gallo",
    "Davide Conti",
    "Martina De Luca",
    "Simone Mancini",
    "Valentina Costa",
    "Alessandro Giordano",
    "Ilaria Rizzo",
    "Matteo Lombardi",
    "Federica Moretti",
    "Riccardo Barbieri",
    "Silvia Fontana",
    "Nicola Santoro",
    "Laura Marchetti",
    "Fabio Caruso",
    "Beatrice Ferrara",
    "Giovanni Rinaldi",
    "Camilla Leone",
    "Tommaso Longo",
    "Arianna Gentile",
    "Enrico Martinelli",
    "Noemi Vitale",
    "Pietro Lombardo",
    "Serena Serra",
    "Claudio Coppola",
]

GREETINGS = [
    "Buongiorno,",
    "Buon giorno,",
    "Buonasera,",
    "Salve,",
    "Gentile reception,",
    "Scusate il disturbo,",
    "Ciao,",
    "Buongiorno",
]

CLOSINGS = [
    "Grazie.",
    "Grazie mille.",
    "Cordiali saluti.",
    "Resto in attesa di una risposta.",
    "Fatemi sapere al piu' presto.",
    "A presto.",
    "Vi ringrazio in anticipo.",
    "Grazie, aspetto vostre notizie.",
]

MONTHS_IT = [
    "gennaio",
    "febbraio",
    "marzo",
    "aprile",
    "maggio",
    "giugno",
    "luglio",
    "agosto",
    "settembre",
    "ottobre",
    "novembre",
    "dicembre",
]

ROOM_TYPES = [
    "Doppia Classic",
    "Matrimoniale Superior",
    "Camera Familiare",
    "Singola",
    "Suite con vista lago",
    "Tripla Standard",
    "Doppia con balcone",
]

PARTY = [
    "in due",
    "con mio marito",
    "con mia moglie",
    "con la mia famiglia",
    "da sola",
    "da solo",
    "con due bambini piccoli",
    "con un gruppo di amici",
    "con i miei genitori",
]

NIGHTS = [
    "una notte",
    "due notti",
    "tre notti",
    "un weekend lungo",
    "quattro notti",
    "una settimana",
]

PROBLEMS = [
    "la camera era sporca e il bagno non era stato pulito",
    "il condizionatore non funzionava e abbiamo passato la notte al caldo",
    "c'era rumore in corridoio fino alle due di notte",
    "la colazione era molto scarsa rispetto a quanto promesso sul sito",
    "abbiamo trovato la biancheria da letto macchiata",
    "il personale della reception e' stato scortese",
    "la doccia perdeva acqua in tutto il bagno",
    "ci hanno assegnato una camera diversa da quella prenotata",
    "l'ascensore era guasto e la nostra camera era al quarto piano",
    "il wifi non ha funzionato per tutto il soggiorno",
]

REQUESTS = [
    "una culla per un neonato di otto mesi",
    "un letto matrimoniale con materasso rigido",
    "una colazione senza glutine per una persona celiaca",
    "una camera ai piani alti, lontano dall'ascensore",
    "un posto auto con ricarica elettrica",
    "il check-in anticipato alle undici",
    "un tavolo per due al ristorante per il nostro anniversario",
    "un transfer dall'aeroporto",
    "cuscini anallergici",
    "una cena vegetariana per due",
]

BILLS = [
    "un addebito di 164,50 euro che non riconosco",
    "una tassa di soggiorno che non ci era stata comunicata",
    "una differenza di 40 euro tra la conferma e la fattura",
    "un addebito per il minibar che non abbiamo mai aperto",
    "una fattura intestata alla persona sbagliata",
    "il costo della colazione in un pacchetto che la includeva",
    "un supplemento animali di cui non sapevamo nulla",
    "l'anticipo versato che non compare in fattura",
]

TEMPLATES: dict[str, list[Template]] = {
    "availability": [
        Template(
            "{greeting} sono {name} e vorrei sapere se avete disponibilita' per {party} "
            "dal {date} per {nights}. Il preventivo online include la colazione? {closing}",
            "low",
        ),
        Template(
            "{greeting} sto organizzando un soggiorno a {property} con {party} dal {date}. "
            "Avete camere libere in quel periodo? {closing}",
            "low",
        ),
        Template(
            "{greeting} cercavo una {room} per {party} dal {date} al {date2}. "
            "E' ancora disponibile? {closing}",
            "low",
        ),
        Template(
            "{greeting} prima di prenotare vorrei la conferma che la {room} abbia la vista "
            "sul lago. Saremmo {party} dal {date}. {closing}",
            "low",
        ),
        Template(
            "{greeting} avete posto per {party} nel weekend del {date}? Se si', qual e' "
            "il prezzo migliore che potete farmi? {closing}",
            "medium",
        ),
        Template(
            "{greeting} mi servirebbe una {room} per {nights} a partire dal {date}: "
            "ne avete ancora? {closing}",
            "low",
        ),
        Template(
            "{greeting} siamo {party} e cerchiamo alloggio dal {date} per {nights}. "
            "Accettate cani di piccola taglia? {closing}",
            "low",
        ),
        Template(
            "{greeting} e' rimasta qualche camera per il ponte del {date}? "
            "Saremmo {party}, {nights}. {closing}",
            "medium",
        ),
    ],
    "cancellation": [
        Template(
            "{greeting} purtroppo devo annullare la prenotazione {ref} per la {room} "
            "dal {date}. Cosa devo fare per non perdere l'anticipo? {closing}",
            "medium",
        ),
        Template(
            "{greeting} la prenotazione {ref} dal {date} non mi serve piu': e' possibile "
            "cancellarla senza penali? {closing}",
            "medium",
        ),
        Template(
            "{greeting} sono {name}, ho prenotato per {party} dal {date} ma ho avuto un "
            "problema di salute e non possiamo venire. Posso spostare la data? {closing}",
            "high",
        ),
        Template(
            "{greeting} dovrei cancellare il soggiorno dal {date}. La mia tariffa era non "
            "rimborsabile: c'e' margine per un cambio data? {closing}",
            "high",
        ),
        Template(
            "{greeting} annullo la {room} dal {date}: il volo e' stato cancellato e non "
            "riusciamo ad arrivare. {closing}",
            "high",
        ),
        Template(
            "{greeting} volevo disdire la prenotazione {ref}: possiamo spostarla al {date2}? "
            "{closing}",
            "medium",
        ),
        Template(
            "{greeting} mi vedo costretto a rinunciare al soggiorno dal {date} per {party}. "
            "Rendete l'acconto sotto forma di voucher? {closing}",
            "medium",
        ),
        Template(
            "{greeting} cancello la prenotazione per {party} dal {date}: e' cambiato tutto "
            "all'ultimo momento. Fatemi sapere le condizioni. {closing}",
            "high",
        ),
    ],
    "complaint": [
        Template(
            "{greeting} sono {name}, camera {room} dal {date}. Purtroppo {problem}. "
            "Chiedo un rimborso o almeno delle scuse formali. {closing}",
            "high",
        ),
        Template(
            "{greeting} scrivo per segnalare che durante il soggiorno dal {date} {problem}. "
            "Non e' accettabile per un hotel della vostra categoria. {closing}",
            "high",
        ),
        Template(
            "{greeting} soggiorno a {property} dal {date}: purtroppo {problem}. Nessuno ha "
            "risposto alle nostre richieste in reception. Come pensate di rimediare? {closing}",
            "high",
        ),
        Template(
            "{greeting} sono appena tornato da {property} (camera {room}, dal {date}) e "
            "purtroppo {problem}. Abbiamo dovuto cambiare camera alle undici di sera. {closing}",
            "high",
        ),
        Template(
            "{greeting} purtroppo {problem}, e alla reception ci hanno detto che non "
            "potevano fare nulla. Pretendo una spiegazione. {closing}",
            "high",
        ),
        Template(
            "{greeting} durante il soggiorno dal {date} purtroppo {problem}. Ho pagato per "
            "un servizio che non ho ricevuto e chiedo un rimborso. {closing}",
            "high",
        ),
        Template(
            "{greeting} e' la seconda volta che soggiorno a {property} e purtroppo {problem}. "
            "Se non cambia nulla dovro' scrivere una recensione molto negativa. {closing}",
            "medium",
        ),
        Template(
            "{greeting} scrivo al ritorno da {property}: purtroppo {problem}. Speravo in uno "
            "standard diverso da quello che ho pagato. {closing}",
            "high",
        ),
    ],
    "special_request": [
        Template(
            "{greeting} ho prenotato {ref} per {party} dal {date} e vorrei chiedere {request}, "
            "se e' possibile. {closing}",
            "low",
        ),
        Template(
            "{greeting} viaggiamo {party} dal {date}: potete preparare {request}? "
            "E' un dettaglio importante per noi. {closing}",
            "low",
        ),
        Template(
            "{greeting} sono {name}, arrivo il {date}. Sarebbe possibile avere {request}? "
            "{closing}",
            "low",
        ),
        Template(
            "{greeting} prenotazione {ref}: chiedo {request}. Non e' urgente, ma ci farebbe "
            "piacere. {closing}",
            "low",
        ),
        Template(
            "{greeting} festeggiamo un anniversario il {date}: possiamo avere {request}? {closing}",
            "medium",
        ),
        Template(
            "{greeting} con {party} dal {date} avremmo bisogno di {request}. "
            "C'e' un supplemento? {closing}",
            "medium",
        ),
        Template(
            "{greeting} nella prenotazione {ref} avevo chiesto {request}: e' stato "
            "registrato? {closing}",
            "low",
        ),
        Template(
            "{greeting} arriveremo tardi, verso mezzanotte del {date}. Possiamo avere "
            "{request} in camera? {closing}",
            "medium",
        ),
    ],
    "billing": [
        Template(
            "{greeting} sono {name}, ho soggiornato a {property} dal {date} e sulla carta "
            "vedo {bill}. Potete verificare? {closing}",
            "high",
        ),
        Template(
            "{greeting} nella fattura della prenotazione {ref} c'e' {bill}. "
            "Chiedo la correzione e il rimborso. {closing}",
            "high",
        ),
        Template(
            "{greeting} alla partenza del {date} ho pagato il conto, ma ora trovo {bill}. "
            "Non ho firmato nulla del genere. {closing}",
            "high",
        ),
        Template(
            "{greeting} ho ricevuto {bill}. Potete mandarmi il dettaglio di quello che "
            "abbiamo consumato? {closing}",
            "medium",
        ),
        Template(
            "{greeting} prenotazione {ref}: nel totale c'e' {bill}. "
            "Era incluso nel pacchetto che avevo scelto. {closing}",
            "medium",
        ),
        Template(
            "{greeting} chiedo una fattura corretta per il soggiorno dal {date}: "
            "compare {bill} e non e' giusto. {closing}",
            "medium",
        ),
        Template(
            "{greeting} mi hanno addebitato {bill}. Vorrei capire da dove arriva questa "
            "cifra prima di procedere per altra via. {closing}",
            "high",
        ),
        Template(
            "{greeting} purtroppo c'e' {bill}. Se non si risolve dovro' chiedere il "
            "chargeback alla carta. {closing}",
            "high",
        ),
    ],
    "info": [
        Template(
            "{greeting} a che ora e' il check-in a {property}? Arriviamo il {date}. {closing}",
            "low",
        ),
        Template(
            "{greeting} la {room} ha l'aria condizionata? Sarei li' dal {date}. {closing}",
            "low",
        ),
        Template(
            "{greeting} c'e' un parcheggio vicino a {property}? Arriviamo in auto il {date}. "
            "{closing}",
            "low",
        ),
        Template(
            "{greeting} la colazione e' inclusa nella tariffa del {date}? {closing}",
            "low",
        ),
        Template(
            "{greeting} posso lasciare i bagagli prima del check-in il {date}? {closing}",
            "low",
        ),
        Template(
            "{greeting} quanti chilometri dista {property} dal centro? Veniamo in treno "
            "il {date}. {closing}",
            "low",
        ),
        Template(
            "{greeting} la piscina e' aperta a fine {date2}? {closing}",
            "low",
        ),
        Template(
            "{greeting} accettate buoni pasto per il soggiorno dal {date}? {closing}",
            "low",
        ),
    ],
}

# refusi realistici: accenti mancanti e doppie lettere, il significato resta
TYPO_SWAPS = [
    ("prenotazione", "prenotazzione"),
    ("camera", "cameraa"),
    ("disponibilita'", "disponibilita"),
    ("soggiorno", "soggiorrno"),
    ("colazione", "colazzione"),
]


def it_date(d: dt.date) -> str:
    return f"{d.day} {MONTHS_IT[d.month - 1]} {d.year}"


def _noise(body: str) -> str:
    if rng.random() < 0.12:
        body = body.replace(" e' ", " e ", 1)  # accento mancante (e' invece di e')
    if rng.random() < 0.08:
        old, new = rng.choice(TYPO_SWAPS)
        body = body.replace(old, new, 1)
    return body


PROPERTY = {1: "Buby Lago", 2: "Buby Montagna"}
PAST_CATS = {"complaint", "billing"}


def build(cat: str) -> tuple[int, dt.datetime, str, str]:
    """-> (property_id, received_at, body, urgency)"""
    pid = rng.choice([1, 2])
    stay = rng.randrange(1, 91)
    received = dt.datetime(2026, 9, 1, tzinfo=dt.UTC) + dt.timedelta(
        days=rng.randrange(75), hours=rng.randrange(24)
    )
    # le lamentele e le questioni di fattura parlano di un soggiorno gia' passato
    delta = -dt.timedelta(days=stay) if cat in PAST_CATS else dt.timedelta(days=stay)
    date = received + delta
    date2 = received + delta + dt.timedelta(days=rng.randrange(1, 8))
    t = rng.choice(TEMPLATES[cat])
    body = _noise(
        t.text.format(
            greeting=rng.choice(GREETINGS),
            name=rng.choice(NAMES),
            date=it_date(date.date()),
            date2=it_date(date2.date()),
            property=PROPERTY[pid],
            room=rng.choice(ROOM_TYPES),
            party=rng.choice(PARTY),
            nights=rng.choice(NIGHTS),
            ref=f"BUBY-2026-{rng.randrange(1000, 9999)}",
            problem=rng.choice(PROBLEMS),
            request=rng.choice(REQUESTS),
            bill=rng.choice(BILLS),
            closing=rng.choice(CLOSINGS),
        )
    )
    return pid, received, body, t.urgency


rows, gold = [], []
for cat, n in zip(CATS, N_PER_CAT, strict=True):
    for _ in range(n):
        pid, received, body, urgency = build(cat)
        rows.append((pid, received, body))
        gold.append((len(rows), cat, urgency))  # id = ordine di insert dopo TRUNCATE

assert len(rows) == 800 and len(gold) == 800

# gold SOLO qui, mai nel database
try:
    with open("data/eval/email_gold.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "true_category", "true_urgency"])
        w.writerows(gold)
except OSError as e:
    raise SystemExit(f"gold file non scrivibile (data/eval/): {e}") from e

url = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://")
with psycopg.connect(url) as conn, conn.cursor() as cur:
    cur.execute("TRUNCATE guest_requests RESTART IDENTITY")
    with cur.copy("COPY guest_requests (property_id,received_at,body) FROM STDIN") as cp:
        for r in rows:
            cp.write_row(r)
    conn.commit()
print(f"guest_requests: {len(rows)} email, gold: data/eval/email_gold.csv ({len(gold)} righe)")
