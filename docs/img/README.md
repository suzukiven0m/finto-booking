# Immagini

Qui vanno le immagini usate nella documentazione (screenshot della dashboard,
diagrammi renderizzati).

## Screenshot della dashboard

Il file `dashboard.png` si genera con lo script `scripts/capture_screenshot.py`
(richiede un browser headless, vedi le istruzioni nel script). Non è committato
di default perché va generato con l'applicazione accesa:

```bash
pip install playwright && python -m playwright install chromium
# con l'app accesa (docs/getting-started.md):
python scripts/capture_screenshot.py
git add docs/img/dashboard.png && git commit -m "docs: screenshot dashboard"
```

Il README lo referencia come `docs/img/dashboard.png`.

## Diagramma di architettura

Il sorgente è `docs/architettura.d2` (D2). Per renderizzarlo in SVG:

```bash
d2 docs/architettura.d2 docs/img/architettura.svg
```

Il SVG renderizzato si può committare qui e linkare dall'indice di architettura.