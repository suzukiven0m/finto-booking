# O5 — stato settimanale al cliente (testo finale, send-ready)

Settimana del SAL 1 (ven 2026-11-20). Testo finale preparato da WP5 il
2026-11-19 sulla bozza WP4 di `docs/client-comms.md`. **Pronto per l'invio di
venerdì; nulla è ancora inviato.** Invio + archiviazione della copia in
`docs/client-comms.md` sono azioni umane (ledger HA-02). Il testo da inviare è
quanto segue.

---

Buongiorno,

stato settimanale in vista del SAL 1 di domani (ven 20 nov), dove congeliamo
schema e contratto API con voi presenti.

**Gap riconosciuto:** lo stato del 13 nov non risulta inviato/archiviato
(nessuna evidenza): gap riconosciuto. Questo aggiornamento recupera il ritardo.

**Dati.** Il dataset è riproducibile end-to-end e il baseline è verificato al
centesimo: 61.777 prenotazioni valide, 218.410 room-night, 22.976.960,13 € di
ricavo realizzato, ADR 105,20 €, cancellation rate 27,49% (deduplica sulle 32
colonne originali del CSV, 87.396 righe). Le recensioni vengono dal corpus
TripAdvisor reale (ADR 0003, opzione E): 1.638 recensioni (762 + 876) con voti
reali nelle cinque dimensioni.

**Disclosure complete (vincolanti, riportate anche in dashboard):**

1. Le due strutture «Buby Lago/Montagna» sono **fittizie**: mappatura 1:1 dei
   due tipi di hotel del CSV (Resort/City). Nessun dato Buby reale.
2. Il legame recensioni↔prenotazioni è **asserito a livello di proprietà**, non
   fattuale: occupazione/ricavi solo dalle prenotazioni, reputazione solo dalle
   recensioni.
3. La capacità (190/230 camere) è **assunta**, inferita dal picco osservato e
   mai misurata: occupazione e RevPAR non sono misure (footnote in dashboard).
4. Le email guest-request sono **sintetiche** (800, italiano, 6 categorie, nomi
   inventati): non sono corrispondenza reale di ospiti.
5. **Nessun overlap temporale (S4):** le recensioni sono tutte del 2012
   (2012-01-02…2012-12-19), le prenotazioni coprono 2015-07…2017-09: zero mesi
   in comune. Nessuna analisi congiunta a livello di mese esiste: solo
   comparazione a livello di proprietà; il trend reputazione è solo-2012,
   nessuna lettura causale accanto all'occupazione.
6. Il corpus recensioni è **solo inglese**; la demo email resta italiana.
7. **N reale = 1.638, non 20k**: si prendono tutte le recensioni delle due
   strutture più recensite e si fissa l'N reale.

**Nessun dato reale del cliente è mai arrivato**: la sostituzione dei dati è
dichiarata (ADR 0003 opzione E) e nessun dato cliente entra nel repository; la
richiesta dati scritta (B4) resta da archiviare.

**Tecnica al 19 nov.** Contratto API con le contraddizioni S1/S2/S3 corrette
(PR #11), pronto per il freeze; schema a 0005 con le decisioni pre-freeze su
auth e output NLP (PR #12); API mergiata (PR #9): 4 operazioni su 11 del
contratto (properties, kpis/summary, kpis/daily, auth/login) verificate su dati
reali contro gli esempi del contratto — token finto fino a D11; login UI
mergiata (PR #10); dashboard ancora sul mock Prism fino allo swap D17.

**Domani al SAL 1:** freeze di schema (0001–0005) + contratto (1.0.0) con
sign-off del catalogo KPI da parte di entrambi i team, disclosure complete e
tag v1.0.0. Restano da implementare le altre 7 operazioni, l'NLP (D14/D15,
componente obbligatoria), l'auth reale (D11), lo swap su dati reali (D17) e il
deploy.

---

*Fine del testo da inviare. Promemoria per il lead (non fa parte dello stato):
inviare venerdì 20 nov e archiviare la copia inviata in `docs/client-comms.md`
(HA-02). Il gap del 13 nov usa la formulazione ammorbidita dal reviewer:
«non risulta inviato/archiviato (nessuna evidenza)», non la negazione forte.*
