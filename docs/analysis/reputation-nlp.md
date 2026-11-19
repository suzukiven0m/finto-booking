# Reputazione e NLP delle recensioni (D14, WP9)

| | |
|---|---|
| Data | 2026-11-19 (run completato il 2026-11-19, ~2 h 41 min di inferenza CPU) |
| Branch | `fix/wp9-review-nlp` (base `master` @ `74690c5`, v1.0.0 congelato) |
| Sorgente | `reviews` dal DB, **sola lettura** (1.638 body, 0 nulli). Mai `guest_requests`, mai il gold delle email |
| Output | `data/eval/review_nlp_predictions.csv` (solo locale, gitignored), `data/eval/review_nlp_metrics.json` e `data/eval/review_summaries.json` (committati). Tutti i numeri di questo report vengono dal metrics JSON |
| Decisioni di riferimento | ADR 0003 §5 (NLP, etichette deboli), dizionario «Decisioni pre-freeze» S8 (output al momento della query), S4 (zero overlap temporale) |

**Perimetro.** Il contratto congelato non espone alcun endpoint di output del
modello (`ReviewSummary` = soli voti reali degli ospiti): questo pacchetto è
solo livello DATI. L'esposizione API è un contract-bump successivo (nuovo ADR +
bump di `info.version` + migrazione), non questo lavoro. Nessun output del
modello è scritto nel DB (S8): il run legge con una SELECT e scrive i suoi
artefatti in `data/eval/`. Verificato prima e dopo: `reviews` = 1.638 righe,
`guest_requests.urgency` tutta NULL (800 righe), schema invariato (5 tabelle).

## 1. Metodo

### 1.1 Sentiment

- Modello: `cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual`,
  revision `82107f4ccba672c9ab1eee538e727e462cad21de`. Multilingue, 3 classi
  (negative/neutral/positive), **preaddestrato, nessun training**.
- Punteggio continuo: `P(positive) − P(negative)` in [−1, 1]; label = argmax
  delle 3 classi. La sola probabilità della classe vincente non è monotona
  rispetto al voto 1–5, la differenza sì: è la forma che si correla con i voti
  reali (ADR 0003 §5).
- Troncamento a **512 token**: è il limite del modello (xlm-roberta), non una
  scelta di runtime. Troncati 112 body su 1.638 (**6,84%**).

### 1.2 Topics (zero-shot NLI multi-label)

- Modello: `facebook/bart-large-mnli`, revision
  `d7645e127eaf1aefc7862fd59a17a5aa8558b8ce`. Zero-shot, **nessun training**,
  6 topic dell'ADR: cleanliness, staff, location, breakfast, noise, value.
  Il corpus è solo inglese (dizionario §1): un modello NLI inglese è
  appropriato, non serve addestrare un classificatore.
- Template di ipotesi: `This review discusses {}.`; il topic value è presentato
  come «value for money» (senza «for money» l'etichetta è ambigua).
- **Soglie per-topic calibrate**, non la soglia naturale 0.5: gli score NLI
  sono gonfiati (es. «value for money» ~0.93 su recensioni che non parlano di
  prezzo, location ~0.79 senza menzione). Calibrazione su una probe di **20
  recensioni** (`id % 82 = 7`), 120 giudizi di menzione annotati a mano sul
  testo visto dal modello; per ogni topic la soglia di massimo F1, arrotondata
  dentro il plateau ottimo:

  | Topic | Soglia | F1 sulla probe |
  |---|---:|---:|
  | cleanliness | 0.70 | 0.889 |
  | staff | 0.55 | 0.929 |
  | location | 0.70 | 0.880 |
  | breakfast | 0.50 | 0.909 |
  | noise | 0.90 | 0.933 |
  | value | 0.85 | 0.857 |

  Onestà sulla calibrazione: probe piccola, stesso corpus, annotatore unico →
  F1 **ottimistico**. Restano falsi negativi che nessuna soglia recupera
  (menzioni esplicite con score 0.21/0.35): la prevalenza dei topic è un
  segnale debole, non una misura esatta. Con soglia unica 0.5 la precisione
  sulla probe crollerebbe (value 0.526, noise 0.667, location 0.688).
- **Troncamento a 256 token per runtime** (decisione documentata, non del
  modello: bart-large arriva a 1024). Misura sul processore del run
  (i5-10210U, 4 core): ~1.3 s per coppia NLI fp32; a 1024 token la passata
  sarebbe ~8 h, a 256 è stata **2 h 21 min**. Troncati 420 body su 1.638
  (**25,64%**); la mediana è 152 token, quindi la maggioranza dei body resta
  intera. Il troncamento è esplicito (`nlp.truncate_body`) perché la pipeline
  zero-shot di transformers ignora `max_length` e troncherebbe da sola a 1024.
  Le sintesi mensili (§1.3) usano invece il body **intero**.

### 1.3 Sintesi mensile per proprietà — ESTRATTIVA

Niente LLM (O2: le sintesi generative sono human-gated e non in questo
pacchetto). Per proprietà e mese: frasi pesate dal sentiment della recensione
con lead-bias (`score − 0.01 × posizione`), filtro 4–40 parole, deduplica
testuale, prime k=3. Deterministica a parità di input; `None` se il mese è
vuoto. Output: 24 sintesi (2 proprietà × 12 mesi del 2012), ciascuna con
frase, `review_id`, `post_date` e punteggio — sempre tracciabile al testo reale.

### 1.4 Inferenza: decisioni di costo e determinismo

- **Fasi sequenziali, un modello per volta**: fp32, ~1.7 GB di pesi ciascuno;
  tenerli entrambi residenti su una macchina da 8 GB farebbe swap.
- **4 thread** (misurati: 8 peggiorano su 4 core/8 thread), batch sentiment 32
  body, batch topics 6 body (36 coppie NLI), **batch ordinati per lunghezza
  token** (meno padding). Seed 42, revision fissate, CPU fp32.
- **Crash-resiliente**: append per batch su due CSV parziali (uno per fase),
  `--resume` salta gli id già presenti; il CSV finale è il merge dei parziali.
  Con `--resume` la composizione dei batch può cambiare: le riduzioni fp32
  possono variare ~1e-6, label e topic no (soglie distanti dai bordi).
- Runtime misurato (metrics JSON): sentiment **1.177,7 s**, topics
  **8.466,0 s**, totale **9.645,3 s** (~2 h 41 min). Librerie: transformers
  4.57.6, torch 2.9.1+cpu, pandas 3.1.1 (+ scipy 1.17.1: lo spearman di
  pandas 3 passa da `scipy.stats`).

## 2. Valutazione con etichette deboli (onesta)

I voti reali 1–5 (overall + 5 dimensioni) **non sono stati generati dal
modello**: sono l'etichetta debole di ADR 0003 §5. Correlazione ≠ accuratezza;
nessun training, nessun test set held-out (zero-shot preaddestrato).

### 2.1 Sentiment previsto vs voti reali — pooled (n = 1.638)

| Dimensione | Spearman | Pearson |
|---|---:|---:|
| overall | **0.5517** | **0.5894** |
| cleanliness | 0.4154 | 0.4579 |
| value | 0.4396 | 0.4999 |
| location | 0.2126 | 0.2230 |
| rooms | 0.4565 | 0.5057 |
| sleep_quality | 0.4082 | 0.4438 |

Per proprietà (overall): **Buby Lago (1)** ρ = 0.6266, r = 0.6217 (n = 762);
**Buby Montagna (2)** ρ = 0.4370, r = 0.5171 (n = 876). Il segnale è più forte
su Buby Lago; su Buby Montagna tutte le dimensioni scendono (cleanliness
0.2633, value 0.2673, rooms 0.2862, sleep_quality 0.3416, location 0.2055 —
Spearman).

Conteggio label (pooled): negative **352**, neutral **477**, positive **809**.
Per proprietà: Buby Lago 196/277/289, Buby Montagna 156/200/520.

### 2.2 Prevalenza dei topic

| Topic | Pooled | Buby Lago (1) | Buby Montagna (2) |
|---|---:|---:|---:|
| cleanliness | 0.4664 | 0.3714 | 0.5491 |
| staff | 0.6862 | 0.7283 | 0.6495 |
| location | 0.6813 | 0.6273 | 0.7283 |
| breakfast | 0.2265 | 0.1549 | 0.2888 |
| noise | 0.1783 | 0.1654 | 0.1895 |
| value | 0.7912 | 0.7231 | 0.8505 |

Prevalenze alte = topic di cui si parla spesso, non giudizio positivo. value
(0.79) è il topic con la calibrazione più debole (F1 0.857, precisione 0.818
sulla probe): la sua prevalenza va letta con cautela.

### 2.3 Topic menzionato vs voto della dimensione (pooled)

Mappa dichiarata: cleanliness→cleanliness, location→location, value→value,
**noise→sleep_quality** (assunzione: il rumore perturba il sonno; non esiste
un voto «rumore» nel corpus). staff e breakfast non hanno dimensione: solo
prevalenza.

| Topic | Dimensione | n menzionati | Media dim. con menzione | senza | Delta |
|---|---|---:|---:|---:|---:|
| cleanliness | cleanliness | 764 | 4.482 | 4.310 | +0.172 |
| location | location | 1.116 | 4.562 | 4.492 | +0.070 |
| noise | sleep_quality | 292 | 3.596 | 4.292 | **−0.696** |
| value | value | 1.296 | 4.048 | 3.243 | **+0.805** |

Per proprietà il pattern noise è coerente: delta −0.626 (Buby Lago, n = 126)
e −0.752 (Buby Montagna, n = 166). value: +0.660 e +0.659. cleanliness:
−0.001 e +0.149; location: +0.046 e +0.131.

## 3. Cosa risponde a R1 («fattori che influenzano soddisfazione e reputazione»)

Lettura **descrittiva, non causale** (S4, §4):

1. **Il rumore è il segnale negativo più netto**: chi menziona noise ha un
   voto sleep_quality medio di 0.70 punti più basso (3.60 vs 4.29), in entrambe
   le proprietà. È il candidato principale su cui agire (insonorizzazione,
   gestione camere quiete).
2. **Le dimensioni che seguono meglio il sentiment generale** sono rooms
   (ρ 0.4565), value (0.4396), cleanliness (0.4154), sleep_quality (0.4082);
   **location è la più debole** (0.2126): il voto di posizione spiega poco il
   tono complessivo della recensione.
3. **Chi parla di value tende ad avere un voto value più alto** (+0.805):
   nella probe le menzioni di prezzo sono per lo più commenti positivi
   («great value», «worth the price»). Attenzione: è associazione, e il topic
   value è quello calibrato peggio; non va letto come «il prezzo guida la
   soddisfazione».
4. cleanliness e location hanno delta piccoli (+0.172, +0.070): se ne parla
   sia nelle recensioni alte sia in quelle basse, la menzione da sola non
   discrimina il voto.
5. Differenza tra proprietà: Buby Lago ha accordo sentiment-voti più alto
   (ρ 0.6266 vs 0.4370) e più label negative (196/762 = 25.7% vs 156/876 =
   17.8%); Buby Montagna ha più menzioni di cleanliness, breakfast e value.

## 4. Caveats (tutti vincolanti)

- **S4 — zero overlap temporale**: tutte le 1.638 recensioni sono del 2012
  (2012-01-02…2012-12-19), le prenotazioni coprono 2015-07…2017-09. Zero mesi
  in comune: nessuna analisi congiunta, comparazione **solo a livello di
  proprietà**, nessuna lettura causale tra reputazione e occupazione/ricavi.
- **Corpus solo inglese**, N = 1.638, due proprietà: statistiche descrittive,
  non inferenza su una popolazione. Il modello sentiment è multilingue ma qui
  vede solo inglese; il modello topics è NLI inglese.
- **Preaddestrati, zero-shot, nessun training**: niente fine-tuning sul corpus,
  niente train/test split; le soglie sono calibrate su una probe interna
  (ottimistica, §1.2).
- **Etichette deboli**: i voti 1–5 sono soggettivi e non generati dal modello;
  correlazione non è accuratezza. La mappa noise→sleep_quality è un'assunzione
  dichiarata. Il modello sbaglia anche su recensioni ovvie (nella probe: una
  recensione entusiasta con overall 5 classificata negative).
- **Sintesi estrattive**, non generative (O2 human-gated): nessuna parafrasi,
  solo frasi reali selezionate.
- **Troncamenti**: sentiment 512 token (limite del modello, 6.84% dei body);
  topics 256 token (scelta di runtime, 25.64%): le menzioni oltre il tetto non
  possono essere viste dal classificatore topics.
- **S8**: output query-time, mai nel DB; l'esposizione API richiede
  contract-bump.

## 5. Riproducibilità

Prerequisiti: `.venv` con `data/requirements.txt` + `backend/requirements.txt`
(`uv venv --python 3.12 .venv`; per il pin `torch==2.9.1+cpu` serve
`--index-strategy unsafe-best-match`, altrimenti la strategia first-index
cerca la wheel +cpu su PyPI e fallisce); pesi in cache HF alle due revision
sopra (`snapshot_download`); DB raggiungibile. Host→container TCP bloccato
(VPN): si usa il sidecar con la rete di Postgres, repo in sola lettura,
`data/eval` scrivibile.

Run completo (background + log; **non** è un passo di CI: ~2 GB di pesi al
primo download sarebbero proibitivi a ogni run):

```bash
nohup docker run --rm -i --network container:buby-postgres \
  -v "$PWD":/repo:ro -v "$PWD/data/eval":/repo/data/eval \
  -v "$HOME/.cache/huggingface":/root/.cache/huggingface \
  -w /repo -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 \
  -e PYTHONPATH=/repo/.venv/lib/python3.12/site-packages:/repo/backend:/repo/data \
  python:3.12-slim python data/etl/run_review_nlp.py \
  > /tmp/wp9-run.log 2>&1 &
# ripresa dopo un crash: stesso comando con --resume in coda
```

Test (CI e locale, senza scaricare pesi): dalla root del repo, nel sidecar,
`python -m pytest data/tests` — la logica non-modello (soglie/mapping,
troncamento, selezione estrattiva, metriche su fixture, helper di resume) è
coperta da `data/tests/test_review_nlp.py`; il test sulla CSV completa si salta
dove il file non c'è (pattern di `test_baseline.py`). Lint: `ruff check data/`
e `isort --check-only data/` (ruff 0.17.5, isort 9.0.2).

## 6. Riferimenti

- **Li et al. (2013)** — Jiwei Li, Myle Ott, Claire Cardie, *Identifying
  Manipulated Offerings on Review Portals*, EMNLP 2013: corpus TripAdvisor
  accademico da cui deriva `jniimi/tripadvisor-review-rating` (repository
  Apache 2.0), come da ADR 0003 («citare Li et al. (2013)»).
- ADR 0003 §5 (NLP e etichette deboli), §«Punto debole» + correzione S4;
  dizionario «Decisioni pre-freeze» S7/S8; `docs/playbooks/solo-dataset.md`.
- Modelli: cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual e
  facebook/bart-large-mnli (revision in §1 e nel metrics JSON).