const svgPlaceholder = (label, hue) =>
  `data:image/svg+xml;utf8,${encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 480">
      <defs>
        <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="${hue}"/>
          <stop offset="100%" stop-color="#ffffff"/>
        </linearGradient>
      </defs>
      <rect width="640" height="480" fill="url(#g)"/>
      <rect x="70" y="70" width="500" height="340" rx="28" fill="#ffffff" fill-opacity="0.82"/>
      <text x="320" y="220" text-anchor="middle" font-size="28" font-family="Arial, Helvetica, sans-serif" fill="#111820">${label}</text>
      <text x="320" y="270" text-anchor="middle" font-size="18" font-family="Arial, Helvetica, sans-serif" fill="#5c5f62">Demo listing image</text>
    </svg>`
  )}`;

const DEMO_CATALOG = {
  "pokemon black ds cartridge only": {
    query: "pokemon black ds cartridge only",
    domain: "www.ebay.co.uk",
    items: [
      {
        title: "Pokemon Black Nintendo DS Cartridge Only Tested Working",
        price_text: "£39.99",
        price_value: 39.99,
        url: "https://www.ebay.co.uk/",
        image_url: svgPlaceholder("Pokemon Black", "#ffd66b"),
        description: "Loose cartridge sale with tested status and a clean front label.",
        condition: "Good",
        sold_date: "14 Mar 2026",
        shipping_text: "Free postage",
        location_text: "Leeds, United Kingdom",
        listing_id: "156000001001",
        marketplace: "www.ebay.co.uk",
        search_query: "pokemon black ds cartridge only"
      },
      {
        title: "Pokemon Black Version DS Game Cart Genuine PAL",
        price_text: "£42.50",
        price_value: 42.5,
        url: "https://www.ebay.co.uk/",
        image_url: svgPlaceholder("PAL Cartridge", "#a7d8ff"),
        description: "Genuine PAL cartridge with light wear and no case.",
        condition: "Very Good",
        sold_date: "13 Mar 2026",
        shipping_text: "£2.70 postage",
        location_text: "Bristol, United Kingdom",
        listing_id: "156000001002",
        marketplace: "www.ebay.co.uk",
        search_query: "pokemon black ds cartridge only"
      },
      {
        title: "Pokemon Black DS Cartridge Authentic Cart Only",
        price_text: "£36.00",
        price_value: 36.0,
        url: "https://www.ebay.co.uk/",
        image_url: svgPlaceholder("Authentic Cart", "#d2f2a1"),
        description: "Lower-end comp with visible label wear and quick sale timing.",
        condition: "Acceptable",
        sold_date: "11 Mar 2026",
        shipping_text: "Free postage",
        location_text: "Glasgow, United Kingdom",
        listing_id: "156000001003",
        marketplace: "www.ebay.co.uk",
        search_query: "pokemon black ds cartridge only"
      },
      {
        title: "Pokemon Black DS Loose Cartridge Genuine Nintendo",
        price_text: "£44.99",
        price_value: 44.99,
        url: "https://www.ebay.co.uk/",
        image_url: svgPlaceholder("Loose Genuine", "#ffc1cc"),
        description: "Higher-end comp with sharper label condition and stronger imagery.",
        condition: "Excellent",
        sold_date: "10 Mar 2026",
        shipping_text: "£1.99 postage",
        location_text: "Manchester, United Kingdom",
        listing_id: "156000001004",
        marketplace: "www.ebay.co.uk",
        search_query: "pokemon black ds cartridge only"
      }
    ]
  },
  "steam deck 256gb": {
    query: "steam deck 256gb",
    domain: "www.ebay.com",
    items: [
      {
        title: "Valve Steam Deck 256GB Handheld Console with Case",
        price_text: "$319.00",
        price_value: 319.0,
        url: "https://www.ebay.com/",
        image_url: svgPlaceholder("Steam Deck", "#b8c6ff"),
        description: "Complete handheld with case and charger, lightly used.",
        condition: "Used",
        sold_date: "15 Mar 2026",
        shipping_text: "Free shipping",
        location_text: "Austin, Texas, United States",
        listing_id: "256000001001",
        marketplace: "www.ebay.com",
        search_query: "steam deck 256gb"
      },
      {
        title: "Steam Deck 256GB Console Tested and Reset",
        price_text: "$305.00",
        price_value: 305.0,
        url: "https://www.ebay.com/",
        image_url: svgPlaceholder("256GB Console", "#ffddb0"),
        description: "Mid-range comp with standard accessories and visible wear.",
        condition: "Good",
        sold_date: "13 Mar 2026",
        shipping_text: "$9.99 shipping",
        location_text: "Denver, Colorado, United States",
        listing_id: "256000001002",
        marketplace: "www.ebay.com",
        search_query: "steam deck 256gb"
      },
      {
        title: "Valve Steam Deck 256GB Portable Gaming System",
        price_text: "$289.99",
        price_value: 289.99,
        url: "https://www.ebay.com/",
        image_url: svgPlaceholder("Portable Gaming", "#c6f0d1"),
        description: "Softer comp that helps illustrate spread and margin sensitivity.",
        condition: "Fair",
        sold_date: "09 Mar 2026",
        shipping_text: "Free shipping",
        location_text: "Phoenix, Arizona, United States",
        listing_id: "256000001003",
        marketplace: "www.ebay.com",
        search_query: "steam deck 256gb"
      }
    ]
  }
};

const DEFAULT_KEY = "pokemon black ds cartridge only";
const STORAGE_KEY = "ebay-pages-demo-results";

function estimateBuyerProtectionFee(soldPrice, marketplace) {
  if (soldPrice == null || marketplace !== "www.ebay.co.uk") {
    return null;
  }
  return roundMoney(Math.max(soldPrice - estimateSellerReceives(soldPrice, marketplace), 0));
}

function estimateSellerReceives(soldPrice, marketplace) {
  if (soldPrice == null) {
    return null;
  }

  if (marketplace === "www.ebay.co.uk") {
    const total = Math.max(Number(soldPrice), 0);
    let itemPrice;
    if (total <= 21.5) {
      itemPrice = (total - 0.1) / 1.07;
    } else if (total <= 312.7) {
      itemPrice = (total + 0.5) / 1.04;
    } else if (total <= 4086.7) {
      itemPrice = (total + 5.5) / 1.02;
    } else {
      itemPrice = total - 86.7;
    }
    return roundMoney(Math.max(itemPrice, 0));
  }

  return roundMoney(soldPrice - ((soldPrice * 0.13) + 0.3));
}

function calculateMetrics(results) {
  const items = results.items || [];
  if (!items.length) {
    return {};
  }

  const sellerPrices = items
    .map((item) => estimateSellerReceives(item.price_value, item.marketplace))
    .filter((value) => value != null);

  if (!sellerPrices.length) {
    return {};
  }

  const filtered = removeOutliers(sellerPrices);
  const expectedSale = median(filtered);
  const averageSale = average(filtered);
  const lowestSale = Math.min(...filtered);
  const highestSale = Math.max(...filtered);
  const spread = filtered.length > 1 ? populationStdDev(filtered) : 0;
  const spreadRatio = expectedSale ? spread / expectedSale : null;
  const totalCosts = 1.0;
  const targetProfit = expectedSale < 10 ? 2 : expectedSale < 20 ? 4 : 6;
  const rawMaxBuy = Math.max(expectedSale - totalCosts - targetProfit, 0);
  const buyRatioCap = 0.55;
  const maxBuy = Math.max(Math.min(rawMaxBuy, expectedSale * buyRatioCap), 0);
  const expectedProfit = expectedSale - maxBuy - totalCosts;
  const roi = maxBuy > 0 ? expectedProfit / maxBuy : null;

  return {
    median_estimated_sale_price: roundMoney(expectedSale),
    average_estimated_sale_price: roundMoney(averageSale),
    lowest_estimated_sale_price: roundMoney(lowestSale),
    highest_estimated_sale_price: roundMoney(highestSale),
    price_spread: roundMoney(spread),
    sell_through_confidence: getConfidence(filtered.length, spreadRatio),
    total_costs: totalCosts,
    target_profit: targetProfit,
    recommended_max_buy_price: roundMoney(maxBuy),
    expected_profit_at_max_buy: roundMoney(expectedProfit),
    roi_at_max_buy: roi,
    buy_ratio_cap: buyRatioCap
  };
}

function removeOutliers(values) {
  if (values.length < 4) {
    return [...values];
  }
  const sorted = [...values].sort((a, b) => a - b);
  const lowerHalf = sorted.slice(0, Math.floor(sorted.length / 2));
  const upperHalf = sorted.slice(Math.ceil(sorted.length / 2));
  const q1 = median(lowerHalf);
  const q3 = median(upperHalf);
  const iqr = q3 - q1;
  const low = q1 - (1.5 * iqr);
  const high = q3 + (1.5 * iqr);
  const filtered = sorted.filter((value) => value >= low && value <= high);
  return filtered.length ? filtered : sorted;
}

function getConfidence(count, spreadRatio) {
  if (count >= 12 && spreadRatio != null && spreadRatio <= 0.2) {
    return "High";
  }
  if (count >= 8 && spreadRatio != null && spreadRatio <= 0.35) {
    return "Medium";
  }
  return "Low";
}

function roundMoney(value) {
  return Math.round(value * 100) / 100;
}

function average(values) {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 0) {
    return (sorted[mid - 1] + sorted[mid]) / 2;
  }
  return sorted[mid];
}

function populationStdDev(values) {
  const mean = average(values);
  const variance = average(values.map((value) => (value - mean) ** 2));
  return Math.sqrt(variance);
}

function getCurrencySymbol(domain) {
  return domain === "www.ebay.com" ? "$" : "£";
}

function buildResults(query, domain, limit) {
  const normalized = query.trim().toLowerCase();
  const fallbackKey = domain === "www.ebay.com" ? "steam deck 256gb" : DEFAULT_KEY;
  const catalogEntry = DEMO_CATALOG[normalized] || DEMO_CATALOG[fallbackKey];
  const items = catalogEntry.items.slice(0, Math.max(1, Math.min(limit, 50)));
  const priceValues = items.map((item) => item.price_value).filter((value) => value != null);

  return {
    query: query.trim() || catalogEntry.query,
    count: items.length,
    average_price: priceValues.length ? roundMoney(average(priceValues)) : null,
    lowest_price: priceValues.length ? roundMoney(Math.min(...priceValues)) : null,
    highest_price: priceValues.length ? roundMoney(Math.max(...priceValues)) : null,
    items,
    debug: {
      final_url: `https://${domain}/sch/i.html?_nkw=${encodeURIComponent(query.trim() || catalogEntry.query)}&LH_Sold=1&LH_Complete=1`,
      page_title: `${catalogEntry.query} sold listings`,
      cards_found: items.length + 2,
      items_after_filtering: items.length
    }
  };
}

function saveResults(results) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(results));
}

function loadSavedResults() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch (error) {
    return null;
  }
}

function formatMoney(value, domain) {
  if (value == null) {
    return "N/A";
  }
  return `${getCurrencySymbol(domain)}${Number(value).toFixed(2)}`;
}

function renderIndexPage() {
  const form = document.getElementById("demo-search-form");
  if (!form) {
    return;
  }

  const queryInput = document.getElementById("query");
  const domainInput = document.getElementById("domain");
  const limitInput = document.getElementById("limit");

  function updatePage(results) {
    saveResults(results);
    renderStats(results);
    renderDebug(results);
    renderItems(results);
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const results = buildResults(queryInput.value, domainInput.value, Number(limitInput.value || 8));
    updatePage(results);
  });

  const initialResults = loadSavedResults() || buildResults(queryInput.value, domainInput.value, Number(limitInput.value || 8));
  queryInput.value = initialResults.query;
  domainInput.value = initialResults.items[0]?.marketplace || "www.ebay.co.uk";
  limitInput.value = initialResults.items.length;
  updatePage(initialResults);
}

function renderStats(results) {
  const stats = document.getElementById("stats");
  const domain = results.items[0]?.marketplace || "www.ebay.co.uk";
  stats.innerHTML = `
    <div class="stat-card"><strong>Query</strong><br>${results.query}</div>
    <div class="stat-card"><strong>Items Found</strong><br>${results.count}</div>
    <div class="stat-card"><strong>Average Price</strong><br>${formatMoney(results.average_price, domain)}</div>
    <div class="stat-card"><strong>Lowest Price</strong><br>${formatMoney(results.lowest_price, domain)}</div>
    <div class="stat-card"><strong>Highest Price</strong><br>${formatMoney(results.highest_price, domain)}</div>
  `;
}

function renderDebug(results) {
  const debugBox = document.getElementById("debug-box");
  debugBox.innerHTML = `
    <strong>Debug</strong><br>
    Final URL: ${results.debug.final_url}<br>
    Page title: ${results.debug.page_title}<br>
    Cards found: ${results.debug.cards_found}<br>
    Items after filtering: ${results.debug.items_after_filtering}
  `;
}

function renderItems(results) {
  const itemsRoot = document.getElementById("items");
  itemsRoot.innerHTML = "";

  if (!results.items.length) {
    itemsRoot.innerHTML = `<div class="empty-state">No demo items are available for this search.</div>`;
    return;
  }

  results.items.forEach((item, index) => {
    const card = document.createElement("div");
    card.className = "item";
    card.innerHTML = `
      <div class="item-media">
        <img src="${item.image_url}" alt="${escapeHtml(item.title)}">
      </div>
      <div class="item-content">
        <div class="item-topline">
          <span class="item-index">Result ${index + 1}</span>
          <span class="item-price">${item.price_text}</span>
        </div>
        <h3>${escapeHtml(item.title)}</h3>
        <div class="listing-strip">
          <span class="listing-pill">Sold Listing</span>
          <span class="listing-pill listing-pill-soft">${item.marketplace}</span>
          <span class="listing-pill listing-pill-soft">${item.sold_date || "Date unavailable"}</span>
        </div>
        <div class="item-meta-grid">
          <div class="meta-chip">
            <span class="meta-label">Condition</span>
            <span class="meta-value">${escapeHtml(item.condition || "N/A")}</span>
          </div>
          <div class="meta-chip">
            <span class="meta-label">Sold Date</span>
            <span class="meta-value">${escapeHtml(item.sold_date || "N/A")}</span>
          </div>
          <div class="meta-chip">
            <span class="meta-label">Shipping</span>
            <span class="meta-value">${escapeHtml(item.shipping_text || "N/A")}</span>
          </div>
          <div class="meta-chip">
            <span class="meta-label">Location</span>
            <span class="meta-value">${escapeHtml(item.location_text || "N/A")}</span>
          </div>
          <div class="meta-chip">
            <span class="meta-label">Listing ID</span>
            <span class="meta-value">${escapeHtml(item.listing_id || "N/A")}</span>
          </div>
          <div class="meta-chip">
            <span class="meta-label">Marketplace</span>
            <span class="meta-value">${escapeHtml(item.marketplace)}</span>
          </div>
          <div class="meta-chip">
            <span class="meta-label">Numeric Price</span>
            <span class="meta-value">${Number(item.price_value).toFixed(2)}</span>
          </div>
        </div>
        <p class="item-description"><strong>Quick summary:</strong> ${escapeHtml(item.description || "No extra summary available.")}</p>
        <div class="item-actions">
          <a class="link-btn secondary-btn" href="item.html?index=${index}">View Details</a>
          <a class="link-btn" href="${item.url}" target="_blank" rel="noopener noreferrer">Open eBay Listing</a>
        </div>
      </div>
    `;
    itemsRoot.appendChild(card);
  });
}

function renderDetailPage() {
  const detailRoot = document.getElementById("detail-root");
  if (!detailRoot) {
    return;
  }

  const results = loadSavedResults() || buildResults(DEFAULT_KEY, "www.ebay.co.uk", 4);
  const params = new URLSearchParams(window.location.search);
  const index = Number(params.get("index") || 0);
  const item = results.items[index] || results.items[0];
  const metrics = calculateMetrics(results);
  const currency = getCurrencySymbol(item.marketplace);
  const buyerProtection = estimateBuyerProtectionFee(item.price_value, item.marketplace);
  const sellerReceives = estimateSellerReceives(item.price_value, item.marketplace);

  document.getElementById("item-link").href = item.url;

  detailRoot.innerHTML = `
    <div class="detail-layout">
      <div class="detail-image-panel">
        <img class="detail-image" src="${item.image_url}" alt="${escapeHtml(item.title)}">
      </div>
      <div class="detail-content">
        <div class="item-topline">
          <span class="item-index">Result ${results.items.indexOf(item) + 1}</span>
          <span class="item-price">${item.price_text}</span>
        </div>
        <h2>${escapeHtml(item.title)}</h2>
        <div class="listing-strip">
          <span class="listing-pill">Sold Listing</span>
          <span class="listing-pill listing-pill-soft">${item.marketplace}</span>
          <span class="listing-pill listing-pill-soft">${item.sold_date || "Date unavailable"}</span>
        </div>
        <p class="item-description"><strong>Search used:</strong> ${escapeHtml(results.query)}</p>

        <div class="detail-section">
          <div class="section-head">
            <h3>Pricing Snapshot</h3>
            <p class="muted">Use these numbers to quickly compare what the buyer likely paid against what the seller likely kept.</p>
          </div>
          <div class="pricing-grid">
            <div class="price-card primary-price-card">
              <span class="meta-label">Observed Sold Price</span>
              <span class="price-value">${formatMoney(item.price_value, item.marketplace)}</span>
              <span class="supporting-copy">Buyer-facing sold price shown on the listing.</span>
            </div>
            <div class="price-card">
              <span class="meta-label">Estimated Buyer Protection</span>
              <span class="price-value subdued">${formatMoney(buyerProtection, item.marketplace)}</span>
              <span class="supporting-copy">Estimated amount added on top for eligible UK private sales.</span>
            </div>
            <div class="price-card emphasis-card">
              <span class="meta-label">Estimated Seller Receives</span>
              <span class="price-value">${formatMoney(sellerReceives, item.marketplace)}</span>
              <span class="supporting-copy">Useful anchor for judging realistic resale value.</span>
            </div>
          </div>
        </div>

        <div class="detail-grid">
          <div class="detail-card"><span class="meta-label">Condition</span><span class="meta-value">${escapeHtml(item.condition || "N/A")}</span></div>
          <div class="detail-card"><span class="meta-label">Sold Date</span><span class="meta-value">${escapeHtml(item.sold_date || "N/A")}</span></div>
          <div class="detail-card"><span class="meta-label">Shipping</span><span class="meta-value">${escapeHtml(item.shipping_text || "N/A")}</span></div>
          <div class="detail-card"><span class="meta-label">Location</span><span class="meta-value">${escapeHtml(item.location_text || "N/A")}</span></div>
          <div class="detail-card"><span class="meta-label">Listing ID</span><span class="meta-value">${escapeHtml(item.listing_id || "N/A")}</span></div>
          <div class="detail-card"><span class="meta-label">Marketplace</span><span class="meta-value">${escapeHtml(item.marketplace)}</span></div>
          <div class="detail-card"><span class="meta-label">Numeric Price</span><span class="meta-value">${Number(item.price_value).toFixed(2)}</span></div>
        </div>

        <div class="detail-two-column">
          <div class="detail-notes">
            <div class="section-head">
              <h3>Market Read</h3>
              <p class="muted">These values come from the current demo result set on screen, not a fresh scrape.</p>
            </div>
            <div class="market-grid">
              <div class="detail-card"><span class="meta-label">Median Estimated Sale</span><span class="meta-value">${currency}${metrics.median_estimated_sale_price?.toFixed(2) || "0.00"}</span></div>
              <div class="detail-card"><span class="meta-label">Average Estimated Sale</span><span class="meta-value">${currency}${metrics.average_estimated_sale_price?.toFixed(2) || "0.00"}</span></div>
              <div class="detail-card"><span class="meta-label">Recommended Max Buy</span><span class="meta-value">${currency}${metrics.recommended_max_buy_price?.toFixed(2) || "0.00"}</span></div>
              <div class="detail-card"><span class="meta-label">Expected Profit</span><span class="meta-value">${currency}${metrics.expected_profit_at_max_buy?.toFixed(2) || "0.00"}</span></div>
              <div class="detail-card"><span class="meta-label">ROI At Max Buy</span><span class="meta-value">${metrics.roi_at_max_buy != null ? `${Math.round(metrics.roi_at_max_buy * 100)}%` : "N/A"}</span></div>
              <div class="detail-card"><span class="meta-label">Confidence</span><span class="meta-value">${metrics.sell_through_confidence || "N/A"}</span></div>
            </div>
          </div>

          <div class="detail-notes">
            <div class="section-head">
              <h3>Reseller Notes</h3>
              <p class="muted">A compact checklist before buying another copy to flip.</p>
            </div>
            <p><strong>Summary:</strong> ${escapeHtml(item.description || "No extra summary available.")}</p>
            <p><strong>Check condition match:</strong> Make sure your target buy is as clean as this sold example and includes the same extras or omissions.</p>
            <p><strong>Check price realism:</strong> Compare this sale against the market median, not just the top price, before deciding your buy ceiling.</p>
            <p><strong>Check source:</strong> Use the listing ID and original link for image or wording verification when needed.</p>
            <p><strong>Source URL:</strong> <a href="${item.url}" target="_blank" rel="noopener noreferrer">${item.url}</a></p>
          </div>
        </div>

        <div class="detail-notes source-panel">
          <div class="section-head">
            <h3>Market Range</h3>
            <p class="muted">A quick spread view from the current demo sold set.</p>
          </div>
          <div class="market-grid">
            <div class="detail-card"><span class="meta-label">Lowest Estimated Sale</span><span class="meta-value">${currency}${metrics.lowest_estimated_sale_price?.toFixed(2) || "0.00"}</span></div>
            <div class="detail-card"><span class="meta-label">Highest Estimated Sale</span><span class="meta-value">${currency}${metrics.highest_estimated_sale_price?.toFixed(2) || "0.00"}</span></div>
            <div class="detail-card"><span class="meta-label">Price Spread</span><span class="meta-value">${currency}${metrics.price_spread?.toFixed(2) || "0.00"}</span></div>
            <div class="detail-card"><span class="meta-label">Total Cost Assumption</span><span class="meta-value">${currency}${metrics.total_costs?.toFixed(2) || "0.00"}</span></div>
            <div class="detail-card"><span class="meta-label">Target Profit Rule</span><span class="meta-value">${currency}${metrics.target_profit?.toFixed(2) || "0.00"}</span></div>
            <div class="detail-card"><span class="meta-label">Buy Cap Ratio</span><span class="meta-value">${metrics.buy_ratio_cap != null ? `${Math.round(metrics.buy_ratio_cap * 100)}%` : "N/A"}</span></div>
          </div>
        </div>
      </div>
    </div>
  `;
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

renderIndexPage();
renderDetailPage();
