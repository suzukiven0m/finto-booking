# Assistente email — analisi D15

**Branch:** fix/wp10-email-assistant · **Script:** `data/etl/classify_emails.py`

---

## 1. Metodo

**Classificatore:** lessicale deterministico basato su regex derivate direttamente
dal vocabolario dei template del generatore (`data/etl/gen_emails.py`, seed 42).

**Giustificazione della tecnica:** il corpus e' sintetico (800 email, 8+ template
per categoria, slot noti). Le regex coprono il vocabolario degli slot
(`BILLS`, `PROBLEMS`, `REQUESTS`, ecc.) e le frasi-chiave di ciascun template.
Il classificatore e' trasparente, riproducibile e non richiede training.

**Urgenza:** regole per categoria derivate dai valori `urgency` dei template,
con override testuale per i casi non-default (es. `problema di salute` ->
cancellation high; `recensione negativa` -> complaint medium).

**Dichiarazione di onesta' (obbligatoria):** l'F1 riportato e'
*sul corpus sintetico che ha generato le stesse regex*. **Non e' evidenza di
performance su email reali.** Il corpus ha 800 email generate da ~48 template
con slot controllati; un classificatore lessicale non generalizza a testi fuori
dal vocabolario del generatore.

---

## 2. Allineamento gold

| Metrica | Valore |
|---|---|
| Email nel DB | 800 |
| ID nel gold | 800 |
| ID solo nel predetto | 0 |
| ID solo nel gold | 0 |

Allineamento completo: `ids_matched == n_emails` OK

---

## 3. Risultati — categoria

**Macro-F1 categoria: 0.9901**

| Categoria | Precision | Recall | F1 |
|---|---|---|---|
| availability | 1.0000 | 0.9701 | 0.9848 |
| cancellation | 1.0000 | 1.0000 | 1.0000 |
| complaint | 1.0000 | 1.0000 | 1.0000 |
| special_request | 1.0000 | 0.9699 | 0.9847 |
| billing | 1.0000 | 1.0000 | 1.0000 |
| info | 0.9437 | 1.0000 | 0.9710 |

### Confusion matrix (categoria)

| reale \ predetto | availability | cancellation | complaint | special_request | billing | info |
| --- | --- | --- | --- | --- | --- | --- |
| **availability** | 130 | 0 | 0 | 0 | 0 | 4 |
| **cancellation** | 0 | 133 | 0 | 0 | 0 | 0 |
| **complaint** | 0 | 0 | 133 | 0 | 0 | 0 |
| **special_request** | 0 | 0 | 0 | 129 | 0 | 4 |
| **billing** | 0 | 0 | 0 | 0 | 133 | 0 |
| **info** | 0 | 0 | 0 | 0 | 0 | 134 |

---

## 4. Risultati — urgenza

**Macro-F1 urgenza: 0.9659**

| Urgenza | Precision | Recall | F1 |
|---|---|---|---|
| low | 0.9831 | 0.9295 | 0.9555 |
| medium | 0.9091 | 0.9778 | 0.9422 |
| high | 1.0000 | 1.0000 | 1.0000 |

### Confusion matrix (urgenza)

| reale \ predetto | low | medium | high |
| --- | --- | --- | --- |
| **low** | 290 | 22 | 0 |
| **medium** | 5 | 220 | 0 |
| **high** | 0 | 0 | 263 |

---

## 5. Percorso di upgrade LLM (gated su O2/HA-05)

L'upgrade da classificatore lessicale a LLM (es. GPT-4o, Mistral via API)
e' bloccato sulla decisione umana **HA-05** (chiavi LLM + chi paga, scaduta
2026-11-16, `docs/reviews/human-actions.md`). Finche' HA-05 non e' chiusa
(`done -- data -- link evidenza`), il fallback lessicale e' l'unico componente
attivo.

Passi tecnici *dopo* HA-05:
1. Aggiungere la chiave API in `backend/app/config.py` (env var, non in repo).
2. Sostituire `classify_category` / `classify_urgency` in `email_nlp.py` con
   chiamata LLM (zero-shot o few-shot con gli stessi template come esempi).
3. Rieseguire eval su `email_gold.csv` e aggiornare questo report.
4. Se l'F1 su email reali diverge (atteso), integrare un campione reale nel gold.

---

## 6. Comando riproducibile

```bash
# eval (legge DB + gold, scrive metriche e questo report):
docker run --rm -i --network container:buby-postgres \
  -v "$PWD":/repo:ro -v "$PWD/data/eval":/repo/data/eval \
  -v "$PWD/docs/analysis":/repo/docs/analysis \
  -w /repo -e PYTHONPATH=/repo/.venv/lib/python3.12/site-packages:/repo/backend:/repo/data \
  python:3.12-slim python data/etl/classify_emails.py

# persist (scrive nel DB, idempotente):
docker run --rm -i --network container:buby-postgres \
  -v "$PWD":/repo:ro -w /repo \
  -e PYTHONPATH=/repo/.venv/lib/python3.12/site-packages:/repo/backend:/repo/data \
  python:3.12-slim python data/etl/classify_emails.py --persist
```

---

*Generato automaticamente da `data/etl/classify_emails.py` -- 800 email su DB buby.*
