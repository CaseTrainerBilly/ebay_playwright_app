from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean
from urllib.parse import quote_plus
import re

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)


class EbayChallengeError(Exception):
    pass


def parse_price(price_text: str):
    if not price_text:
        return None
    cleaned = price_text.replace(",", "")
    match = re.search(r"(\d+(?:\.\d{1,2})?)", cleaned)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def clean_text(value: str | None) -> str:
    return (value or "").strip()


def extract_listing_id(item_url: str) -> str:
    value = clean_text(item_url)
    match = re.search(r"/itm/(?:[^/]+/)?(\d+)", value)
    if match:
        return match.group(1)
    match = re.search(r"[?&]item=(\d+)", value)
    if match:
        return match.group(1)
    return ""


def _normalize_words(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", clean_text(value).lower())


def _stem_word(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        return f"{word[:-3]}y"
    if len(word) > 3 and word.endswith("es"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s"):
        return word[:-1]
    return word


def _token_matches(query_token: str, title_tokens: set[str], title_stems: set[str]) -> bool:
    if query_token.isdigit():
        return query_token in title_tokens

    stemmed_query = _stem_word(query_token)
    if query_token in title_tokens or stemmed_query in title_stems:
        return True

    if len(query_token) >= 4:
        return any(token.startswith(query_token) or query_token.startswith(token) for token in title_tokens)

    return False


def _parse_filter_text(filter_text: str) -> tuple[list[str], list[str]]:
    value = clean_text(filter_text).lower()
    if not value:
        return [], []

    excluded_phrases: list[str] = []

    for quoted_phrase in re.findall(r'-"([^"]+)"', value):
        cleaned = clean_text(quoted_phrase)
        if cleaned:
            excluded_phrases.append(cleaned)
    value = re.sub(r'-"[^"]+"', " ", value)

    for phrase in re.findall(r"\b(?:no|without)\s+([a-z0-9][a-z0-9 '\-/&]+?)(?=,|;|/|\band\b|\bor\b|$)", value):
        cleaned = clean_text(phrase)
        if cleaned:
            excluded_phrases.append(cleaned)
    value = re.sub(r"\b(?:no|without)\s+[a-z0-9][a-z0-9 '\-/&]+?(?=,|;|/|\band\b|\bor\b|$)", " ", value)

    for token in re.findall(r"(?<!\w)-([a-z0-9][a-z0-9-]*)", value):
        cleaned = clean_text(token)
        if cleaned:
            excluded_phrases.append(cleaned)
    value = re.sub(r"(?<!\w)-[a-z0-9][a-z0-9-]*", " ", value)

    required_phrases = [clean_text(part) for part in re.split(r"[,;/]|\band\b", value) if clean_text(part)]
    return required_phrases, excluded_phrases


def _required_match_threshold(required_words: set[str]) -> int:
    if not required_words:
        return 0
    if len(required_words) <= 3:
        return len(required_words)
    return len(required_words) - 1


def _normalize_phrase(value: str) -> str:
    return " ".join(_normalize_words(value))


def _required_phrase_matches(phrase: str, normalized_title: str, title_words: set[str], title_stems: set[str]) -> bool:
    normalized_phrase = _normalize_phrase(phrase)
    if not normalized_phrase:
        return True

    if " " in normalized_phrase:
        phrase_parts = normalized_phrase.split()
        position = -1
        title_parts = normalized_title.split()
        for part in phrase_parts:
            try:
                next_position = title_parts.index(part, position + 1)
            except ValueError:
                return False
            position = next_position

        first_part = phrase_parts[0]
        last_part = phrase_parts[-1]
        if first_part == last_part:
            return True

        window = title_parts[title_parts.index(first_part): position + 1]
        blocked_middle_terms = {"no", "without", "missing"}
        if any(term in blocked_middle_terms for term in window[1:-1]):
            return False
        return True

    phrase_words = {
        word for word in _normalize_words(phrase)
        if len(word) > 1 and word not in {"for", "the", "and", "with", "new", "used"}
    }
    if not phrase_words:
        return True

    matches = 0
    for word in phrase_words:
        if _token_matches(word, title_words, title_stems):
            matches += 1
    return matches >= _required_match_threshold(phrase_words)


def is_relevant_listing(query: str, title: str, filter_text: str = "") -> bool:
    normalized_title = _normalize_phrase(title)
    query_words = set(_normalize_words(query))
    required_filter_phrases, excluded_filter_phrases = _parse_filter_text(filter_text)
    required_filter_words = set(_normalize_words(" ".join(required_filter_phrases)))
    combined_query_words = query_words | required_filter_words
    title_words = set(_normalize_words(title))
    title_stems = {_stem_word(word) for word in title_words}

    significant_query_words = {
        word for word in combined_query_words
        if len(word) > 1 and word not in {"for", "the", "and", "with", "only", "new", "used"}
    }

    matched_words = 0
    for word in significant_query_words:
        if _token_matches(word, title_words, title_stems):
            matched_words += 1

    required_matches = _required_match_threshold(significant_query_words)
    if required_matches == 0:
        return True
    if matched_words < required_matches:
        return False

    for phrase in required_filter_phrases:
        if not _required_phrase_matches(phrase, normalized_title, title_words, title_stems):
            return False

    for phrase in excluded_filter_phrases:
        if phrase and _normalize_phrase(phrase) in normalized_title:
            return False

    generic_accessory_terms = (
        "case",
        "manual",
        "box only",
        "cover only",
        "replacement",
        "empty box",
        "no game",
    )
    normalized_filter = _normalize_phrase(filter_text)
    if "only" in required_filter_words:
        for term in generic_accessory_terms:
            if term in normalized_title and term not in normalized_filter:
                return False

    if "only" in combined_query_words and "only" not in title_words and "loose" not in title_words:
        return False

    return True


def is_uk_only_listing(location_text: str, full_text: str, marketplace: str) -> bool:
    if marketplace != "www.ebay.co.uk":
        return True

    normalized_location = clean_text(location_text).lower()
    normalized_full_text = clean_text(full_text).lower()
    uk_markers = (
        "from united kingdom",
        "from uk",
        "from great britain",
        "from england",
        "from scotland",
        "from wales",
        "from northern ireland",
    )

    if normalized_location:
        if normalized_location.startswith("from "):
            return any(marker in normalized_location for marker in uk_markers)
        return True

    location_match = re.search(r"\bfrom\s+([a-z][a-z .'-]+)", normalized_full_text)
    if location_match:
        location_phrase = f"from {location_match.group(1).strip()}"
        if any(marker in location_phrase for marker in uk_markers):
            return True
        return False

    return True


def build_search_url(query: str, ebay_domain: str, filter_text: str = "") -> str:
    search_terms = " ".join(part for part in [clean_text(query), clean_text(filter_text)] if part)
    return (
        f"https://{ebay_domain}/sch/i.html"
        f"?_nkw={quote_plus(search_terms)}"
        f"&_sacat=0"
        f"&_from=R40"
        f"&rt=nc"
        f"&LH_Complete=1"
        f"&LH_Sold=1"
    )


def _normalize_domain(ebay_domain: str) -> str:
    ebay_domain = (ebay_domain or "www.ebay.co.uk").strip()
    if ebay_domain not in {"www.ebay.co.uk", "www.ebay.com"}:
        return "www.ebay.co.uk"
    return ebay_domain


def scrape_ebay_sold(query: str, limit: int = 20, ebay_domain: str = "www.ebay.co.uk", filter_text: str = "") -> dict:
    query = clean_text(query)
    filter_text = clean_text(filter_text)
    limit = max(1, min(int(limit), 50))
    ebay_domain = _normalize_domain(ebay_domain)
    search_url = build_search_url(query, ebay_domain, filter_text)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir="ebay_browser_profile",
            headless=False,
            viewport={"width": 1400, "height": 1100},
            user_agent=USER_AGENT,
            locale="en-GB",
        )

        page = context.new_page()
        page.set_default_timeout(60000)
        page.goto(search_url, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        final_url = page.url
        page_title = page.title()

        html = page.content()
        with open("debug_playwright_response.html", "w", encoding="utf-8") as f:
            f.write(html)

        if "splashui/challenge" in final_url or "challenge" in final_url.lower():
            context.close()
            raise EbayChallengeError(
                "eBay showed a challenge page. A browser window opened so you can complete it once. "
                "After completing the challenge, run the search again."
            )

        try:
            page.locator("li.s-card").first.wait_for(state="visible", timeout=20000)
        except PlaywrightTimeoutError:
            pass

        page.mouse.wheel(0, 3000)
        page.wait_for_timeout(1500)

        raw_items = page.eval_on_selector_all(
            "li.s-card",
            """
            cards => cards.map(card => {
                const fullText = card.textContent ? card.textContent.trim() : "";
                const titleEl =
                  card.querySelector(".s-card__title .su-styled-text") ||
                  card.querySelector(".s-card__title span") ||
                  card.querySelector(".s-card__title");
                const priceEl =
                  card.querySelector(".s-card__price") ||
                  card.querySelector(".su-styled-text.s-card__price");
                const linkEl =
                  Array.from(card.querySelectorAll("a.s-card__link[href], a[href]"))
                    .find(el => el.href && /\\/itm\\//.test(el.href)) ||
                  card.querySelector("a.s-card__link[href]") ||
                  card.querySelector("a[href]");
                const imageEl = card.querySelector(".s-card__image");
                const subtitleEl =
                  card.querySelector(".s-card__subtitle .su-styled-text") ||
                  card.querySelector(".s-card__subtitle span") ||
                  card.querySelector(".s-card__subtitle");
                const soldDateEl =
                  card.querySelector(".s-card__caption [aria-label*='Sold item']") ||
                  card.querySelector(".s-card__caption .su-styled-text") ||
                  card.querySelector(".s-card__caption");
                const shippingEl = Array.from(card.querySelectorAll(".s-card__attribute-row .su-styled-text, .s-card__attribute-row span"))
                  .find(el => el.textContent && /(delivery|postage|shipping)/i.test(el.textContent));
                const locationEl = Array.from(card.querySelectorAll(".s-card__attribute-row .su-styled-text, .s-card__attribute-row span"))
                  .find(el => el.textContent && /^from\\s+/i.test(el.textContent.trim()));
                const soldFlag = /\\bsold\\b/i.test(fullText) || (soldDateEl && /\\bsold\\b/i.test(soldDateEl.textContent || ""));

                return {
                    title: titleEl ? titleEl.textContent.trim() : "",
                    price_text: priceEl ? priceEl.textContent.trim() : "",
                    url: linkEl ? linkEl.href : "",
                    image_url: imageEl ? (imageEl.src || imageEl.getAttribute("data-src") || "") : "",
                    condition: subtitleEl ? subtitleEl.textContent.trim() : "",
                    sold_date: soldDateEl ? soldDateEl.textContent.trim() : "",
                    shipping_text: shippingEl ? shippingEl.textContent.trim() : "",
                    location_text: locationEl ? locationEl.textContent.trim() : "",
                    is_sold: Boolean(soldFlag),
                    full_text: fullText
                };
            })
            """
        )

        context.close()

    items = []
    seen_urls = set()

    for item in raw_items:
        title = clean_text(item.get("title"))
        price_text = clean_text(item.get("price_text"))
        item_url = clean_text(item.get("url"))
        image_url = clean_text(item.get("image_url"))
        condition = clean_text(item.get("condition"))
        sold_date = clean_text(item.get("sold_date"))
        shipping_text = clean_text(item.get("shipping_text"))
        location_text = clean_text(item.get("location_text"))
        is_sold = bool(item.get("is_sold"))
        full_text = clean_text(item.get("full_text"))

        if not title or not price_text or not item_url:
            continue
        if item_url in seen_urls:
            continue
        if title.lower() == "shop on ebay":
            continue
        if not is_sold and "sold" not in sold_date.lower():
            continue
        if not is_relevant_listing(query, title, filter_text):
            continue
        if not is_uk_only_listing(location_text, full_text, ebay_domain):
            continue

        price_value = parse_price(price_text)
        if price_value is None:
            continue

        seen_urls.add(item_url)
        items.append(
            {
                "title": title,
                "price_text": price_text,
                "price_value": price_value,
                "listing_id": extract_listing_id(item_url),
                "marketplace": ebay_domain,
                "search_query": query,
                "filter_query": filter_text,
                "image_url": image_url,
                "description": sold_date or condition,
                "condition": condition,
                "sold_date": sold_date,
                "shipping_text": shipping_text,
                "location_text": location_text,
                "url": item_url,
            }
        )
        if len(items) >= limit:
            break

    prices = [item["price_value"] for item in items]

    return {
        "query": query,
        "filter_query": filter_text,
        "effective_query": " ".join(part for part in [query, filter_text] if part),
        "count": len(items),
        "average_price": round(mean(prices), 2) if prices else None,
        "lowest_price": round(min(prices), 2) if prices else None,
        "highest_price": round(max(prices), 2) if prices else None,
        "items": items,
        "search_url": search_url,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "debug": {
            "final_url": final_url,
            "page_title": page_title,
            "cards_found": len(raw_items),
            "items_after_filtering": len(items),
        },
    }
