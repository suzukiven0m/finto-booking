"""Genera lo screenshot della dashboard per il README.

Richiede un browser headless (playwright). Installazione una tantum:

    pip install playwright
    python -m playwright install chromium

Poi, con l'applicazione accesa (vedi docs/getting-started.md):

    python scripts/capture_screenshot.py

Lo script fa login con l'account demo manager, attende il caricamento dei KPI
e salva docs/img/dashboard.png. Il repository non committiamo il PNG generato
da una macchina senza browser: lo generi tu e lo committi quando ce l'hai.
"""

import sys
from pathlib import Path

BASE = "http://localhost:8080"  # web Docker; usa :5173 se sei in sviluppo Vite
OUT = Path(__file__).resolve().parent.parent / "docs" / "img" / "dashboard.png"


def main() -> None:
    try:
        # dipendenza opzionale: import lazy, così lo script dà istruzioni
        # chiare se playwright non è installato invece di un ImportError nudo
        from playwright.sync_api import sync_playwright  # pyright: ignore[reportMissingImports]
    except ImportError:
        print("playwright non installato. Esegui:\n"
              "  pip install playwright\n"
              "  python -m playwright install chromium")
        sys.exit(1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE)
        page.fill('input[type="email"]', "manager@buby.travel")
        page.fill('input[type="password"]', "demo")
        page.click('button[type="submit"]')
        page.wait_for_selector("text=Occupazione", timeout=15000)
        page.wait_for_timeout(1500)  # lascia assestare i grafici
        page.screenshot(path=str(OUT), full_page=True)
        browser.close()
    print(f"Screenshot salvato: {OUT}")


if __name__ == "__main__":
    main()