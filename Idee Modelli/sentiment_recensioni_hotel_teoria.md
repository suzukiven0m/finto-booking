# Analisi del sentiment delle recensioni dell'hotel

*Descrizione teorica del progetto*

---

## 1. Obiettivo

Le recensioni degli ospiti arrivano sotto forma di messaggi di testo libero. Leggerle tutte a mano richiede tempo, ed è difficile ricavarne una visione d'insieme: quali aspetti piacciono di più? Quali generano più lamentele? La situazione migliora o peggiora nel tempo?

Il progetto ha lo scopo di **analizzare automaticamente ogni recensione** e rispondere a due domande:

1. **Com'è la recensione nel complesso?** Positiva, negativa o neutra.
2. **Per quale motivo?** Quali aspetti del soggiorno vengono citati (camera, pulizia, personale, colazione, posizione, rumore, prezzo…) e con quale giudizio.

Il risultato non è solo un'etichetta per recensione. Dall'insieme delle recensioni si ottiene un quadro di **punti di forza e criticità** dell'hotel.

## 2. Il problema dal punto di vista dell'intelligenza artificiale

La classificazione del sentiment "semplice" assegna una sola etichetta a tutto il testo. Per un hotel però non basta, perché molte recensioni sono **miste**:

> *"Camera pulitissima e personale gentile, ma la colazione era scarsa e cara."*

Una sola etichetta, positiva o negativa, farebbe perdere l'informazione più utile: la camera e il personale vanno bene, la colazione va migliorata.

Per questo il problema viene trattato come **analisi del sentiment per aspetti** (in inglese *Aspect-Based Sentiment Analysis*). Per ogni aspetto citato si individua il giudizio corrispondente e la frase che lo giustifica.

## 3. Vincoli del progetto

- **Solo modelli open-source di Hugging Face.** Niente servizi esterni a pagamento né API di terze parti.
- **Esecuzione in locale.** I modelli girano sui computer o sui server dell'hotel. Le recensioni, che possono contenere dati personali, non vengono inviate a nessun servizio esterno.
- **Multilingua.** Gli ospiti scrivono in italiano, ma anche in inglese, tedesco, francese…

## 4. L'idea di base: ragionare per frasi

Il sistema non analizza la recensione in blocco. La scompone e la analizza in quattro passaggi:

1. **Suddivisione in frasi.** La recensione viene divisa usando la punteggiatura e le parole che introducono un contrasto (*"ma"*, *"però"*, *"tuttavia"*, *"purtroppo"*). In questo modo le parti positive e negative finiscono in frasi separate.
2. **Sentiment di ogni frase.** Un modello stabilisce se la frase è positiva, negativa o neutra.
3. **Categoria di ogni frase.** Un secondo modello stabilisce di quale aspetto del soggiorno parla. Le frasi che non riguardano un aspetto preciso (es. *"siamo stati qui ad agosto"*) vengono scartate.
4. **Aggregazione.** I risultati delle frasi vengono combinati nel giudizio complessivo della recensione: prevale il sentiment più frequente, e se positivi e negativi si equivalgono la recensione è considerata neutra (mista).

Per l'esempio precedente il risultato è:

| Aspetto | Giudizio | Frase |
|---|---|---|
| Pulizia | positivo | "Camera pulitissima e personale gentile" |
| Colazione | negativo | "la colazione era scarsa e cara" |
| **Complessivo** | **neutro (misto)** | |

## 5. Due fasi di sviluppo

Il progetto prevede due fasi successive. La prima produce un risultato subito, la seconda lo migliora.

### 5.1 Fase 1 – Classificazione "zero-shot" (senza addestramento)

In questa fase si usano modelli già pronti, senza addestrarli sui dati dell'hotel.

- **Per il sentiment** si usa un modello multilingue basato su **XLM-RoBERTa**, già addestrato a riconoscere positivo, negativo e neutro su testi brevi e informali, simili alle recensioni.
- **Per la categoria** si usa un modello di classificazione **zero-shot** basato su mDeBERTa. Riceve la frase e l'elenco delle categorie possibili, e valuta per ciascuna quanto è plausibile l'affermazione *"questa frase parla di…"*. La categoria più plausibile viene assegnata alla frase, purché superi una soglia minima di confidenza.

| Vantaggi | Svantaggi |
|---|---|
| Funziona subito, senza dati etichettati | Precisione limitata sul linguaggio specifico del settore alberghiero |
| Le categorie si cambiano liberamente | Fatica con ironia e frasi ambigue |
| Gira anche su computer senza GPU | Più lento, perché valuta ogni categoria separatamente |

Questa fase serve anche da **punto di riferimento**: i risultati della Fase 2 verranno confrontati con questi.

### 5.2 Fase 2 – Fine-tuning di XLM-RoBERTa

Il **fine-tuning** consiste nel prendere un modello linguistico già addestrato su enormi quantità di testo e "specializzarlo" con un numero relativamente piccolo di esempi etichettati, in questo caso le frasi delle recensioni dell'hotel. È un esempio di **transfer learning**: il modello sa già come funziona la lingua e deve solo imparare il compito specifico.

Si addestrano **due modelli distinti**:

| Modello | Parte da | Impara a |
|---|---|---|
| Sentiment | un XLM-RoBERTa già specializzato nel sentiment | riconoscere il sentiment *nel linguaggio delle recensioni d'hotel* |
| Categoria | XLM-RoBERTa "base" | assegnare le categorie scelte dall'hotel |

Il modello del sentiment parte da uno che sa già fare quel compito, quindi gli bastano pochi esempi per adattarsi. Quello delle categorie parte da zero sul compito specifico e richiede più dati.

**Preparazione dei dati.** Le recensioni reali vengono divise in frasi con lo stesso metodo usato poi in produzione. Ogni frase viene etichettata a mano con sentiment e categoria. Come ordine di grandezza servono **almeno 50–100 frasi per categoria**. Usare per l'addestramento esattamente lo stesso tipo di frasi che il modello vedrà in uso reale è importante per la qualità del risultato.

**Addestramento.** I dati vengono divisi in tre parti:
- **addestramento:** gli esempi da cui il modello impara;
- **validazione:** serve a decidere quando fermarsi. L'addestramento si interrompe da solo quando il modello smette di migliorare (*early stopping*), per evitare che impari a memoria gli esempi invece di generalizzare;
- **test:** frasi mai viste durante l'addestramento, usate solo per la valutazione finale.

La divisione è **stratificata**: ogni parte contiene le stesse proporzioni di categorie e sentiment.

**Metrica di valutazione.** La metrica principale è il **macro-F1**, che dà lo stesso peso a tutte le classi. Nelle recensioni alcune classi sono rare, per esempio quelle neutre. Un modello potrebbe ottenere un'accuratezza alta pur sbagliando sempre le classi rare, mentre il macro-F1 mette in evidenza questo problema.

## 6. Valutazione dei modelli

Dopo l'addestramento i modelli vengono valutati sul **test set**, le frasi tenute da parte. La valutazione prevede tre attività:

1. **Confronto con la Fase 1:** si misura quanto il fine-tuning migliora rispetto allo zero-shot sulle stesse frasi.
2. **Analisi per classe:** si individuano le categorie o i sentiment su cui il modello sbaglia di più.
3. **Analisi degli errori:** le frasi classificate male vengono riviste a mano. Gli errori di solito rivelano:
   - **etichette sbagliate** nei dati di addestramento, da correggere;
   - **categorie che si sovrappongono** (es. "camera" e "pulizia"), da unire o definire meglio;
   - **classi con pochi esempi**, da arricchire.

## 7. Utilizzo nell'applicazione dell'hotel

### 7.1 Analisi di tutte le recensioni

Il sistema analizza l'intero archivio delle recensioni e produce due elenchi:
- una riga per **recensione**, con il giudizio complessivo;
- una riga per **ogni motivo trovato**, con categoria, giudizio e frase originale.

### 7.2 Statistiche per l'hotel

Dagli elenchi si ottiene una **tabella per categoria**: per ogni aspetto, quante volte è citato positivamente, neutralmente e negativamente, e la percentuale di lamentele. Per esempio:

| Aspetto | Positivi | Neutri | Negativi | % negativi |
|---|---|---|---|---|
| Rumore | 12 | 5 | 48 | 74 % |
| Colazione | 40 | 8 | 31 | 39 % |
| Pulizia | 55 | 3 | 14 | 19 % |
| Personale | 88 | 6 | 9 | 9 % |

*(dati puramente illustrativi)*

In questo esempio la direzione capirebbe subito che il **rumore** è la criticità principale e il **personale** il punto di forza. Per ogni aspetto sono disponibili anche esempi concreti delle frasi degli ospiti. Se le recensioni hanno una data, si può seguire l'andamento nel tempo, per esempio per verificare se un intervento sulla colazione ha ridotto le lamentele.

### 7.3 Integrazione tramite API

Il modello viene esposto come un **servizio interno** (API web) sul server dell'hotel. L'applicazione gli invia il testo di una recensione e riceve il giudizio complessivo e l'elenco dei motivi in un formato strutturato. Così:
- l'analisi avviene in tempo reale all'arrivo di ogni nuova recensione;
- qualsiasi applicazione, scritta in qualsiasi linguaggio, può usare il servizio;
- i dati non lasciano mai l'infrastruttura dell'hotel.

## 8. Miglioramento continuo

Il modello non è un prodotto finito: migliora con l'uso. Il ciclo previsto è:

1. periodicamente si estrae un campione di recensioni nuove, privilegiando i casi incerti;
2. le previsioni sbagliate vengono corrette a mano e aggiunte ai dati di addestramento;
3. il modello viene riaddestrato e rivalutato **sempre sullo stesso test set**, così il confronto è corretto;
4. il nuovo modello sostituisce il precedente **solo se è migliorato**. Le versioni precedenti vengono conservate per poter tornare indietro.

## 9. Limiti e possibili sviluppi

**Limiti attuali:**
- l'**ironia** e il sarcasmo restano difficili da riconoscere;
- una frase che cita **più aspetti insieme** (*"camera e bagno sporchi"*) viene assegnata a una sola categoria;
- la suddivisione in frasi si basa su regole semplici e può sbagliare con testi molto scorretti o privi di punteggiatura;
- la qualità dipende dalla **quantità e coerenza delle etichette** inserite a mano.

**Possibili sviluppi:**
- classificazione **multi-etichetta**, cioè più categorie per frase;
- **cruscotto grafico** con l'andamento mensile per categoria;
- **avvisi automatici** alla direzione quando arriva una recensione molto negativa;
- collegamento con l'**assistente virtuale** dell'hotel (vedi il documento dedicato), per un unico sistema di intelligenza artificiale dell'hotel.

## 10. Valore per l'hotel

- **Risparmio di tempo:** migliaia di recensioni analizzate in pochi minuti.
- **Decisioni basate sui dati:** le priorità di intervento emergono dai numeri, non da impressioni.
- **Misurazione dei risultati:** si può verificare se un cambiamento ha avuto effetto sulla soddisfazione degli ospiti.
- **Privacy e indipendenza:** nessun dato inviato a terzi, nessun costo per chiamata, nessuna dipendenza da fornitori esterni.
