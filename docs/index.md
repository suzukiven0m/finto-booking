# Buby Travel

Benvenuto nella documentazione del nostro progetto di laboratorio per il caso 1
(Turismo) di Buby Group. Siamo un team misto di due corsi: Data Analyst / AI
Specialist (DA) e Web Solutions Architect (WSA). I DA preparano e analizzano i
dati, i WSA costruiscono database, API e interfaccia web.

L'applicazione mostra i KPI di occupazione e ricavo, una pagina reputazione
basata sulle recensioni, una ricerca sulle prenotazioni e una inbox dove
l'assistente propone bozze di risposta che una persona approva prima di inviare.

!!! warning "Cosa è vero e cosa no"
    Il cliente non ci ha mai consegnato dati suoi. Le due strutture sono
    fittizie, le prenotazioni vengono da un dataset pubblico portoghese
    (2015-2017), le recensioni sono reali ma tutte del 2012 (nessun mese in
    comune con le prenotazioni), le email sono sintetiche, la capacità delle
    strutture è assunta. Il legame recensioni-prenotazioni è asserito a livello
    di proprietà, non fattuale. Sono disclosure vincolanti: le ripetiamo nella
    dashboard, nelle slide e nel report finale.

## Da dove partire

Se sei nuovo, segui questo percorso:

1. **[Guida per iniziare](getting-started.md)**: porta da zero a un'app
   funzionante sul tuo computer, ogni passaggio spiegato.
2. **[Glossario](glossario.md)**: i termini tecnici in due righe, per pareggiare
   le competenze tra i due corsi.
3. **[Architettura](architettura/README.md)**: il diagramma e un documento per
   ogni elemento, che spiega perché è disegnato così.

## Se cerchi qualcosa di specifico

- **Dati e API**: [dizionario dati](data-dictionary.md), [ERD](erd.md),
  [contratto API](api-contract.md).
- **Analisi**: [reputazione NLP](analysis/reputation-nlp.md),
  [assistente email](analysis/email-assistant.md),
  [domanda e prezzi](analysis/demand-pricing.md),
  [report finale](analysis/final-report.md).
- **Decisioni**: [ADR](adr/0001-tech-stack.md) (stack, persistenza, sorgenti, deploy).
- **Processo**: [piani](plan.md), [SAL 1](sal1/slides-outline.md),
  [azioni umane](reviews/human-actions.md), [stato della remediation](reviews/2026-11-20-remediation-status.md).

## Come leggere questa documentazione

Ogni documento tecnico è scritto per un team misto: i termini sono spiegati
alla prima occorrenza, le scelte motivano le alternative scartate, i numeri
sono verificati e i limiti dichiarati. Il codice e il contratto restano nella
repository GitHub: questo sito è la loro porta d'ingresso leggibile.