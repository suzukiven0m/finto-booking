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
| O5 | Stato scritto settimanale (ven) | Nov 13 / Nov 20 | 🟡 bozza sotto; copia inviata da archiviare |

## O5 — stato settimanale (bozza 2026-11-16, per SAL 1 ven 2026-11-20)

> Aggiornamento dati. Il dataset del progetto è ora riproducibile end-to-end:
> prenotazioni reali (`hotel_bookings.csv`, Kaggle) pulite e caricate, con il
> baseline verificato al centesimo — 61.777 prenotazioni valide, 218.410 room-night,
> **22.976.960,13 €** di ricavo realizzato, ADR 105,20 €. Le recensioni vengono dal
> corpus TripAdvisor reale (ADR 0003, opzione E): due strutture mappate, 1.638
> recensioni con i voti reali nelle cinque dimensioni. Le email guest-request sono
> sintetiche (800, italiano, 6 categorie) e dichiarate come tali.
>
> Va dichiarato esplicitamente: le due strutture "Buby Lago/Montagna" sono fittizie
> (mappatura 1:1 dei due hotel del CSV); il legame recensioni↔prenotazioni è
> **asserito a livello di proprietà**, non fattuale; la capacità delle strutture
> (190/230 camere) è **assunta**, quindi occupazione e RevPAR non sono misure.
> Nessun dato reale del cliente entra nel repository.
>
> Entro SAL 1: contratto API + schema congelati, dizionario dati v1, campione di
> dati reali che attraversa la ETL v0. Resta da chiudere la specifica OpenAPI (D5)
> e la shell della dashboard (D10).

*Da inviare venerdì e archiviare qui la copia inviata (O5).*

## Notifica al team (bozza — playbook §8.1)

> I deliverable DA-1/DA-2/DA-3 risultano non presidiati alla data del 2026-11-16.
> Eseguo B6/D3/D4/D8/D9 (+ metà dati di D7) secondo `docs/playbooks/solo-dataset.md`
> sul branch `data-solo`. Obiezioni o rivendicazioni entro il SAL 1 (2026-11-20).
> Le decisioni prese in solo sono registrate nel dizionario dati.

*Da inviare sul canale del team + email; il silenzio dopo la scadenza è consenso
documentato. Riassegnazione formale al prossimo sync (playbook §8.5).*
