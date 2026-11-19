# Client communications — registro e bozze

Mitiga P1-1 (status review 2026-11-16): le obbligazioni O1–O5 e la richiesta dati
B4 non avevano evidenza nel repo. Questo file raccoglie copie/link e bozze. Ciò che
è solo bozza va **inviato e archiviato** dal team lead; non si dichiara fatto ciò
che non è documentato.

## Obbligazioni — stato dell'evidenza

| ID | Obbligo | Scadenza | Evidenza nel repo |
|---|---|---|---|
| B4 | Richiesta dati al cliente, per iscritto | Nov 10 | 🔴 da archiviare (copia qui o link drive) |
| O1 | NDA / GDPR / pseudonymizzazione | SAL 1 | 🔴 da archiviare. Nel repo: dati fittizi e email sintetiche (dizionario §1, §4) |
| O2 | Chiavi LLM e chi paga | Nov 16 | 🔴 decisione da registrare (blocca D15 e i secret di deploy) |
| O3 | Ownership del codice | SAL 1 | 🔴 da archiviare |
| O4 | Conferma 4ª sessione cliente | Nov 13 | 🔴 da archiviare |
| O5 | Stato scritto settimanale (ven) | Nov 13 / Nov 20 | 🟡 bozza 2026-11-19 sotto; lo stato del 13 nov non ha evidenza (gap riconosciuto); copia inviata da archiviare |

## O5 — stato settimanale (bozza 2026-11-19, per SAL 1 ven 2026-11-20)

> **Gap riconosciuto:** lo stato del 13 nov non è stato inviato/archiviato: gap
> riconosciuto. Questo aggiornamento del 19 nov recupera il ritardo; invio e
> archiviazione della copia restano azioni umane (ledger HA-02).
>
> Aggiornamento dati e applicazione. Il dataset è riproducibile end-to-end e il
> baseline è verificato al centesimo — 61.777 prenotazioni valide, 218.410
> room-night, **22.976.960,13 €** di ricavo realizzato, ADR 105,20 €. Le
> recensioni vengono dal corpus TripAdvisor reale (ADR 0003, opzione E): due
> strutture mappate, **1.638 recensioni** (762 + 876), corpus **solo inglese**,
> voti reali nelle cinque dimensioni. Le email guest-request sono sintetiche
> (800, italiano, 6 categorie) e dichiarate come tali.
>
> Va dichiarato esplicitamente: le due strutture "Buby Lago/Montagna" sono
> fittizie (mappatura 1:1 dei due hotel del CSV); il legame recensioni↔prenotazioni
> è **asserito a livello di proprietà**, non fattuale; la capacità delle strutture
> (190/230 camere) è **assunta**, quindi occupazione e RevPAR non sono misure.
> **S4 — nessun overlap temporale:** le recensioni sono tutte del 2012
> (2012-01-02…2012-12-19), le prenotazioni coprono 2015-07…2017-09: zero mesi in
> comune, quindi solo comparazione a livello di proprietà, nessun join mensile
> possibile. Nessun dato reale del cliente entra nel repository.
>
> Stato tecnico al 19 nov: contratto API con le contraddizioni S1/S2/S3 corrette
> (WP1, PR #11), pronto per il freeze di domani; schema a 0005 con le decisioni
> pre-freeze su auth e output NLP (WP2, PR #12); API mergiata (PR #9): 4 operazioni
> su 11 del contratto (properties, kpis/summary, kpis/daily, auth/login — token
> finto fino a D11); login UI mergiata (PR #10); dashboard ancora sul mock Prism
> fino allo swap D17. Restano da implementare le altre 7 operazioni, NLP
> (D14/D15) e il forecast (stretch).
>
> Entro SAL 1 (domani): freeze di contratto + schema con sign-off, dizionario
> dati v1, disclosure complete (sostituzioni dati, capacità assunta, S4).

*Bozza base: il testo finale send-ready sarà finalizzato in WP5 (`docs/sal1/`).
Da inviare venerdì e archiviare qui la copia inviata (O5). Nulla è ancora inviato.*

## Notifica al team (bozza — playbook §8.1)

> I deliverable DA-1/DA-2/DA-3 risultano non presidiati alla data del 2026-11-16.
> Eseguo B6/D3/D4/D8/D9 (+ metà dati di D7) secondo `docs/playbooks/solo-dataset.md`
> sul branch `data-solo`. Obiezioni o rivendicazioni entro il SAL 1 (2026-11-20).
> Le decisioni prese in solo sono registrate nel dizionario dati.

*Da inviare sul canale del team + email; il silenzio dopo la scadenza è consenso
documentato. Riassegnazione formale al prossimo sync (playbook §8.5).*
