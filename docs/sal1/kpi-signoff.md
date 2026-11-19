# Sign-off del catalogo KPI — SAL 1 (ven 2026-11-20)

**Con questa firma i due team (DA + WSA) congelano il catalogo KPI al SAL 1.**
Le regole sotto sono quelle vincolanti del dizionario dati §3
(`docs/data-dictionary.md`): ogni numero in dashboard deve avere qui la sua
regola, e qualsiasi endpoint KPI che non riproduce la baseline è sbagliato.
**Ogni modifica successiva al catalogo passa dal protocollo contract-bump:**
nuovo ADR + bump di `info.version` in `openapi.yaml` + migrazione dedicata
(dizionario §2 «Decisioni pre-freeze 2026-11-19»). Il freeze senza sign-off di
entrambi i team non è il freeze valutato (audit §8.4; ledger HA-01).

## Baseline di riferimento (pinned, dizionario §3)

Dopo deduplica esatta sulle 32 colonne originali (87.396 righe) e filtro
`is_canceled=0, nights>0, adr>0`: **61.777** prenotazioni valide ·
**218.410** room-night · **22.976.960,13 €** di ricavo realizzato ·
ADR **105,20 €** · cancellation **27,49%**. Ricomputata al centesimo dal DB
seedato nell'audit 2026-11-19 (§2 R4) e coperta da test (`data/tests/`).

## Catalogo KPI vincolante

| KPI | Regola (sintesi dal dizionario §3) | Baseline pinned |
|---|---|---|
| Cancellation rate | Solo cancellate, dopo deduplica; **No-Show riportato a parte**; rapporto 0–1. Trappola: 37,04% raw vs 27,49% dedup vs 27,98% fondendo il No-Show | **27,49%** (0,2749) |
| ADR | revenue / room-night, solo `adr > 0`; **riportare anche la mediana**. Trappola: media 101,83 distorta dal typo 5400,0 e da 1.959 zeri | **105,20 €** (mediana: valore non pinned) |
| Revenue | `adr × nights`, solo non cancellate, dopo deduplica. Trappola: 42,72 M€ lordo vs 25,996 M€ realizzato vs 22,98 M€ realizzato+dedup | **22.976.960,13 €** |
| Seasonality | Medie **per mese dell'anno**, mai totali mensili grezzi (2015 e 2017 sono anni parziali). `avg_adr` pooled: `Σ(adr × nights) / Σnights` sulle valide per mese di arrivo | Nessun valore pinned (regola sola) |
| Channel mix | Per `market_segment` (8 valori); `agent`/`company` sono ID numerici non mappati: nessuna disaggregazione per OTA con nome | Nessun valore pinned (regola sola) |
| Occupancy / RevPAR | Contro la **capacità assunta** (Lago 190, Montagna 230; picco osservato + margine, mai misurata — Assunzione 3). `occupancy_avg` pooled: `Σroom_nights / (Σroom_count × giorni della finestra)`, non media dei rapporti giornalieri. Rapporto 0–1, mai ×100 | Esempio contratto (finestra 2015-07-01 → 2017-08-31, 420 × 793): `occupancy_avg` **0,6558**, `revpar` **68,99** |

Regole di finestra e aggregazione (riepilogo = coorte di arrivi; giornaliero =
giorni di soggiorno; divergenza ai bordi by design; null-property = somme su
capacità combinata 420): dizionario §3 «Finestra e aggregazione» e
`openapi.yaml` (getKpiSummary / getKpiDaily / getKpiSeasonality), fix S1/S2/S3
pre-freeze (record WP1).

## Firma — team Data Analyst / AI Specialist

Nomi come registrati nel team (`docs/plan.md` §Workstreams, audit §5); i cognomi
mancanti nel record restano come registrati. **Campi data e firma vuoti di
proposito: firmano gli umani al SAL 1 (HA-01); nessun agent li compila.**

| Nome | Ruolo | Data | Firma |
|---|---|---|---|
| Daniele [DA-1] | Structured ETL + KPI | | |
| Federico Bertazzoni [DA-2] | NLP reviews/emails | | |
| Fabio Baradello [DA-3] | Forecast + AI assistant | | |

## Firma — team Web Solutions Architect

| Nome | Ruolo | Data | Firma |
|---|---|---|---|
| Riccardo Bentivoglio [WSA-1] | Backend / API / DB | | |
| Simone [WSA-2] | Frontend / UX | | |
| Facundo Fanti [WSA-3] | Integration / DevOps | | |

---

*Preparato da WP5 (2026-11-19). Stato: pronto per la firma, non firmato.
La chiusura di HA-01 (`done — <data> — <link evidenza>`) è azione umana.*
