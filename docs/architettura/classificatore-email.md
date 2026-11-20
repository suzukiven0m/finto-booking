# Classificatore email D15: bozze proposte, mai inviate da sole

## Cos'è

È la componente che legge le 800 email sintetiche degli ospiti, assegna a
ciascuna una categoria (availability, cancellation, complaint, special_request,
billing, info) e un'urgenza (low, medium, high), e propone una bozza di risposta
in italiano. È uno dei due pezzi che soddisfano il requisito minimo del brief
"almeno una componente di elaborazione di testi/email" (R6). Il risultato
finisce nella inbox della dashboard, dove una persona approva.

## Perché l'abbiamo disegnato così

Tre scelte guidano il design:

1. **Fallback a template, non LLM.** Le chiavi LLM e la decisione su chi paga
   sono un'azione umana scaduta (O2, registro HA-05). Invece di bloccare il
   deliverable, abbiamo costruito un classificatore trasparente a lessico e
   pattern, derivato dai template noti del generatore. Il corpus è sintetico
   (lo abbiamo generato noi), quindi un lessico basato sui template è
   appropriato e onesto. Un upgrade LLM è previsto ma gated sulle chiavi:
   il percorso è documentato nel report, non implementato alla cieca.
2. **Niente training.** Non abbiamo etichette reali per addestrare un modello
   (le email sono inventate), e il gold file serve solo per valutare, non per
   addestrare. Un modello addestrato sul gold sarebbe una tautologia.
3. **HITL (human in the loop).** Le bozze atterrano con stato `draft`, mai
   `sent`. Nessuna email parte automaticamente: il pulsante "invia" nella
   inbox fa una PATCH esplicita, e solo da `draft`. Lo stato `sent` è
   terminale. Il principio: propone la macchina, approva una persona.

Abbiamo scartato un modello fine-tuned (niente budget di etichette, corpus
sintetico comunque), zero-shot NLI (più pesante, nessun vantaggio su template
noti) e un LLM subito (chiavi e costi umani, non disponibili).

## Com'è fatto in pratica

- `data/etl/email_nlp.py`: le regole di classificazione (categoria e urgenza)
  e i template di bozza per categoria, property-aware.
- `data/etl/classify_emails.py`: lo script. Default = sola valutazione;
  `--persist` scrive nel database `category`, `urgency`, `draft_reply` e
  `status='draft'` per tutte le 800 righe.
- La colonna `urgency` è nella migrazione 0005 (pre-freeze, decisione S8):
  il gold valuta `true_urgency`, quindi l'output predetto aveva bisogno di
  una casa nello schema.

Due guardrail importanti:

- **Anti-leakage.** La pipeline non legge MAI `data/eval/email_gold.csv`
  (le etichette vere). Solo lo script di valutazione lo legge, ed è il suo
  lavoro. Un test ispeziona il sorgente della pipeline per verificare che non
  ci siano riferimenti al gold; un altro ricalcola le predizioni per ogni id
  e verifica che il database contenga quelle, non le etichette gold. Le 8
  righe classificate male sono la prova: se il database contenesse il gold,
  quelle 8 coinciderebbero e il test lo noterebbe.
- **Sent-guard.** La UPDATE di `--persist` ha `AND status != 'sent'`: un
  rilancio non sovrascrive mai le righe che una persona ha già approvato e
  inviato. La semantica "una tantum" è ora imposta dal codice, non solo
  documentata.

Numeri (valutazione onesta, corpus sintetico): macro-F1 categoria 0.9901,
urgenza 0.9659. Gli 8 errori (4 availability→info, 4 special_request→info)
sono divulgati con cause nel report. Un F1 alto su_corpus sintetico generato
da template NON è evidenza di performance nel mondo reale: lo diciamo
esplicitamente.

In CI il passo `--persist` gira dopo il seed e prima dei test: senza, la inbox
sarebbe vuota di bozze e i test post-D15 fallirebbero (era un gap di ordinamento
che abbiamo corretto).

## Limiti e cosa può andare storto

- Il lessico è tarato sui template del generatore: su email vere, fuori da
  quei pattern, la performance crollerebbe. È un fallback dimostrativo, non
  un prodotto.
- Senza chiavi LLM (HA-05) il percorso di upgrade resta bloccato: la demo
  mostra il fallback, e lo dichiara.
- Se rilanci `gen_emails.py` (rigenera le email con TRUNCATE RESTART IDENTITY),
  devi rigenerare anche il gold nello stesso run, altrimenti gli id non
  combaciano più.

## Riferimenti

- [Analisi assistente email](../analysis/email-assistant.md)
- [Valutazione e anti-leakage](valutazione-anti-leakage.md)
- [Dizionario dati: guest_requests e urgenza](../data-dictionary.md)
- [Registro azioni umane: HA-05](../reviews/human-actions.md)
- Codice: `data/etl/email_nlp.py`, `data/etl/classify_emails.py`
