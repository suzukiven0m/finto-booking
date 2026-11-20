# Valutazione e anti-leakage: numeri onesti, per costruzione

## Cos'è

È l'insieme di script, file e regole che misurano quanto sono buoni i modelli
(NLP recensioni e classificatore email) e che impediscono alla valutazione di
barare. "Anti-leakage" significa evitare che le etichette vere (il gold)
finiscano dove il modello può vederle: se succedesse, la valutazione sarebbe
una tautologia (il modello "indovina" perché ha già la risposta).

## Perché l'abbiamo disegnato così

Il brief valuta "utilità e affidabilità delle componenti AI". Una valutazione
onesta è il cuore di quel criterio. Abbiamo separato nettamente tre ruoli:

1. **La pipeline** (classificatore, NLP) produce predizioni. Non legge MAI il
   gold file.
2. **La valutazione** legge il gold e confronta le predizioni con le etichette
   vere. È l'unico posto dove il gold entra.
3. **Il database** tiene le predizioni (per la demo), mai le etichette gold.

Per le email, le etichette vere (`true_category`, `true_urgency`) vivono SOLO
in `data/eval/email_gold.csv`. Non sono colonne del database, non sono lette
dagli script di classificazione. Un test ispeziona il sorgente della pipeline
per verificare l'assenza di riferimenti al gold; un altro ricalcola le
predizioni per ogni id e verifica che il database contenga quelle. Le 8 righe
classificate male sono la prova vivente: se il database contenesse il gold,
quelle 8 coinciderebbero e il test di riproducibilità lo noterebbe.

Per le recensioni non c'è un gold separato: usiamo **weak labels**, cioè i
voti reali degli ospiti (overall e cinque dimensioni) come riferimento. Sono
"deboli" perché non sono etichette di sentiment annotate a mano, ma voti
numerici correlati. La valutazione è onesta per costruzione: le etichette non
vengono dal modello che stiamo valutando, quindi misuriamo una correlazione
reale, non una auto-conferma. Correlazione di Spearman pooled 0.5517, Pearson
0.5894: un segnale moderato, dichiarato come tale, non spacciato per accuratezza.

Abbiamo scartato un test set tenuto da parte (il corpus è piccolo: 1.638
recensioni, 800 email; togliere una fetta ridurrebbe troppo i dati) e
l'annotazione umana pagata (budget da laboratorio). Le weak labels e la probe
di calibrazione sono il compromesso onesto disponibile.

## Com'è fatto in pratica

- `data/eval/email_gold.csv`: 800 righe, header `id,true_category,true_urgency`.
  Gli id combaciano con `guest_requests.id` perché entrambi partono da
  TRUNCATE RESTART IDENTITY nello stesso run. Se ricarichi le email, rigenera
  il gold nello stesso run, altrimenti gli id non combaciano.
- `data/eval/review_nlp_metrics.json`: correlazioni (pooled, per proprietà,
  per dimensione), coverage, modelli e revisioni, truncation, runtime,
  calibrazione delle soglie con le precisioni della probe.
- `data/eval/email_metrics.json`: macro-F1, precision/recall per classe,
  confusion matrix per categoria e urgenza.
- `data/eval/topic_probe_annotations.csv`: le 20 recensioni annotate a mano
  per calibrare le soglie dei topic (committate per riproducibilità).
- `data/eval/demand_analysis.json`: i numeri dell'analisi domanda/prezzi.

I file JSON sono committati (sono l'evidenza); i CSV delle predizioni sono
locali/gitignored (riproducibili con un comando). Ogni numero del report è
tracciabile a un JSON, e ogni JSON a una query o a un run documentato.
L'orchestratore ha ri-eseguito indipendentemente le correlazioni e il macro-F1:
match esatto con i JSON committati.

Le disclosure di onestà sono parte della valutazione, non un contorno:
corpus sintetico (F1 alto non è evidenza reale), probe ottimistica, tassi di
troncamento, associazione non causalità, nessun join recensioni-prenotazioni
per mese (S4).

## Limiti e cosa può andare storto

- Weak labels non sono ground truth: misurano correlazione con i voti, non
  accuratezza di sentiment. Un ρ di 0.55 è un segnale, non una certificazione.
- La probe di calibrazione è piccola e annotata dalla stessa persona che
  calibra: il suo F1 è ottimistico per costruzione, e lo dichiariamo.
- Se il gold e il database si disallineano (reload senza rigenerare il gold),
  i test di allineamento falliscono: è voluto, è la rete che protegge
  l'anti-leakage.

## Riferimenti

- [Classificatore email](classificatore-email.md)
- [NLP recensioni](nlp-recensioni.md)
- [Analisi reputazione](../analysis/reputation-nlp.md)
- [Analisi assistente email](../analysis/email-assistant.md)
- [Dizionario dati: anti-leakage](../data-dictionary.md)
- Codice: `data/eval/`, `data/tests/test_emails.py`, `data/tests/test_review_nlp.py`
