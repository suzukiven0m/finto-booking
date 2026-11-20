# Processo: SAL, ADR e registro delle azioni umane

## Cos'è

Questo elemento non è un pezzo di software: è l'insieme delle decisioni
scritte e delle regole di lavoro che tengono insieme il progetto. Comprende
i SAL (Stato Avanzamento Lavori) con il cliente, gli ADR (Architecture Decision
Record, le decisioni di architettura), il registro delle azioni umane e la
traccia di audit e review. Nel diagramma è il livello viola: avvolge tutto,
perché senza processo i due team non collaborano e la valutazione non ha
evidenza.

## Perché l'abbiamo disegnato così

Il brief valuta esplicitamente la "collaborazione tra i team" e il "rispetto
delle scadenze". Un progetto fatto da una persona sola che scrive tutto, senza
traccia di accordo con gli altri, non dimostra collaborazione. Il processo è
l'architettura organizzativa che rende la collaborazione visibile e verificabile.

I pezzi:

- **SAL 1 con freeze** (20 novembre 2026, cliente presente): schema e contratto
  si congelano a `v1.0.0` con un tag. Il freeze non è un dettaglio tecnico: è
  il momento in cui i due team si accordano davanti al cliente, e da lì ogni
  modifica costa una procedura (contract-bump). Le slide, il catalogo KPI da
  firmare e lo stato settimanale sono in `docs/sal1/`.
- **ADR**: ogni decisione importante è un documento con contesto, alternative,
  scelta e conseguenze. 0001 stack, 0002 persistenza, 0003 sorgenti dati
  (opzione E), 0004 deploy (proposto, non accettato: gli account sono umani).
  Tenere le alternative scartate è ciò che rende una decisione difendibile:
  se il cliente chiede "perché non X?", la risposta è già lì.
- **Registro azioni umane** (`docs/reviews/human-actions.md`): le cose che
  solo le persone possono fare (firmare, inviare email, pagare, presentare,
  creare account). Gli agent preparano gli artefatti, ma non chiudono mai una
  riga umana. Ogni riga ha owner, scadenza, conseguenza se saltata. È il
  confine onesto tra automazione e responsabilità.
- **Traccia di audit e review**: l'audit shepherd ha fotografato lo stato
  (finding S1-S10, R1-R18), e ogni work package ha un record nel formato
  builder → reviewer indipendente → fix → merge. Nessuno reviewa il proprio
  output; l'evidenza è eseguita, non citata; gli skip sono dichiarati come
  skip. Le deviazioni sono registrate (merge admin con sign-off per il limite
  del singolo account, incidenti di quota provider, modalità sequenziale
  dopo crash OOM).

Abbiamo "scartato" l'alternativa di non scrivere il processo: sarebbe stato
più veloce nell'immediato, ma il voto di collaborazione non avrebbe evidenza,
e i tagli silenziosi di requisiti nominati nel brief sarebbero emersi in sede
di valutazione. Il processo scritto è più lento ma difendibile.

## Com'è fatto in pratica

- `docs/sal1/`: slides-outline, kpi-signoff (firme vuote, le riempiono le
  persone), o5-status (stato settimanale pronto), freeze-checklist.
- `docs/adr/0001-0004`: le decisioni.
- `docs/client-comms.md`: registro delle obbligazioni cliente (O1-O5, B4).
- `docs/reviews/human-actions.md`: il ledger delle azioni umane (HA-01…HA-15).
- `docs/reviews/`: audit, record per-package, stato della remediation.
- `docs/playbooks/solo-dataset.md`: il playbook del lavoro svolto in solo
  (tre owner DA silenti, un WSA ha portato i workstream; notifica e
  riassegnazione formale sono azioni umane pendenti, HA-03/HA-04).

## Limiti e cosa può andare storto

- Il processo scritto non sostituisce le azioni: le slide pronte non sono la
  presentazione, il catalogo pronto non è la firma, lo stato pronto non è
  l'invio. Finché le persone non eseguono, quelle righe restano aperte.
- La notifica del lavoro in solo è ancora una bozza: senza invio e
  riassegnazione, la collaborazione resta sulla carta. È il rischio
  strutturale più grande segnalato dall'audit.
- Un freeze non impedisce le modifiche di nascosto: le rende tracciabili.
  La disciplina è umana, rinforzata da tag, test e mirror.

## Riferimenti

- [Contratto openapi.yaml e freeze](contratto-openapi.md)
- [ADR 0001](../adr/0001-tech-stack.md), [0002](../adr/0002-data-storage.md), [0003](../adr/0003-data-sources.md), [0004](../adr/0004-deploy.md)
- [Registro azioni umane](../reviews/human-actions.md)
- [Stato della remediation](../reviews/2026-11-20-remediation-status.md)
- [Comunicazioni cliente](../client-comms.md)
