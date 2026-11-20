# Human-action ledger — azioni che solo gli umani possono eseguire (WP6)

Registro aperto il **2026-11-19** (audit shepherd, SAL 1 domani). Gli agent preparano
gli artefatti; **firmare, inviare, pagare, presentare possono farlo solo gli umani**.
Stesso principio di `docs/client-comms.md`: non si dichiara fatto ciò che non è
documentato. All'apertura: 14 righe, 0 done, 4 overdue (HA-05, HA-08, HA-09, HA-10).
Aggiornamento 2026-11-20 (remediation): +HA-15 (crediti OpenRouter); HA-14 artefatti
pronti (WP7 implementato, memo WP12 in docs/analysis/demand-pricing.md §10).

## Regole

- **Nessuna riga viene mai chiusa da un agent.** Un agent può preparare l'artefatto e
  aggiornare i puntatori, non scrivere `done`.
- **Chiusura (solo umani):** sostituire lo stato nella riga con
  `done — <data> — <link evidenza>` (copia inviata archiviata, verbale, commento PR,
  ricevuta account). Senza evidenza linkata la riga resta aperta.
- Stato iniziale: `open`; `overdue` se la scadenza è già passata al 2026-11-19.
- Le conseguenze sono riprese dall'audit `2026-11-19-shepherd-audit.md` §8 (citato per
  riga); la mappatura completa §8 → righe è in fondo.

## Ledger

| ID | Azione (esecuzione umana) | Owner | Scadenza | Conseguenza se saltata | Evidenza/artefatto | Stato |
|---|---|---|---|---|---|---|
| HA-01 | Sign-off del catalogo KPI da parte di **entrambi i team**: nomi, data, righe di firma | Lead DA + lead WSA | 2026-11-20 (SAL 1) | Il freeze senza sign-off non è il freeze valutato (§8.4) | `docs/sal1/kpi-signoff.md` (WP5, in preparazione); checklist freeze in delivery-plan §4 | open |
| HA-02 | Inviare + archiviare lo stato scritto settimanale O5 al cliente. Lo stato del 13 nov non ha alcuna evidenza: **il gap va riconosciuto esplicitamente nell'invio**; lo stato del 20 nov è dovuto domani | Lead | 2026-11-20 (ven); 2026-11-13 già senza evidenza | Obbligo R16 di stato settimanale mancato: gli stati mancanti sono deadline miss di valutazione (§8.4) | Bozza: client-comms.md §O5; testo finale preparato da WP5; copia inviata da archiviare in client-comms.md | open |
| HA-03 | Inviare la notifica di solo-work (ancora bozza) sul canale team + email e archiviarla; la finestra obiezioni si chiude al SAL 1 | Lead | Prima del SAL 1, 2026-11-20 | Il voto di collaborazione si regge su un WSA che fa il lavoro di due team senza traccia di consenso (§8.5, R13) | client-comms.md §«Notifica al team» (bozza — da inviare); playbook solo-dataset §8.1 | open |
| HA-04 | Riassegnazione formale dei workstream DA-1 (Daniele, 0 commit), DA-2 (Federico Bertazzoni, solo md di teoria), DA-3 (Fabio Baradello, solo upload dataset), WSA-2 (Simone, 0 commit): **owner nominati + date**. D14 riceve un owner nominato **per primo** (componente obbligatoria del brief, zero codice) | Lead | Sync 2026-11-20 → MVP 2026-12-03 | Un WSA continua a portare due team; la componente obbligatoria testi/email (R6) fallisce al 18 dic (§8.5) | Audit §5 (staffing nominato); playbook §8.5; esito: verbale del sync + docs/plan.md §Workstreams aggiornati | open |
| HA-05 | O2 — chiavi LLM e **chi paga**: decisione con il cliente e registrazione | DA-3 + lead | 2026-11-16 — scaduta | Percorso LLM di D15 morto; il grading di AI-reliability non ha numeri (§8.7) | client-comms.md O2 🔴; delivery-plan §9 O2; blocca l'upgrade LLM di WP10 (il fallback a template si costruisce anche senza chiavi) | overdue |
| HA-06 | O1 — stato dell'accordo NDA/GDPR/anonimizzazione con il cliente. La mitigazione tecnica esiste (email sintetiche, niente PII nel repo) ma **mitigazione ≠ accordo** | Lead | 2026-11-20 (SAL 1) | Obbligo del brief senza traccia documentale alla valutazione (R17, §8.10) | client-comms.md O1 🔴; mitigazione verificata: data-dictionary §1 e §4 | open |
| HA-07 | O3 — record di ownership di codice/analisi/modelli concordato con il cliente | Lead | 2026-11-20 (SAL 1) | Stessa classe: obbligo del brief senza traccia documentale alla valutazione (§8.10) | client-comms.md O3 🔴; delivery-plan §9 O3 | open |
| HA-08 | O4 — conferma della 4ª sessione cliente (presenza alla demo finale del 18 dic; kickoff 26 ott, SAL 1 20 nov, finale 18 dic + una sessione ancora da confermare) | Lead | 2026-11-13 — scaduta | Stessa classe: obbligo del brief senza traccia documentale alla valutazione (§8.10) | client-comms.md O4 🔴; delivery-plan §9 O4 | overdue |
| HA-09 | B4 — richiesta dati al cliente per iscritto: archiviare l'evidenza (copia qui o link drive) | Lead | 2026-11-10 — scaduta | La sostituzione dei dati cliente resta non documentata (audit R4, §5 B4) | client-comms.md B4 🔴; delivery-plan §1 B4 | overdue |
| HA-10 | Account di deploy (Render per l'API + Vercel per la SPA + Neon per Postgres, free tier): creazione umana e registrazione della decisione di target, scaduta il 13 nov. La demo gira comunque in **locale** (docker compose); istanza pubblica scaldata 10 min prima di ogni check esterno | WSA-3 + lead | Decisione: 2026-11-13 — scaduta; account: 2026-12-17 (D18) | Nessun deploy né URL pubblico per il grading; WP14 bloccato (§8.10) | delivery-plan §2 «Deploy target»; audit §8.10 | overdue |
| HA-11 | Presentare SAL 1 davanti al cliente (dry run incluso): freeze con sign-off e disclosure complete — S4 (recensioni 2012 vs prenotazioni 2015–17, zero overlap mensile), sostituzioni dati, capacità assunta | Lead + team | Dry run 2026-11-19; SAL 1 2026-11-20 | Freeze non valutato; il gap 2012/2015 scoperto dal cliente invece che dichiarato dal team legge come occultamento (§8.4) | Slide preparate da WP5 (in preparazione); disclosure: audit §3 S4 e §8.4 | open |
| HA-12 | Demo finale del 18 dic davanti all'azienda + presenza a **2 rehearsal** (script preparato da WP14) | Tutto il team; lead coordina le rehearsal | Rehearsal in Sprint 4 (11–17 dic); demo 2026-12-18 | Demo non provata: nessuna rehearsal archiviata, si va in scena senza rete (§8.10, R15) | delivery-plan §8 (rehearsal ×2); script WP14 (in preparazione) | open |
| HA-13 | Branch protection GitHub: richiede 1 review approvante ma l'unico account gh è l'autore delle PR → self-approval bloccato. #11/#12/#9/#10 mergiate il 2026-11-19 con sign-off indipendente nei commenti PR + admin override (limite single-account). **Un secondo account holder del team deve approvare le PR future (da WP7 in poi)** o adeguare la branch protection | Lead + secondo account holder del team | Prima del prossimo merge (WP7+) | Ogni merge richiede bypass admin: il gate di review si indebolisce nella traccia documentale | Protection gh: 1 review approvante, `enforce_admins: false`; sign-off: PR #11 commento 7011371703, PR #12 commento 7011478799, PR #9 commento 7011607497, PR #10 commento 7011609691; review WP1 §4 | open |
| HA-14 | Risolvere con il cliente al SAL 1 le contraddizioni di delivery-plan §11: **D11 auth** «cuttable» vs autenticazione nominata nel brief (WP7 cancella la riga o allega qui una richiesta di waiver scritta al cliente); **D16 forecast** «eventuale» vs obiettivo del caso «prevedere la domanda» (memo WP12: baseline moving-average come stretch o waiver). La decisione del cliente va archiviata in questa riga | Lead + WSA-1 (D11) + DA-3 (D16) | 2026-11-20 (SAL 1) | I tagli silenziosi di requisiti nominati nel brief emergono in sede di valutazione (§6) | delivery-plan §11 (cut-order #1 e #4); audit §6; **artefatti pronti**: WP7 implementato (riga §11 rimossa, PR #18), memo WP12 §10 con opzioni A/B (PR #20) | open |
| HA-15 | Crediti OpenRouter: il modello fallback approvato (claude-sonnet-4.6) ha esaurito i crediti a metà remediation (402, 2026-11-20). Ricaricare se si vuole riusare il fallback; altrimenti i child girano sul modello di sessione (quota recovery verificata) | Lead / chi paga il tooling | Prima del prossimo uso del fallback | I child agent si fermano a metà package (checkpoint-resilient, ma più lento) | Errore 402 OpenRouter 2026-11-20 (run cba1c6b4); handoff remediation | open |

## Mappatura audit §8 → ledger

Ogni azione ranked 1–10 dell'audit §8 è mappata su almeno una riga. Dove l'azione ha una
parte tecnica, quella è dei WP agent (stato nel report di remediation);
qui resta il gate umano che la protegge.

| Audit §8 | Azione (sintesi) | Righe ledger | Parte agent / nota |
|---|---|---|---|
| 1 | Fix del contratto S1/S2/S3 prima del freeze | HA-01, HA-13 | Tecnica: WP1 (PR #11, mergiata). Umano: sign-off del freeze e approvazione/merge |
| 2 | Mergiare o rifiutare esplicitamente le PR #9/#10 | HA-13 | Tecnica+gate eseguiti 2026-11-19: WP3 review indipendente, merge dc572e0/#9 e 1fb7527/#10, sign-off nei commenti PR. Resta HA-13 per le PR future. |
| 3 | Decisioni schema pre-freeze (S7/S8, urgency) | HA-11, HA-13 | Tecnica: WP2 (PR #12, mergiata). Umano: ratifica al SAL 1 e approvazione/merge |
| 4 | Pacchetto SAL 1 (slide, sign-off, tag, dry run, O5) | HA-01, HA-02, HA-11 | Artefatti: WP5. Esecuzione: umani |
| 5 | Riassegnazione formale + notifica solo-work | HA-03, HA-04 | Interamente umana |
| 6 | D11 auth reale + rimozione del taglio o waiver | HA-14, HA-13 | Tecnica: WP7. Umano: waiver scritto del cliente al SAL 1; approvazione/merge |
| 7 | D14/D15 implementazione + decisione O2 chiavi/costi | HA-05, HA-04 | Tecnica: WP10 (upgrade LLM) e WP di implementazione. Umano: chiavi, chi paga, owner nominato di D14 |
| 8 | 7 operazioni contrattuali mancanti + contract test in CI | HA-13 | Tecnica: WP agent (vedi report di stato). Umano: approvazione/merge delle PR |
| 9 | D17 swap mock→reale + E2E | HA-13, HA-12 | Tecnica: WP agent. Umano: merge e demo su dati reali (un mock spacciato per integrato è faked) |
| 10 | D18 release + evidenze O1/O3/O4 | HA-06, HA-07, HA-08, HA-10, HA-12 | Tecnica: WP14. Umano: account deploy, obbligazioni, rehearsal e demo |

## Riferimenti

- Audit: `docs/reviews/2026-11-19-shepherd-audit.md` §8 (azioni ranked 1–10, tutte
  mappate sopra), §5 (staffing nominato), §6 (contraddizioni brief ↔ piano).
- Stato di remediation dei WP: `docs/reviews/2026-11-20-remediation-status.md`.
- Registro comunicazioni cliente: `docs/client-comms.md` — le copie inviate si
  archiviano lì; questo ledger punta all'evidenza, non la duplica.
