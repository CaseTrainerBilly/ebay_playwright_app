from __future__ import annotations

import csv
from io import StringIO
from statistics import mean, median, pstdev


PACKAGING_COST = 0.20
PROMOTED_LISTING_COST = 0.30
RISK_BUFFER_COST = 0.50
BUY_RATIO_CAP = 0.55

UK_PRIVATE_SELLER_FEE_RATE = 0.0
UK_PRIVATE_SELLER_FIXED_FEE = 0.0
DEFAULT_BUSINESS_FEE_RATE = 0.13
DEFAULT_BUSINESS_FIXED_FEE = 0.30


def _money(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}"


def _percent(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value * 100:.0f}%"


def estimate_uk_buyer_protection_fee_from_item_price(item_price: float) -> float:
    remaining = max(item_price, 0.0)
    fee = 0.10

    tier = min(remaining, 20.0)
    fee += tier * 0.07
    remaining -= tier

    if remaining > 0:
        tier = min(remaining, 280.0)
        fee += tier * 0.04
        remaining -= tier

    if remaining > 0:
        tier = min(remaining, 3700.0)
        fee += tier * 0.02

    return round(fee, 2)


def estimate_uk_private_seller_payout_from_buyer_total(buyer_total: float | None) -> float | None:
    if buyer_total is None:
        return None

    total = max(float(buyer_total), 0.0)
    if total <= 21.50:
        item_price = (total - 0.10) / 1.07
    elif total <= 312.70:
        item_price = (total + 0.50) / 1.04
    elif total <= 4086.70:
        item_price = (total + 5.50) / 1.02
    else:
        item_price = total - 86.70

    return round(max(item_price, 0.0), 2)


def _fee_model(marketplace: str | None) -> tuple[float, float]:
    if marketplace == "www.ebay.co.uk":
        return (UK_PRIVATE_SELLER_FEE_RATE, UK_PRIVATE_SELLER_FIXED_FEE)
    return (DEFAULT_BUSINESS_FEE_RATE, DEFAULT_BUSINESS_FIXED_FEE)


def estimate_ebay_fee(sold_price: float | None, marketplace: str | None) -> float | None:
    if sold_price is None:
        return None
    fee_rate, fixed_fee = _fee_model(marketplace)
    return round((sold_price * fee_rate) + fixed_fee, 2)


def estimate_buyer_protection_fee(sold_price: float | None, marketplace: str | None) -> float | None:
    if sold_price is None:
        return None
    if marketplace == "www.ebay.co.uk":
        seller_receives = estimate_uk_private_seller_payout_from_buyer_total(sold_price)
        if seller_receives is None:
            return None
        return round(max(sold_price - seller_receives, 0), 2)
    return None


def estimate_seller_receives(sold_price: float | None, marketplace: str | None) -> float | None:
    if sold_price is None:
        return None
    if marketplace == "www.ebay.co.uk":
        return estimate_uk_private_seller_payout_from_buyer_total(sold_price)
    fee = estimate_ebay_fee(sold_price, marketplace)
    return round(sold_price - fee, 2) if fee is not None else None


def _target_profit(expected_sale_price: float) -> float:
    if expected_sale_price < 10:
        return 2.0
    if expected_sale_price < 20:
        return 4.0
    return 6.0


def _remove_outliers(values: list[float]) -> list[float]:
    if len(values) < 4:
        return values[:]

    sorted_values = sorted(values)
    lower_half = sorted_values[: len(sorted_values) // 2]
    upper_half = sorted_values[(len(sorted_values) + 1) // 2 :]
    q1 = median(lower_half)
    q3 = median(upper_half)
    iqr = q3 - q1
    low = q1 - (1.5 * iqr)
    high = q3 + (1.5 * iqr)
    filtered = [value for value in sorted_values if low <= value <= high]
    return filtered or sorted_values


def _sell_through_confidence(count: int, spread_ratio: float | None) -> str:
    if count >= 12 and spread_ratio is not None and spread_ratio <= 0.20:
        return "High"
    if count >= 8 and spread_ratio is not None and spread_ratio <= 0.35:
        return "Medium"
    return "Low"


def calculate_resale_metrics(results: dict) -> dict:
    items = results.get("items", [])
    if not items:
        return {}

    marketplace = items[0].get("marketplace")
    seller_prices = [
        value for value in
        (estimate_seller_receives(item.get("price_value"), marketplace) for item in items)
        if value is not None
    ]
    if not seller_prices:
        return {}

    filtered_prices = _remove_outliers(seller_prices)
    expected_sale_price = round(median(filtered_prices), 2)
    average_sale_price = round(mean(filtered_prices), 2)
    lowest_sale_price = round(min(filtered_prices), 2)
    highest_sale_price = round(max(filtered_prices), 2)
    spread = round(pstdev(filtered_prices), 2) if len(filtered_prices) > 1 else 0.0
    spread_ratio = round(spread / expected_sale_price, 4) if expected_sale_price else None

    total_costs = round(PACKAGING_COST + PROMOTED_LISTING_COST + RISK_BUFFER_COST, 2)
    target_profit = _target_profit(expected_sale_price)
    raw_max_buy = max(expected_sale_price - total_costs - target_profit, 0)
    capped_max_buy = expected_sale_price * BUY_RATIO_CAP
    max_buy_price = round(max(min(raw_max_buy, capped_max_buy), 0), 2)
    expected_profit = round(expected_sale_price - max_buy_price - total_costs, 2)
    roi = round(expected_profit / max_buy_price, 4) if max_buy_price > 0 else None

    observed_prices = [item.get("price_value") for item in items if item.get("price_value") is not None]
    average_observed_price = round(mean(observed_prices), 2) if observed_prices else None
    buyer_protection_values = [
        value for value in
        (estimate_buyer_protection_fee(item.get("price_value"), marketplace) for item in items)
        if value is not None
    ]
    average_buyer_protection = round(mean(buyer_protection_values), 2) if buyer_protection_values else None

    return {
        "average_observed_sold_price": average_observed_price,
        "average_buyer_protection_fee": average_buyer_protection,
        "median_estimated_sale_price": expected_sale_price,
        "average_estimated_sale_price": average_sale_price,
        "lowest_estimated_sale_price": lowest_sale_price,
        "highest_estimated_sale_price": highest_sale_price,
        "price_spread": spread,
        "sell_through_confidence": _sell_through_confidence(len(filtered_prices), spread_ratio),
        "total_costs": total_costs,
        "target_profit": target_profit,
        "recommended_max_buy_price": max_buy_price,
        "expected_profit_at_max_buy": expected_profit,
        "roi_at_max_buy": roi,
        "buy_ratio_cap": BUY_RATIO_CAP,
    }


def build_csv(results: dict) -> str:
    output = StringIO()
    writer = csv.writer(output)
    resale_metrics = calculate_resale_metrics(results)

    writer.writerow(
        [
            "title",
            "price_text",
            "observed_sold_price",
            "estimated_buyer_protection_fee",
            "estimated_seller_receives",
            "recommended_max_buy_price",
            "expected_profit_at_max_buy",
            "roi_at_max_buy",
            "image_url",
            "description",
            "condition",
            "sold_date",
            "shipping_text",
            "location_text",
            "listing_id",
            "marketplace",
            "search_query",
            "url",
        ]
    )

    for item in results.get("items", []):
        sold_price = item.get("price_value")
        marketplace = item.get("marketplace")
        writer.writerow(
            [
                item.get("title", ""),
                item.get("price_text", ""),
                _money(sold_price),
                _money(estimate_buyer_protection_fee(sold_price, marketplace)),
                _money(estimate_seller_receives(sold_price, marketplace)),
                "",
                "",
                "",
                item.get("image_url", ""),
                item.get("description", ""),
                item.get("condition", ""),
                item.get("sold_date", ""),
                item.get("shipping_text", ""),
                item.get("location_text", ""),
                item.get("listing_id", ""),
                item.get("marketplace", ""),
                item.get("search_query", ""),
                item.get("url", ""),
            ]
        )

    writer.writerow(
        [
            "AVERAGE",
            "",
            _money(resale_metrics.get("average_observed_sold_price")),
            _money(resale_metrics.get("average_buyer_protection_fee")),
            _money(resale_metrics.get("average_estimated_sale_price")),
            _money(resale_metrics.get("recommended_max_buy_price")),
            _money(resale_metrics.get("expected_profit_at_max_buy")),
            _percent(resale_metrics.get("roi_at_max_buy")),
            "",
            f"Median sale price {_money(resale_metrics.get('median_estimated_sale_price'))} | Confidence {resale_metrics.get('sell_through_confidence', '')}",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ]
    )

    return output.getvalue()
