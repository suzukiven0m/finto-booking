Schede:
- 
1. Occupazione
2. Ricavi e prezzi (economico) 
3. Ospiti
4. Reputazione
5. Previsione

## Pagina iniziale personalizzabile

Mostra solo i blocchi scelti dall'utente: ogni blocco è una card o un grafico preso dalle altre schede. All'accesso si sceglie un profilo preimpostato, poi si aggiungono o tolgono blocchi.

| Blocco | Visualizzazione | Preso dalla scheda |
| --- | --- | --- |
| Occupazione di oggi e dei prossimi 7 giorni | numero + mini linea | Occupazione |
| Arrivi e partenze di oggi e domani | due numeri affiancati | Occupazione |
| Ricavo del mese rispetto allo stesso mese dell'anno prima | numero con variazione | Ricavi e prezzi |
| Prezzo medio per camera venduta | numero con variazione | Ricavi e prezzi |
| Quota di prenotazioni dirette | numero % | Canali di vendita |
| Voto medio degli ultimi 30 giorni | numero con variazione | Reputazione |
| Ultimi 5 reclami | elenco | Richieste e reclami |
| Previsione dell'occupazione a 30 giorni | linea con previsione tratteggiata | Previsione |
| Camere vendibili in più senza rischio (overbooking) | numero per struttura | Previsione |

| Profilo | Blocchi preimpostati |
| --- | --- |
| Direzione | occupazione, ricavo del mese, voto medio, previsione a 30 giorni |
| Reception | arrivi e partenze, ultimi reclami, camere fuori servizio |
| Marketing | mercati di provenienza, quota diretta, voto medio, ultime recensioni negative |
| Gestione prezzi | prezzo medio, ricavo per camera disponibile, previsione, indicazione sul prezzo |

Nel prototipo la scelta si salva nel browser, senza accesso con utente e password.

## 1. Occupazione

Filtri aggiuntivi: stagione, tipologia di camera. Il blocco "Prenotazioni e cancellazioni" riunisce i dati sul comportamento di prenotazione.

| Dato | Visualizzazione | Dettaglio | Rif. |
| --- | --- | --- | --- |
| Tasso di occupazione | numero con variazione | camere occupate / camere disponibili, esclusi i giorni di chiusura | 1.1 |
| Notti-camera vendute | numero | somma delle camere occupate | 1.7 |
| Ospiti per camera | numero | ospiti presenti / camere occupate | 1.8 |
| Camere fuori servizio | numero % | giorni-camera fuori servizio sul totale | 1.10 |
| Andamento dell'occupazione | linea, una per struttura o per area | giorno o settimana; i giorni evento evidenziati come bande | 1.2, 1.11 |
| Occupazione per struttura | barre orizzontali ordinate | dalla più alta alla più bassa | 1.3 |
| Calendario di occupazione | heatmap (strutture × mesi) | colore più scuro = più pieno | 1.4 |
| Occupazione per stagione | barre raggruppate lago e montagna | stagioni delle anagrafiche | 1.5 |
| Occupazione per giorno della settimana | barre verticali | lunedì–domenica | 1.6 |
| Occupazione per tipologia di camera | barre orizzontali | notti vendute / (unità × giorni di apertura) | 1.12 |
| Effetto degli eventi | barre di confronto | occupazione nei giorni evento contro la media della stagione | 1.11 |
| Arrivi e partenze dei prossimi 14 giorni | linea doppia | vista operativa per la reception | 1.9 |
| Periodi di apertura | timeline | barre orizzontali sui mesi, per struttura | 1.13 |

### Prenotazioni e cancellazioni

| Dato | Visualizzazione | Dettaglio | Rif. |
| --- | --- | --- | --- |
| Tasso di cancellazione | numero + linea mensile | includere le prenotazioni "annullata" | 4.4 |
| Tasso di no-show | numero | no-show / confermate | 4.6 |
| Ricavo perso | numero in euro | importi cancellati e no-show | 4.7 |
| Anticipo di prenotazione | numero (mediana) + istogramma | giorni tra prenotazione e arrivo; box plot per area e stagione | 4.1 |
| Durata media del soggiorno | numero + istogramma | notti per prenotazione | 4.2 |
| Giorno di arrivo | barre verticali | arrivi per giorno della settimana | 4.11 |
| Anticipo di cancellazione | istogramma | giorni tra cancellazione e arrivo | 4.5 |
| Prenotazioni ricevute nel tempo | linea settimanale | per data di prenotazione | 4.3 |
| Già prenotato per i mesi futuri | barre raggruppate per mese | quest'anno contro lo stesso momento dell'anno scorso | 4.8 |

## 2. Ricavi e prezzi

Filtri aggiuntivi: stagione, canale, tipologia di camera, trattamento.

| Dato | Visualizzazione | Dettaglio | Rif. |
| --- | --- | --- | --- |
| Ricavo camere | numero con variazione | somma del ricavo giornaliero | 2.1 |
| Prezzo medio per camera venduta | numero con variazione | ricavo camere / camere occupate | 2.2 |
| Ricavo per camera disponibile | numero con variazione | prezzo medio × occupazione | 2.3 |
| Valore medio di una prenotazione | numero | solo prenotazioni confermate | 2.4 |
| Ricavo mensile per struttura | barre impilate | un colore per struttura | 2.1 |
| Prezzo medio mensile | linea, una per struttura | confronto con l'anno precedente | 2.2 |
| Prezzo a notte per tipologia | box plot | filtrabile per stagione | 2.5 |
| Scostamento tra venduto e listino | scatterplot (listino sull'asse x, venduto sull'asse y) con la diagonale + barre dello scostamento medio per canale | mostra quanto si vende sotto il listino | 2.6 |
| Listino per stagione | linea a gradini, una per struttura | tariffa a notte nel tempo | 2.7 |
| Uso delle promozioni | numero % + barre per codice | EARLY60, LASTMIN, SKI3, NONRIMB: prenotazioni, sconto medio, ricavo | 2.8 |
| Mix di trattamento | barre impilate al 100% per struttura | solo pernottamento, colazione, mezza pensione, pensione completa | 2.9 |
| Ricavo per tipologia di camera | barre orizzontali | somma degli importi | 2.10 |
| Prezzo medio nei giorni evento | barre affiancate per evento | giorni evento contro giorni normali | 2.11 |
| Relazione tra prezzo e occupazione | scatterplot colorato per stagione | un punto per giorno: occupazione sull'asse x, prezzo medio sull'asse y | 2.12 |
| Distribuzione degli importi | istogramma | importo delle prenotazioni | 2.4 |

## 3. Canali di vendita

Filtri aggiuntivi: canale (raggruppabile per tipo: diretto, portali, intermediari, aziende), mercato. Le commissioni vengono dalla tabella Canali delle anagrafiche.

| Dato | Visualizzazione | Dettaglio | Rif. |
| --- | --- | --- | --- |
| Quota di prenotazioni dirette | numero % + linea mensile | sito, telefono/email, convenzione aziendale | 3.2 |
| Commissioni pagate | numero in euro | importo × commissione del canale, prenotazioni confermate | 3.3 |
| Ricavo netto | numero in euro | importo meno commissioni | 3.4 |
| Quota per canale | barre orizzontali + barre impilate al 100% per struttura | % prenotazioni e % ricavo | 3.1 |
| Ricavo lordo e netto per canale | barre affiancate | mostra quanto costa ogni canale | 3.4 |
| Prezzo medio netto per canale | barre orizzontali | ricavo netto / notti | 3.5 |
| Cancellazioni per canale | barre orizzontali | % di prenotazioni cancellate | 3.6 |
| Paese × canale | heatmap | prenotazioni per paese e canale | 3.7 |

## 4. Ospiti

Filtri aggiuntivi: mercato (paese di provenienza).

| Dato | Visualizzazione | Dettaglio | Rif. |
| --- | --- | --- | --- |
| Quota di ospiti stranieri | numero % + linea mensile | prenotazioni con paese diverso da Italia | 5.2 |
| Ospiti medi per prenotazione | numero | adulti più bambini | 5.5 |
| Clienti di ritorno | numero % | codici cliente con più di una prenotazione; sarà basso perché quasi tutti i codici sono unici | 5.6 |
| Mercati di provenienza | barre orizzontali, primi 10 paesi | % prenotazioni e ricavo; mappa come extra | 5.1 |
| Paese × mese | heatmap | prenotazioni per paese e mese di arrivo | 5.3 |
| Composizione del gruppo | barre orizzontali | coppie, famiglie con bambini, singoli, gruppi | 5.4 |
| Richieste speciali | barre orizzontali | animali, culla, allergie, auto elettrica, late check-out | 5.7 |

## 5. Reputazione

Filtri aggiuntivi: piattaforma (StayHub, TravelNest, sito), lingua, tipo di viaggio, mercato. Il voto è sempre normalizzato su 0–10, perché le recensioni arrivano con due scale diverse. Con 270 recensioni mostrare sempre anche il numero.

| Dato | Visualizzazione | Dettaglio | Rif. |
| --- | --- | --- | --- |
| Voto medio | numero con variazione | media del voto su 0–10 | 6.1 |
| Recensioni negative | numero % | dal sentiment di Federico | 6.8 |
| Numero di recensioni | numero | nel periodo selezionato | 6.7 |
| Tasso di risposta della direzione | numero % | oggi 25 recensioni su 270 | 6.11 |
| Voto per struttura | barre orizzontali ordinate | con il numero di recensioni accanto | 6.2 |
| Andamento del voto | linea | media mobile a 3 mesi, perché ci sono poche recensioni al mese | 6.3 |
| Distribuzione dei voti | istogramma | recensioni per fascia di voto | 6.4 |
| Voto per piattaforma | barre | StayHub, TravelNest, sito | 6.5 |
| Voto per tipo di viaggio e per lingua | barre raggruppate | coppia, famiglia, amici, solo, lavoro; it, en, de | 6.6 |
| Sentiment per struttura | barre impilate al 100% | positive, neutre, negative | 6.8 |
| Recensioni per mese | barre mensili | per struttura | 6.7 |
| Reputazione e prezzo | scatterplot | un punto per struttura: voto medio sull'asse x, prezzo medio sull'asse y | 6.12 |
| Ultime recensioni negative | tabella filtrabile | data, struttura, voto, topic, testo | 6.13 |

## 6. Richieste e reclami ospiti

Filtri aggiuntivi: canale di comunicazione, lingua. Sono solo 61 testi (36 email e 25 messaggi): mostrare numeri assoluti e non percentuali.

| Dato | Visualizzazione | Dettaglio | Rif. |
| --- | --- | --- | --- |
| Comunicazioni ricevute | numero | email e messaggi nel periodo | 7.1 |
| Reclami e ringraziamenti | due numeri affiancati | dalla classificazione di Federico | 7.6 |
| Richieste commerciali di gruppo | numero | gruppi, matrimoni, aziende, scuole | 7.7 |
| Comunicazioni per mese | barre impilate | richieste e reclami | 7.1 |
| Comunicazioni per canale | barre orizzontali | WhatsApp, portale, modulo del sito, email | 7.2 |
| Comunicazioni per struttura | barre raggruppate | richieste e reclami separati | 7.3 |
| Tipo di richiesta | barre orizzontali | disponibilità e preventivi, gruppi ed eventi, animali, accessibilità, fatture, cancellazioni, convenzioni | 7.4 |
| Motivi di reclamo | barre orizzontali, colore per struttura | attese al check-in, riscaldamento e acqua calda, pulizia, rumore, camera diversa da quella prenotata, parcheggio, Wi-Fi | 7.5 |
| Lingua delle comunicazioni | barre | italiano, inglese, tedesco | 7.8 |
| Reclami recenti | tabella filtrabile | data, canale, struttura, motivo, testo | 7.9 |
| Richieste di gruppo | tabella | data, struttura, numero di persone | 7.7 |

## 7. Punti forti e deboli

Sintesi per struttura di cosa funziona e cosa no, ricavata da recensioni e comunicazioni. Dipende dai topic e dal sentiment di Federico. Filtri aggiuntivi: piattaforma, lingua, tipo di viaggio.

| Dato | Visualizzazione | Dettaglio | Rif. |
| --- | --- | --- | --- |
| Punto forte e punto debole di ogni struttura | sei card, una per struttura | topic con il voto medio più alto e topic con il più basso, con numero di menzioni | nuovo |
| Profilo della struttura | grafico radar | voto medio per topic (pulizia, personale, colazione, posizione, prezzo, Wi-Fi…) con la media del gruppo come linea di confronto | nuovo |
| Struttura × topic | heatmap a semaforo (verde, giallo, rosso) | voto medio nella cella, numero di menzioni al passaggio del mouse | nuovo |
| Matrice dei fattori di soddisfazione | scatterplot a 4 quadranti | % di recensioni che citano il topic sull'asse x, voto medio sull'asse y; in basso a destra i problemi da risolvere per primi | 6.10 |
| Topic positivi e negativi | barre divergenti orizzontali | negativi a sinistra, positivi a destra | 6.9 |
| Peso dei fattori sul voto finale | barre divergenti orizzontali + albero decisionale come immagine | punti di voto guadagnati o persi quando il fattore è citato (è più importante il bagno o il materasso?); indicativo | idea Fabio |
| Evoluzione di un topic | linea | voto medio del topic scelto nel tempo, con un filtro per topic | nuovo |
| Motivi di reclamo per struttura | tabella con i primi 3 motivi | dalle comunicazioni; per esempio attese al check-in, riscaldamento e acqua calda, rumore, Wi-Fi | 7.5 |



## 8. Previsioni:
-

| Previsione | Tipo | Scopo | Modelli | Variabili |
| --- | --- | --- | --- | --- |
| Domanda | Occupazione | Quante camere occupate in futuro? | Regressione poi Random Forest o Gradient Boosting | Mese, giorno, stagione, evento, festività, occupazione precedente, prenotato in anticipo |
| Cancellazioni | Occupazione | Probabilità di cancellazione per ogni prenotazione | Regressione Logistica \(probabilità\) | Quelle note in prenotazione: canale, codice promo, anticipo, notti, stagione, struttura, tipologia trattamento, paese, importo |
| Ricavi | Economico | Moltiplica la previsione di occupazione con la tariffa stagionale decisa da noi, confronto con previsione sugli introiti generali \(troppi pochi dati temporai per stagionalità\) | attinge a previsione occupazione, confronto con serie temporale | Previsione occupazione, tariffe |
| Elasticità prezzo | Economico | Quanto cala l’occupazione al salire dell’ADR, per struttura e stagione\. Quando conviene alzre/abbassare il prezzo? |  |  |
| Prenotazioni in arrivo | Occupazione | Quante prenotazioni ci aspettiamo ancora nei prossimi 30 giorni per il 31 esimo giorno? \(non sono sicuro di volerlo usare\) |  |  |
| Overbooking sicuro | Occupazione | Quanto si può andare in overbooking in modo sicuro |  |  |
| Fattori del voto | Reputazione | Definire l’importanza dei vari fattori delle recensioni sulla recensione finale\. È più importante il bagno o il materasso? |  |  |
| Picchi di arrivo e partenze | Occupazione | Per orario\. Per gestire meglio le risorse della reception |  |  |
| Domanda per mercato | Economico? | Da dove arrivano i clienti? Per decidere dove investire in Marketing\. |  |  |









Filtri globali:
-

| Filtro | Valori | Sezione | Tipologia |
| --- | --- | --- | --- |
| Periodo | intervallo date \+ preset mese / stagione / anno; confronto con anno precedente | tutte | date range picker \+ toggle vs anno prec\. |
| Area | lago, montagna | tutte | pulsanti |
| Struttura | 6 strutture \(S01–S06\) | Tutte | menu a selezione multipla |
| Stagione | chiusura, bassa, media, alta, altissima \(da ANA Stagionalità\) | Occupazione, Prezzi, Previsione | menu |
| Canale | 7 canali, raggruppabili per tipo: Diretto, OTA, Intermediario, B2B | Prezzi, Previsione \(Domanda\) | menu a selezione multipla |
| Tipologia camera | Standard, Superior, Suite, Family, Monolocale… | Occupazione, Prezzi, Previsione | menu |
| Trattamento | RO, BB, HB, FB | Prezzi, Previsione | menu |
| Mercato | paese dell'ospite | Domanda, Ospiti, Reputazione | menu |
| Data di riferimento | data soggiorno o data prenotazione | Domanda | toggle |
| Piattaforma, lingua, tipo viaggio | StayHub, TravelNest, sito; it/en/de; coppia, famiglia, amici, solo, lavoro | solo Reputazione | menu |