# eBay Sold Items Research App (Playwright)

This Flask web app searches eBay sold listings in a real browser session, calculates the average, highest, and lowest sold prices, and exports the results to CSV with reseller-friendly pricing columns.

## Why this version uses Playwright

eBay often redirects normal HTTP scraping to a challenge page. This version opens a persistent Chromium browser profile so you can complete the challenge once and reuse that session on later searches.

## Install

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Run

```bash
python app.py
```

Then open:

```bash
http://127.0.0.1:5000
```

## First run

A Chromium window opens because the scraper runs with `headless=False` and a persistent browser profile in `ebay_browser_profile/`.

If eBay shows a challenge page:

1. complete it in the opened browser window
2. close the browser window
3. run the same search again

The saved browser profile helps future searches reuse the session.

## Files

- `app.py` - Flask app
- `scraper.py` - Playwright scraper
- `csv_export.py` - CSV export builder
- `templates/index.html` - UI
- `static/style.css` - styling
- `debug_playwright_response.html` - saved page HTML after a search

## Notes

- This extracts sold item cards from the current eBay card layout.
- Sponsored cards are excluded.
- Shipping is displayed separately when present.
- CSV export uses the current results already shown in the app and does not rerun the scraper.
- eBay can still change its markup or challenge flow later.
