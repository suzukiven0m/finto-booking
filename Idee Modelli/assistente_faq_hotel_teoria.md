# Assistente virtuale per le domande frequenti dell'hotel

*Descrizione teorica del progetto*

---

## 1. Obiettivo

Gran parte delle domande che gli ospiti rivolgono alla reception si ripete:
- *"A che ora è la colazione?"*
- *"C'è il parcheggio?"*
- *"Posso portare il cane?"*
- *"Fino a che ora posso fare il check-out?"*

Le risposte esistono già: si trovano nel regolamento, nel listino dei servizi, negli orari e nelle informazioni pratiche dell'hotel.

Il progetto prevede un **assistente virtuale** che risponde in modo autonomo a queste domande, a qualsiasi ora e in più lingue. Le informazioni non sono scritte "dentro" l'assistente: le recupera dai **documenti caricati direttamente dal proprietario**. Se un orario o un prezzo cambia, basta aggiornare il documento e l'assistente si adegua subito.

## 2. Vincoli del progetto

- **Solo modelli open-source di Hugging Face**, senza servizi o API esterne.
- **Esecuzione in locale**, sui computer o sui server dell'hotel: documenti e conversazioni non vengono inviati a terzi.
- **Risposte affidabili:** l'assistente non deve mai inventare orari, prezzi o servizi.
- **Gestione semplice:** il proprietario deve poter aggiornare le informazioni senza competenze tecniche.

## 3. L'approccio scelto: RAG

### 3.1 Cos'è il RAG

**RAG** sta per *Retrieval-Augmented Generation*, cioè "generazione arricchita dal recupero di informazioni". Il funzionamento si divide in due momenti:

1. **Recupero (retrieval):** data la domanda, il sistema cerca nei documenti dell'hotel i passaggi che contengono la risposta.
2. **Generazione:** un modello linguistico (LLM) legge quei passaggi e formula una risposta in linguaggio naturale, basandosi **solo** su di essi.

È come un impiegato che, prima di rispondere, apre il fascicolo giusto e legge la pagina pertinente, invece di rispondere a memoria.

### 3.2 Perché RAG e non addestrare il modello

| Addestrare un modello sulle informazioni dell'hotel | RAG |
|---|---|
| Ogni modifica (nuovo orario, nuovo prezzo) richiede un nuovo addestramento | Basta sostituire il documento |
| Il modello può "ricordare male" e mescolare informazioni | La risposta si basa su testi recuperati al momento |
| Non si sa da dove venga una risposta | Ogni risposta indica il documento di origine |
| Richiede competenze tecniche e hardware dedicato per ogni aggiornamento | Il proprietario gestisce tutto caricando file |

## 4. I componenti del sistema

Il sistema combina quattro componenti, ciascuno con un ruolo preciso:

| Componente | Modello / tecnologia | Ruolo |
|---|---|---|
| **Modello di embedding** | BGE-M3 | trasforma ogni testo in un vettore numerico che ne rappresenta il *significato* |
| **Indice vettoriale** | FAISS | archivia i vettori e trova velocemente quelli più simili alla domanda |
| **Reranker** | BGE-Reranker-v2-M3 | rilegge domanda e passaggi insieme e assegna un punteggio di pertinenza più preciso |
| **Modello linguistico (LLM)** | Qwen 2.5 Instruct (7 o 3 miliardi di parametri) | scrive la risposta finale in linguaggio naturale |

**Gli embedding.** Due frasi con lo stesso significato hanno vettori vicini anche se usano parole diverse. Per esempio *"a che ora si mangia la mattina?"* e *"orario della colazione"* risultano simili. Il modello scelto è **multilingue**, quindi una domanda in inglese trova anche un documento scritto in italiano.

**Il reranker.** La ricerca per vettori è veloce ma approssimativa. Il reranker è più lento ma più preciso, perché valuta domanda e passaggio insieme. Si usa solo sui pochi candidati trovati dalla ricerca: si ottiene così la precisione del reranker senza perdere velocità.

**L'LLM.** Si è scelto un modello open-source di dimensione contenuta, che funziona bene in italiano e rispetta istruzioni come *"rispondi solo con queste informazioni"*. La versione più piccola consente l'uso anche con hardware modesto.

## 5. Come funziona

### 5.1 Caricamento dei documenti (lato proprietario)

1. Il proprietario carica un documento (PDF, Word o testo) dall'area riservata dell'applicazione.
2. Il sistema **estrae il testo**, comprese le tabelle, importanti per listini prezzi e orari.
3. Il testo viene **diviso in pezzi** di circa 250 parole. Pezzi consecutivi condividono una piccola parte di testo, così un'informazione a cavallo tra due pezzi non va persa.
4. Ogni pezzo viene trasformato in un **vettore** e inserito nell'**indice**, insieme al nome del documento da cui proviene.
5. L'indice viene salvato. Al riavvio, il sistema controlla se i documenti sono cambiati e, solo in quel caso, lo ricostruisce.

### 5.2 Risposta a una domanda (lato ospite)

1. L'ospite scrive una domanda.
2. La domanda viene trasformata in vettore e l'indice restituisce gli **8 pezzi più simili**.
3. Il **reranker** li riordina per pertinenza e tiene i **3 migliori**.
4. **Controllo di pertinenza:** se nemmeno il pezzo migliore supera una soglia minima, il sistema conclude che l'informazione non è nei documenti. Risponde quindi con un messaggio cortese che invita a contattare la reception, **senza interpellare l'LLM**.
5. Altrimenti l'LLM riceve la domanda, i pezzi selezionati e le istruzioni di comportamento, e formula la risposta.
6. All'ospite arrivano la **risposta** e i **documenti** da cui è stata ricavata.

## 6. Come si evita che l'assistente inventi

I modelli linguistici a volte producono risposte plausibili ma false (le cosiddette *allucinazioni*). Per un hotel un orario o un prezzo sbagliato è un problema concreto. Il sistema usa quattro difese:

1. **Soglia di pertinenza:** se i documenti non contengono informazioni adatte, l'LLM non viene nemmeno usato.
2. **Istruzioni vincolanti:** all'LLM viene chiesto esplicitamente di usare *solo* le informazioni fornite, di riportare orari e prezzi esattamente come scritti e di ammettere quando non sa.
3. **Generazione deterministica:** il modello sceglie sempre la formulazione più probabile, senza variazioni casuali. A parità di domanda e documenti dà la stessa risposta.
4. **Citazione delle fonti:** ogni risposta indica da quale documento proviene, quindi è verificabile.

## 7. Memoria della conversazione

### 7.1 Il problema

Senza memoria ogni domanda è isolata. Se l'ospite chiede *"C'è il parcheggio?"* e poi *"Bisogna prenotarlo?"*, la seconda domanda da sola non dice di cosa si parla, e la ricerca nei documenti fallisce.

### 7.2 La soluzione

- **Sessioni:** ogni conversazione ha un identificativo univoco, che l'applicazione conserva e invia a ogni nuova domanda della stessa chat.
- **Archivio delle conversazioni:** domande e risposte vengono salvate in un piccolo database locale.
- **Riformulazione della domanda:** è il passaggio chiave. Prima della ricerca, l'LLM riscrive la domanda in forma autonoma usando la conversazione precedente. *"Bisogna prenotarlo?"* diventa *"Bisogna prenotare il parcheggio?"* e la ricerca torna a funzionare. Se la domanda è già autonoma, resta invariata. In questo modo si gestiscono anche i cambi di argomento.
- **Contesto per la risposta:** all'LLM vengono passati anche gli ultimi scambi, così la risposta è coerente con la conversazione.

### 7.3 Regole di gestione

- Si usano solo gli **ultimi 3 scambi**: uno storico più lungo rallenterebbe il sistema e confonderebbe il modello.
- Dopo **2 ore di inattività** la conversazione riparte da zero.
- Dopo **30 giorni** le conversazioni vengono cancellate automaticamente.
- L'ospite può **cancellare** la propria conversazione in qualsiasi momento.

## 8. Strumenti per il proprietario

Il proprietario dispone di un'area riservata, protetta da una chiave di accesso, da cui può:
- **caricare, consultare ed eliminare** i documenti informativi;
- **leggere le conversazioni**, per capire come gli ospiti usano l'assistente;
- consultare l'elenco delle **domande rimaste senza risposta**.

Quest'ultimo elenco è uno degli strumenti più utili. Se molti ospiti chiedono *"c'è una palestra?"* e l'assistente non sa rispondere, il proprietario capisce quale informazione manca nei documenti e la aggiunge. Il sistema migliora così **senza alcun intervento tecnico**.

La protezione con chiave è essenziale: senza, chiunque potrebbe caricare documenti falsi e far dare all'assistente informazioni sbagliate.

## 9. Integrazione nell'applicazione

L'assistente è esposto come **servizio web interno** (API), utilizzabile da:
- una **chat sul sito** dell'hotel;
- un'**app** per gli ospiti;
- un **totem** o tablet nella hall;
- in futuro, canali di messaggistica.

Il servizio può essere unito a quello di **analisi del sentiment delle recensioni** (vedi il documento dedicato), per formare un'unica piattaforma di intelligenza artificiale dell'hotel.

## 10. Requisiti hardware

| Configurazione | Qualità delle risposte | Hardware |
|---|---|---|
| LLM da 7 miliardi di parametri | alta | scheda grafica (GPU) con circa 16 GB di memoria, o circa 6 GB con compressione a 4 bit |
| LLM da 3 miliardi di parametri | buona | GPU con circa 8 GB, o circa 3 GB compresso. Su processore normale funziona, ma lentamente |

La **compressione a 4 bit** (quantizzazione) riduce di circa tre volte la memoria necessaria, con una piccola perdita di qualità. I componenti di ricerca (embedding e reranker) sono leggeri e funzionano anche senza GPU.

## 11. Valutazione e messa a punto

Prima della messa in servizio si prepara un insieme di **20–30 domande di prova** che copre i casi principali:

| Caso | Comportamento atteso |
|---|---|
| L'informazione è nei documenti | risposta corretta con indicazione della fonte |
| Stessa domanda formulata in modo diverso | stessa risposta |
| Informazione non presente | ammissione di non sapere e invito alla reception |
| Domanda in un'altra lingua | risposta nella lingua dell'ospite |
| Domanda su prezzi o orari | valori identici a quelli dei documenti |
| Domanda fuori tema | nessuna risposta inventata |
| Domanda di seguito (*"e quanto costa?"*) | risposta coerente con la conversazione |

Quando una risposta è sbagliata, si capisce dove intervenire:
- **la ricerca non trova il passaggio giusto:** si regolano la dimensione dei pezzi o la soglia di pertinenza;
- **il passaggio è giusto ma la risposta no:** si passa al modello più grande o si rende più chiaro il documento.

**Consigli per i documenti:**
- documenti **brevi e divisi per argomento** funzionano meglio di un unico documento lungo;
- quando un'informazione cambia, il documento vecchio va **sostituito**, non affiancato;
- i PDF ottenuti da **scansione** contengono immagini e non testo, quindi vanno prima convertiti con un OCR.

## 12. Privacy

Le conversazioni possono contenere dati personali: nomi, numeri di camera, date di soggiorno. Il progetto prevede:
- **elaborazione interamente in locale**, senza invio di dati a terzi;
- **informativa** agli ospiti sul salvataggio delle conversazioni;
- **conservazione limitata** (30 giorni) con cancellazione automatica;
- **cancellazione su richiesta** da parte dell'ospite;
- **protezione dell'archivio** e accesso riservato al proprietario;
- verifica con il responsabile privacy dell'hotel prima della messa in produzione.

## 13. Limiti e possibili sviluppi

**Limiti attuali:**
- senza GPU i tempi di risposta possono arrivare a decine di secondi;
- a ogni caricamento l'indice viene ricostruito da zero: è adeguato per le decine di documenti di un hotel, ma non per archivi molto grandi;
- con il modello più piccolo la riformulazione delle domande di seguito è meno affidabile;
- il sistema risponde solo con informazioni scritte, quindi non può accedere a dati in tempo reale come la disponibilità delle camere.

**Possibili sviluppi:**
- collegamento al **gestionale dell'hotel** per disponibilità e prenotazioni;
- un **server di inferenza dedicato** per gestire molte conversazioni contemporanee;
- **aggiornamento incrementale** dell'indice;
- **passaggio a un operatore umano** quando l'assistente non sa rispondere;
- **statistiche** sugli argomenti più richiesti, da affiancare all'analisi delle recensioni.

## 14. Valore per l'hotel

- **Disponibilità continua:** risposte immediate 24 ore su 24, anche di notte e nei momenti di punta.
- **Meno carico per la reception**, che può dedicarsi alle richieste che richiedono una persona.
- **Multilingua senza costi aggiuntivi.**
- **Informazioni sempre aggiornate**, gestite direttamente dal proprietario.
- **Miglioramento guidato dai dati:** le domande senza risposta mostrano quali informazioni mancano.
- **Privacy e indipendenza:** nessun dato inviato a terzi, nessun costo per singola risposta.
