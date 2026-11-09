# Analisi: Data Analyst nel caso Buby Travel

**In sintesi:** il team dati deve collegare i dati di prenotazione ai testi degli ospiti per spiegare la reputazione, prevedere la domanda e alimentare l'app. Il documento fissa gli obiettivi, ma non i KPI né come misurarli: conviene chiarirli con il cliente.

Il documento tratta sempre insieme **Data Analyst e AI Specialist**, quindi non separa i compiti dei due profili.

## Il problema

Buby Travel gestisce hotel e strutture ricettive sul lago e in montagna, con vendita diretta e tramite portali. Ha due criticità:

- occupazione e prezzi sono gestiti con poca analisi dei dati;
- recensioni e richieste degli ospiti non vengono analizzate in modo sistematico.

## Dati disponibili

| Tipo | Dati |
|---|---|
| **Strutturati** | Prenotazioni, occupazione, tariffe, stagionalità, canali di vendita |
| **Non strutturati** | Recensioni online, email di richiesta informazioni, messaggi e reclami degli ospiti |

## Dagli obiettivi al lavoro sui dati

La colonna "Lavoro del team dati" è una mia interpretazione: il documento indica gli obiettivi e le attività generali del corso, non questo abbinamento.

| Obiettivo del caso | Lavoro del team dati | Dati principali |
|---|---|---|
| Capire cosa influenza soddisfazione e reputazione | Classificare i temi di recensioni e reclami, misurare il sentiment e collegarli a struttura e periodo | Recensioni, reclami, prenotazioni |
| Prevedere la domanda e supportare i prezzi | Modello predittivo per struttura e periodo, analisi del rapporto tra tariffe e occupazione | Prenotazioni, tariffe, stagionalità, canali |
| Dashboard e assistente per la direzione | Preparare i KPI e i dati nel formato concordato, classificare ed estrarre informazioni dalle richieste | Tutti |

## Cosa va consegnato

- Dataset puliti e data dictionary
- Notebook o script documentati
- Endpoint o file di output nel formato concordato
- Report dei risultati

Il minimo richiesto a ogni team è una componente di analisi dei KPI e una di elaborazione di testi o email.

## Punti da chiarire

1. **Previsione:** il caso chiede di prevedere la domanda, ma tra le attività del corso il modello predittivo è solo "eventuale". Va chiarito se è obbligatorio.
2. **Assistente:** il caso lo include, ma la componente basata su LLM è anch'essa "eventuale". Inoltre, non è detto se spetti al team dati o ai WSA.
3. **KPI:** il documento non li elenca per questo caso. Io proporrei tasso di occupazione, ricavo medio per camera venduta (ADR), ricavo per camera disponibile (RevPAR), quota di prenotazioni per canale, punteggio medio delle recensioni e tasso di reclami.
4. **Qualità dei dati:** non si sa quanti dati ci sono, che periodo coprono né se recensioni e prenotazioni si possono collegare. Senza uno storico di più stagioni, la previsione è poco affidabile.
5. **Privacy:** email e messaggi degli ospiti possono contenere dati personali. Anonimizzazione e GDPR sono tra i requisiti da definire con l'azienda.
6. **Tempi:** il contratto dati va definito nella "seconda settimana", ma schema e contratto vengono congelati al SAL 1 del 20 novembre. Va chiarito quale scadenza vale per il team.

## Da dove partire

1. Chiedere subito al cliente i dati, i KPI prioritari e cosa è obbligatorio.
2. Pulire i dati e scrivere il data dictionary, così da concordare presto il contratto dati con i WSA.
3. Fare prima i KPI e l'analisi delle recensioni, che sono il minimo richiesto.
4. Passare poi alla previsione della domanda e, per ultimo, all'assistente.
