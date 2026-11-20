# NLP recensioni D14: sentiment e topic al momento della query

## Cos'è

È la componente che analizza i testi delle 1.638 recensioni TripAdvisor:
assegna un sentiment (positivo/negativo/neutro con punteggio), estrae i topic
(pulizia, personale, posizione, colazione, rumore, rapporto qualità-prezzo) e
produce una sintesi mensile per proprietà. Insieme al classificatore email,
soddisfa il requisito minimo di elaborazione testi (R6) e risponde all'obiettivo
"individuare i fattori che influenzano soddisfazione e reputazione" (R1).

## Perché l'abbiamo disegnato così

La decisione chiave è S8 (pre-freeze): **gli output si calcolano al momento
della query, non si salvano in tabelle derivate**. Perché? Lo schema si
congelava al SAL 1: aggiungere tabelle per sentiment/topic dopo il freeze
avrebbe richiesto un contract-bump. Il delivery-plan §4 permette esplicitamente
il calcolo a query-time, quindi è la strada che sopravvive al freeze senza
nuove migrazioni. Persistere gli output più avanti è possibile, ma con la
procedura scritta. Il wording del contratto è stato allineato a questa
decisione (WP2b: da "live in a derived table" a "computed at query time").

Le scelte tecniche (ADR 0003 §5):

- **Sentiment multilingue preaddestrato, nessun training.** Usiamo
  `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual` (revisione
  fissata). Multilingue perché l'ADR lo richiede per il sentiment, anche se
  il corpus è solo inglese.
- **Topic con zero-shot NLI.** "Zero-shot" significa che il modello classifica
  senza essere stato addestrato su quelle categorie: gli si dà il testo e una
  lista di etichette candidate, e lui valuta quanto ciascuna si applica.
  Usiamo `facebook/bart-large-mnli` con le 6 categorie ADR e soglie calibrate
  su una probe di 20 recensioni annotate a mano (F1 della probe dichiarato
  OTTIMISTICO: campione piccolo, stesso corpus, annotatore unico). Il corpus
  è solo inglese, quindi un modello NLI inglese è giustificato.
- **Sintesi mensili estrattive, non LLM.** Selezioniamo frasi rappresentative
  dai testi (lead-bias pesato sul sentiment), non generiamo testo nuovo.
  Niente LLM perché le chiavi sono gated (O2/HA-05). Sono 24 sintesi (2
  proprietà × 12 mesi).

Abbiamo scartato il fine-tuning (niente budget, e i voti reali esistono già
come weak labels), la persistenza immediata in tabelle (violazione del freeze)
e le sintesi LLM (chiavi umane non disponibili).

## Com'è fatto in pratica

- `data/etl/nlp.py`: le funzioni query-time (sentiment, topic, sintesi) e la
  logica di valutazione.
- `data/etl/run_review_nlp.py`: lo script che esegue su tutti i 1.638 body,
  letti dal database in SOLA LETTURA. Non scrive mai output nel database
  (decisione S8).
- Output: `data/eval/review_nlp_metrics.json` e `review_summaries.json`
  committati; il CSV delle predizioni è locale/gitignored (riproducibile).

Scelte operative documentate (perché i numeri siano onesti):

- **Troncamento**: i topic a 256 token (25,64% dei body troncati), il sentiment
  a 512 (limite del modello, 6,84%). Il runtime a 1024 token sarebbe stato
  ~8 ore; a 256 è 2h21m misurati (la stima iniziale ~4h è distinta dal dato
  misurato).
- **Modelli sequenziali**: con 8GB di RAM, caricare entrambi i modelli insieme
  farebbe swapping. Uno alla volta.
- CPU fp32, 4 thread, batch ordinati per lunghezza (meno padding).

La valutazione usa **weak labels**: i voti reali degli ospiti (overall e le
cinque dimensioni) come riferimento, non etichette generate dal modello. È
onesta per costruzione: le etichette non vengono dal modello che valutiamo.
Correlazione di Spearman pooled sentiment-vs-overall 0.5517, Pearson 0.5894;
per proprietà 0.6266 (Lago) e 0.4370 (Montagna). L'orchestratore ha ricalcolato
indipendentemente tutte le correlazioni da predizioni + database: match esatto.

Il contratto congelato NON espone un endpoint per output di modello
(`ReviewSummary` sono voti reali, "not model output"). Esporre sentiment/topic
via API sarebbe un contract-bump futuro: per ora l'NLP vive a livello di
analisi e report, e la pagina Reputazione usa i voti reali.

## Limiti e cosa può andare storto

- Zero-shot preaddestrato, nessun training: la qualità è quella del modello
  generico, non tarata sul dominio hotel. Le soglie della probe sono ottimistiche.
- Il troncamento a 256 token perde informazione nei body lunghi: è un
  compromesso runtime/qualità dichiarato, con tasso di troncamento nel report.
- Il corpus è solo inglese e del 2012: nessuna analisi congiunta per mese con
  le prenotazioni (S4), nessuna pretesa di causalità.
- Il run completo richiede ~2GB di pesi e ore di CPU: non gira in CI (sarebbe
  proibitivo), ma è riproducibile con un comando documentato.

## Riferimenti

- [ADR 0003 §5: piano NLP](../adr/0003-data-sources.md)
- [Analisi reputazione NLP](../analysis/reputation-nlp.md)
- [Valutazione e anti-leakage](valutazione-anti-leakage.md)
- [Dizionario dati: decisione S8](../data-dictionary.md)
- Codice: `data/etl/nlp.py`, `data/etl/run_review_nlp.py`
