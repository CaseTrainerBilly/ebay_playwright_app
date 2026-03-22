# eBay Sold Items Research App

This project is a Flask web app that opens a real Playwright-powered Chromium session, searches sold eBay listings, filters the results, calculates reseller-oriented pricing metrics, and exports the visible result set to an XLSX spreadsheet with embedded images.

It is designed around a practical problem: normal HTTP scraping is unreliable on eBay because challenge pages appear frequently, so this app uses a persistent browser profile and lets the user complete the challenge once in a real browser window.

## What The App Does

- Searches sold listings on `www.ebay.co.uk` or `www.ebay.com`
- Uses a persistent Playwright browser profile in `ebay_browser_profile/`
- Extracts sold cards from the current eBay card layout
- Filters results to remove irrelevant or mismatched listings
- Applies UK-specific buyer-protection and seller-payout assumptions
- Calculates median, average, spread, ROI, and recommended max buy price
- Shows results in a Flask UI
- Exports the current cached result set to `.xlsx`
- Provides an API endpoint for programmatic search
- Provides an item detail page with market context for one result

## Stack

- Python 3.11+
- Flask
- Playwright
- Plain HTML templates with Jinja
- Plain CSS

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

Open:

```bash
http://127.0.0.1:5000
```

## GitHub Pages UI Demo

If you want to show the interface on GitHub Pages, use the static files in `docs/`.

- `docs/index.html` shows the search/results UI with bundled demo data
- `docs/item.html` shows the item detail page
- `docs/assets/` contains the stylesheet and small client-side demo script

This is intentionally a visual demo only:

- GitHub Pages cannot run the Flask app
- Playwright scraping will not work there
- XLSX export is shown as a disabled UI action

To publish it, set your GitHub Pages source to the `docs/` folder on your default branch.

## First Run And Challenge Flow

The scraper launches Chromium with:

- `headless=False`
- a persistent profile folder: `ebay_browser_profile`
- locale `en-GB`
- a desktop Chrome-style user agent

If eBay shows a challenge page:

1. Complete the challenge in the opened browser window.
2. Close the window.
3. Run the same search again.

The saved profile is intended to preserve the session for later searches.

## Project Files

- `app.py`: Flask routes, result caching, HTML rendering, API responses, XLSX download endpoint
- `scraper.py`: Playwright browser automation, eBay URL building, card extraction, listing relevance filtering
- `csv_export.py`: price math, fee assumptions, resale metrics, CSV generation
- `xlsx_export.py`: manual XLSX generation, image downloading, workbook packaging
- `templates/index.html`: search page and result list
- `templates/item.html`: single item detail page with market metrics
- `static/style.css`: UI styling
- `requirements.txt`: Python dependencies

## Important Runtime Files

- `ebay_browser_profile/`: persistent Chromium profile used by Playwright
- `debug_playwright_response.html`: last saved raw page HTML after a search

These are local/runtime artifacts and are intentionally ignored by Git.

## High-Level Flow

1. The user submits a search from `/`.
2. `POST /search` validates the query, domain, and limit.
3. `scrape_ebay_sold()` launches Playwright, loads the eBay sold-search URL, and extracts `li.s-card` entries.
4. Python filters the raw cards for relevance, sold status, valid pricing, and marketplace rules.
5. A normalized result payload is returned to Flask.
6. Flask stores the payload in the in-memory `RECENT_RESULTS` cache.
7. The UI renders cards, summary stats, and an XLSX export link.
8. `/item` reads the cached result set and shows one item in more detail.
9. `/export-xlsx` reads the same cached result set and builds a spreadsheet without rerunning the scraper.

## Routes

| Route | Method | Purpose |
| --- | --- | --- |
| `/` | `GET` | Render search form and optionally results |
| `/search` | `POST` | Execute a sold-listing search and render results |
| `/export-xlsx` | `GET` | Export the current cached search results as an XLSX file |
| `/api/search` | `GET` | Return JSON search results |
| `/item` | `GET` | Render detail page for a single cached result item |

## Request Inputs

### Search Form

- `query`: free-text product search
- `domain`: `www.ebay.co.uk` or `www.ebay.com`
- `limit`: integer clamped to `1..50`

### API Search

- `query`: required
- `domain`: optional, defaults to `www.ebay.co.uk`
- `limit`: optional, defaults to `40`, clamped to `1..50`

## Data Shape

### Search Result Payload

The main result object returned by `scrape_ebay_sold()` and cached in Flask has this structure:

```python
{
    "query": str,
    "count": int,
    "average_price": float | None,
    "lowest_price": float | None,
    "highest_price": float | None,
    "items": list[dict],
    "debug": {
        "final_url": str,
        "page_title": str,
        "cards_found": int,
        "items_after_filtering": int,
    },
}
```

### Item Object

Each listing in `results["items"]` is normalized into a dictionary with keys like:

```python
{
    "title": str,
    "price_text": str,
    "price_value": float | None,
    "url": str,
    "image_url": str,
    "description": str,
    "condition": str,
    "sold_date": str,
    "shipping_text": str,
    "location_text": str,
    "listing_id": str,
    "marketplace": str,
    "search_query": str,
}
```

## Pricing And Reseller Logic

The pricing model in this repo is intentionally opinionated and reseller-oriented.

### UK Logic

For `www.ebay.co.uk`, the app treats the observed sold price as the buyer-facing total and estimates:

- buyer protection fee
- seller net proceeds
- a recommended maximum buy price for flipping

### Non-UK Fallback

For marketplaces other than `www.ebay.co.uk`, the fallback seller fee assumption is:

- `13% + 0.30`

### Max Buy Logic

`calculate_resale_metrics()` uses:

- median seller-receives price after outlier filtering
- total assumed costs of `1.00`
- target profit tiers
- a hard buy ceiling capped at `55%` of expected sale price

This produces:

- expected sale price
- average sale price
- spread
- sell-through confidence
- recommended max buy price
- expected profit
- ROI

## Module Reference

## `app.py`

### Globals

| Name | Type | Purpose |
| --- | --- | --- |
| `app` | `Flask` | Main Flask application instance |
| `RECENT_RESULTS` | `dict[str, dict]` | In-memory cache of the most recent search result payloads |

### Functions

#### `store_results(results: dict) -> str`

Creates a random token with `uuid.uuid4().hex`, stores the supplied result payload in `RECENT_RESULTS`, trims the cache to 20 entries, and returns the token.

#### `home()`

Renders `templates/index.html` with empty/default state values:

- `results=None`
- `results_token=None`
- `error=None`
- `query=""`
- `domain="www.ebay.co.uk"`
- `limit=40`

#### `search()`

Reads form data from `request.form`, validates and clamps `limit`, rejects empty queries, calls `scrape_ebay_sold()`, stores the returned results with `store_results()`, and re-renders the search page with either results or an error message.

Behavior summary:

- catches `EbayChallengeError` and displays a user-facing challenge message
- catches generic exceptions and shows a generic fetch failure message

#### `export_xlsx()`

Reads a cached search token from the query string, looks up the cached result set, builds an XLSX workbook with `build_xlsx()`, writes it to a temporary file, sanitizes the filename from the original search query, and serves it with `send_file()`.

Important detail:

- this export does not rerun the scraper
- it only uses what is already stored in `RECENT_RESULTS`

#### `api_search()`

API version of the search flow. Reads query parameters, validates inputs, calls `scrape_ebay_sold()`, and returns JSON.

Behavior summary:

- returns `400` for missing query
- returns `400` for `EbayChallengeError`
- returns `500` for other exceptions

#### `item_detail()`

Renders `templates/item.html` for a single result item from a cached search payload.

It:

- reads `token` and `index` from the query string
- validates token presence
- validates token freshness in `RECENT_RESULTS`
- validates index bounds
- calculates item-specific price estimates
- calculates set-wide market metrics with `calculate_resale_metrics()`
- renders the detail page

## `scraper.py`

### Globals

| Name | Type | Purpose |
| --- | --- | --- |
| `USER_AGENT` | `str` | Desktop Chrome-like user agent string used for Playwright pages |

### Classes

#### `EbayChallengeError`

Custom exception used when eBay redirects the session to a challenge page. Flask catches it and shows a retry message instead of a stack trace.

### Functions

#### `parse_price(price_text: str)`

Extracts the first numeric price from a string like `£12.99` or `$12.99`, removes commas, and returns a `float` or `None`.

#### `clean_text(value: str | None) -> str`

Converts `None` to an empty string and strips leading/trailing whitespace.

#### `extract_listing_id(item_url: str) -> str`

Attempts to extract an eBay listing ID from:

- `/itm/.../<digits>`
- query-string pattern `?item=<digits>`

Returns an empty string if neither pattern matches.

#### `_normalize_words(value: str) -> list[str]`

Lowercases text and extracts only alphanumeric word tokens. Used heavily by the matching logic.

#### `_stem_word(word: str) -> str`

Applies a very lightweight plural-reduction rule:

- `ies -> y`
- `es ->`
- trailing `s ->`

This supports fuzzy title matching without using a stemming library.

#### `_token_matches(query_token: str, title_tokens: set[str], title_stems: set[str]) -> bool`

Tests whether one query token is present in the title token set. It supports:

- exact numeric matching
- exact token matching
- stem matching
- prefix matching for tokens with length `>= 4`

#### `_parse_filter_text(filter_text: str) -> tuple[list[str], list[str]]`

Splits optional filter text into:

- required phrases
- excluded phrases

It recognizes exclusion patterns such as:

- `-"quoted phrase"`
- `-token`
- `no something`
- `without something`

#### `_required_match_threshold(required_words: set[str]) -> int`

Controls how strict matching must be:

- `0` words -> `0`
- `1..3` words -> all must match
- `4+` words -> all but one must match

#### `_normalize_phrase(value: str) -> str`

Joins normalized word tokens back into a space-separated normalized string.

#### `_required_phrase_matches(phrase: str, normalized_title: str, title_words: set[str], title_stems: set[str]) -> bool`

Checks whether one required phrase is represented in the title.

For multi-word phrases it enforces ordered appearance and blocks misleading sequences such as terms separated by words like:

- `no`
- `without`
- `missing`

For single-word or tokenized phrases it falls back to token/stem threshold matching.

#### `is_relevant_listing(query: str, title: str, filter_text: str = "") -> bool`

Main title relevance filter.

It:

- normalizes query and title tokens
- folds in required filter words
- applies threshold-based token matching
- enforces required phrases
- rejects excluded phrases
- removes generic accessory-only results in some `only` cases
- requires `"only"` or `"loose"` in the title when the query/filter implies an item-only search

This function is the core defense against irrelevant sold-card matches.

#### `is_uk_only_listing(location_text: str, full_text: str, marketplace: str) -> bool`

Used only for `www.ebay.co.uk`.

If the marketplace is UK, it tries to keep only listings that appear to originate from the UK by examining:

- explicit `location_text`
- fallback `from ...` patterns in full card text

If no strong non-UK signal is found, it defaults to allowing the listing.

#### `build_search_url(query: str, ebay_domain: str, filter_text: str = "") -> str`

Builds the sold-search URL by combining query text and optional filter text and appending sold/completed eBay search parameters.

#### `_normalize_domain(ebay_domain: str) -> str`

Whitelists supported marketplaces:

- `www.ebay.co.uk`
- `www.ebay.com`

Any unsupported input falls back to `www.ebay.co.uk`.

#### `scrape_ebay_sold(query: str, limit: int = 20, ebay_domain: str = "www.ebay.co.uk", filter_text: str = "") -> dict`

This is the main scraping entry point.

What it does:

1. Cleans and clamps inputs.
2. Normalizes the marketplace domain.
3. Builds the sold-search URL.
4. Opens a persistent Chromium context using `ebay_browser_profile`.
5. Loads the page and waits briefly.
6. Saves raw HTML to `debug_playwright_response.html`.
7. Detects challenge pages and raises `EbayChallengeError` if needed.
8. Waits for cards, scrolls once, and evaluates `li.s-card` elements in browser JavaScript.
9. Extracts raw card fields such as title, price, URL, image URL, condition, sold date, shipping, location, and full text.
10. Filters cards in Python for sold status, relevant titles, price validity, duplicate URLs, and marketplace-specific rules.
11. Truncates to the requested `limit`.
12. Calculates top-level summary values like average, low, and high price.
13. Returns a normalized result dictionary with `items` and `debug` metadata.

Important implementation details:

- browser runs non-headless
- timeout is set to `60000ms`
- HTML is always dumped for debugging
- duplicate results are removed by URL
- card parsing depends on current eBay DOM selectors and may need updates if eBay changes markup

## `csv_export.py`

### Constants

| Name | Value | Meaning |
| --- | --- | --- |
| `PACKAGING_COST` | `0.20` | Packing-material cost assumption |
| `PROMOTED_LISTING_COST` | `0.30` | Advertising/promoted listing assumption |
| `RISK_BUFFER_COST` | `0.50` | Safety margin for uncertainty |
| `BUY_RATIO_CAP` | `0.55` | Hard cap for max buy price as a fraction of expected sale value |
| `UK_PRIVATE_SELLER_FEE_RATE` | `0.0` | UK private seller variable fee assumption |
| `UK_PRIVATE_SELLER_FIXED_FEE` | `0.0` | UK private seller fixed fee assumption |
| `DEFAULT_BUSINESS_FEE_RATE` | `0.13` | Fallback variable fee assumption outside UK private model |
| `DEFAULT_BUSINESS_FIXED_FEE` | `0.30` | Fallback fixed fee assumption outside UK private model |

### Functions

#### `_money(value: float | None) -> str`

Formats a numeric value to two decimal places or returns an empty string.

#### `_percent(value: float | None) -> str`

Formats a ratio like `0.24` as a whole-percent string like `24%`.

#### `estimate_uk_buyer_protection_fee_from_item_price(item_price: float) -> float`

Estimates UK buyer protection from item price using a tiered fee structure:

- base `0.10`
- `7%` on the first `20`
- `4%` on the next `280`
- `2%` on the next `3700`

Returns a rounded total.

#### `estimate_uk_private_seller_payout_from_buyer_total(buyer_total: float | None) -> float | None`

Back-calculates the seller's likely received amount from the buyer-facing total for UK private listings by inverting the fee tiers.

#### `_fee_model(marketplace: str | None) -> tuple[float, float]`

Returns the fee-rate/fixed-fee pair for the given marketplace.

#### `estimate_ebay_fee(sold_price: float | None, marketplace: str | None) -> float | None`

Calculates seller fee as:

```python
(sold_price * fee_rate) + fixed_fee
```

using the marketplace fee model.

#### `estimate_buyer_protection_fee(sold_price: float | None, marketplace: str | None) -> float | None`

For UK listings, estimates buyer protection by subtracting inferred seller proceeds from the observed sold total. For other marketplaces it currently returns `None`.

#### `estimate_seller_receives(sold_price: float | None, marketplace: str | None) -> float | None`

Returns estimated seller proceeds:

- UK: uses the private-seller payout back-calculation
- non-UK: subtracts `estimate_ebay_fee()` from sold price

#### `_target_profit(expected_sale_price: float) -> float`

Returns tiered target profit:

- under `10` -> `2.0`
- under `20` -> `4.0`
- otherwise -> `6.0`

#### `_remove_outliers(values: list[float]) -> list[float]`

Uses the IQR method to remove extreme price values. If fewer than 4 values exist, it leaves the list unchanged.

#### `_sell_through_confidence(count: int, spread_ratio: float | None) -> str`

Returns a simple confidence label:

- `High`
- `Medium`
- `Low`

based on sample size and price spread.

#### `calculate_resale_metrics(results: dict) -> dict`

The core economics function for the app.

It:

- extracts item prices
- converts them to estimated seller proceeds
- removes outliers
- calculates median, average, min, max, spread, spread ratio
- adds cost assumptions
- applies target profit logic
- applies the `BUY_RATIO_CAP`
- calculates ROI and expected profit
- returns a summary dictionary used by the detail page and exports

#### `build_csv(results: dict) -> str`

Builds a CSV string from the current result payload.

Important note:

- this function exists and works
- the current Flask UI does not expose a CSV download route
- the live app currently exports only XLSX

## `xlsx_export.py`

### Constants

| Name | Type | Purpose |
| --- | --- | --- |
| `VISIBLE_COLUMNS` | `list[str]` | Spreadsheet columns written into the worksheet |

### Functions

#### `_cell_ref(col_index: int, row_index: int) -> str`

Converts numeric row/column coordinates into Excel-style references like `A1`, `B2`, `AA10`.

#### `_inline_string_cell(col_index: int, row_index: int, value: str) -> str`

Builds raw worksheet XML for an inline string cell after XML-escaping its contents.

#### `_number_cell(col_index: int, row_index: int, value: float | int | None) -> str`

Builds raw worksheet XML for a numeric cell or an empty cell when the value is `None`.

#### `_money(value: float | None) -> str`

Formats a number to two decimals for summary text strings inside the workbook.

#### `_percent(value: float | None) -> str`

Formats a ratio into a percent string for workbook summary text.

#### `_fetch_image_bytes(image_url: str) -> tuple[bytes, str] | None`

Attempts to download a listing image and infer its file extension.

Behavior summary:

- returns `None` if URL is missing or every fetch attempt fails
- retries alternate `.jpg` and `.jpeg` forms when the source URL uses `.webp`
- uses content-type headers and file signatures to determine image type
- supports `jpeg`, `png`, and `gif`

#### `_drawing_anchor_xml(image_index: int, row_zero_based: int) -> str`

Builds the drawing XML that anchors one image into the spreadsheet grid.

#### `_worksheet_xml(results: dict, has_images: bool) -> str`

Builds the XML for `sheet1`, including:

- header row
- one row per item
- a final summary row
- an optional drawing reference when embedded images are present

#### `build_xlsx(results: dict) -> bytes`

Builds the final XLSX file in memory by manually assembling the OpenXML ZIP structure.

It creates:

- workbook XML
- relationships files
- worksheet XML
- document property XML
- optional drawing XML
- optional downloaded image binaries

and returns the final workbook as raw bytes.

## Template Reference

## `templates/index.html`

Purpose:

- shows search form
- displays top-level stats
- shows debug metadata
- exposes spreadsheet export
- renders each result card with image, price, condition, shipping, location, listing ID, and links

Important template variables:

- `results`
- `results_token`
- `error`
- `query`
- `domain`
- `limit`

## `templates/item.html`

Purpose:

- shows one listing in more detail
- displays observed price, buyer protection estimate, seller receive estimate, and market context
- includes source links and buy-decision notes

Important template variables:

- `item`
- `item_buyer_protection_fee`
- `item_seller_receives`
- `market_metrics`
- `token`
- `error`
- `query`
- `index`

## Styling Reference

## `static/style.css`

The CSS defines:

- neutral panel-based layout
- eBay-inspired brand accent colors
- grid-based search/results layout
- result-card and item-detail presentation
- pill, chip, stat-card, and action-button styles

Notable custom properties in `:root`:

- background and panel colors: `--bg`, `--panel`, `--panel-soft`, `--panel-tint`
- border colors: `--line`, `--line-strong`
- text colors: `--text`, `--muted`
- accent colors: `--accent`, `--accent-soft`, `--accent-strong`
- eBay-inspired brand colors: `--brand-blue`, `--brand-red`, `--brand-yellow`, `--brand-green`

## Current Limitations

- The scraper depends on eBay's current DOM structure and selectors.
- A browser window is required because the scraper runs with `headless=False`.
- `RECENT_RESULTS` is in-memory only and resets when the Flask process restarts.
- Cached results expire naturally as the process restarts or as the 20-entry cache rotates.
- The app writes `debug_playwright_response.html` on every search.
- CSV export exists in code but is not currently wired into the Flask UI.
- XLSX image embedding depends on remote image URLs still being reachable at export time.

## Notes For Future Development

- add persistent cache/storage instead of in-memory `RECENT_RESULTS`
- expose CSV export in the UI if needed
- add automated tests around price math and listing relevance filtering
- make filter text a user-facing form input
- add structured logging instead of relying on raw debug HTML dumps
- consider optional headless mode once challenge handling is more robust

## Dependencies

`requirements.txt`

```txt
flask==3.1.0
playwright==1.51.0
```
