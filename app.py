from __future__ import annotations

from flask import Flask, jsonify, render_template, request, send_file
import os
import re
import tempfile
import uuid

from csv_export import calculate_resale_metrics, estimate_buyer_protection_fee, estimate_seller_receives
from scraper import EbayChallengeError, scrape_ebay_sold
from xlsx_export import build_xlsx

app = Flask(__name__)
RECENT_RESULTS: dict[str, dict] = {}


def store_results(results: dict) -> str:
    token = uuid.uuid4().hex
    RECENT_RESULTS[token] = results
    if len(RECENT_RESULTS) > 20:
        oldest_token = next(iter(RECENT_RESULTS))
        RECENT_RESULTS.pop(oldest_token, None)
    return token


@app.route("/", methods=["GET"])
def home():
    return render_template(
        "index.html",
        results=None,
        results_token=None,
        error=None,
        query="",
        domain="www.ebay.co.uk",
        limit=40,
    )


@app.route("/search", methods=["POST"])
def search():
    query = request.form.get("query", "").strip()
    domain = request.form.get("domain", "www.ebay.co.uk").strip()

    try:
        limit = max(1, min(int(request.form.get("limit", 40)), 50))
    except ValueError:
        limit = 40

    if not query:
        return render_template(
            "index.html",
            results=None,
            results_token=None,
            error="Please enter a search term.",
            query=query,
            domain=domain,
            limit=limit,
        )

    try:
        results = scrape_ebay_sold(query=query, limit=limit, ebay_domain=domain)
        results_token = store_results(results)
        return render_template(
            "index.html",
            results=results,
            results_token=results_token,
            error=None,
            query=query,
            domain=domain,
            limit=limit,
        )
    except EbayChallengeError as exc:
        return render_template(
            "index.html",
            results=None,
            results_token=None,
            error=str(exc),
            query=query,
            domain=domain,
            limit=limit,
        )
    except Exception as exc:
        return render_template(
            "index.html",
            results=None,
            results_token=None,
            error=f"Failed to fetch eBay results: {exc}",
            query=query,
            domain=domain,
            limit=limit,
        )


@app.route("/export-xlsx", methods=["GET"])
def export_xlsx():
    token = request.args.get("token", "").strip()
    if not token:
        return "Missing results token.", 400

    results = RECENT_RESULTS.get(token)
    if not results:
        return "These cached results expired. Please run the search again.", 404

    workbook_content = build_xlsx(results)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    temp_file.write(workbook_content)
    temp_file.close()

    query = results.get("query", "")
    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", query).strip("_") or "ebay_results"
    return send_file(
        temp_file.name,
        as_attachment=True,
        download_name=f"{safe_name}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/api/search", methods=["GET"])
def api_search():
    query = request.args.get("query", "").strip()
    domain = request.args.get("domain", "www.ebay.co.uk").strip()

    try:
        limit = max(1, min(int(request.args.get("limit", 40)), 50))
    except ValueError:
        limit = 40

    if not query:
        return jsonify({"error": "Missing query parameter."}), 400

    try:
        results = scrape_ebay_sold(query=query, limit=limit, ebay_domain=domain)
        return jsonify(results)
    except EbayChallengeError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/item", methods=["GET"])
def item_detail():
    query = request.args.get("query", "").strip()
    token = request.args.get("token", "").strip()

    try:
        index = int(request.args.get("index", "0"))
    except ValueError:
        index = -1

    if not token:
        return render_template(
            "item.html",
            item=None,
            error="Missing results token. Please open item details from the current search results.",
            query=query,
            index=index,
        ), 400

    results = RECENT_RESULTS.get(token)
    if not results:
        return render_template(
            "item.html",
            item=None,
            error="These cached results expired. Please run the search again.",
            query=query,
            index=index,
        ), 404

    query = results.get("query", query)

    if index < 0 or index >= len(results["items"]):
        return render_template(
            "item.html",
            item=None,
            error="That item could not be found in the current results.",
            query=query,
            index=index,
        ), 404

    return render_template(
        "item.html",
        item=results["items"][index],
        item_buyer_protection_fee=estimate_buyer_protection_fee(results["items"][index].get("price_value"), results["items"][index].get("marketplace")),
        item_seller_receives=estimate_seller_receives(results["items"][index].get("price_value"), results["items"][index].get("marketplace")),
        market_metrics=calculate_resale_metrics(results),
        token=token,
        error=None,
        query=query,
        index=index,
    )


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "5001"))
    app.run(debug=True, host=host, port=port)
