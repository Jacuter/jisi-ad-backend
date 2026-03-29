"""
Browser Bridge — JS Rendering Layer for Shopify Extractor
Jisi × Shopify AI Video Ad System

Uses OpenClaw's Chrome as a JS rendering engine via CLI commands.
Workflow:
1. openclaw browser open <url> → returns "id: <tab_id>"
2. sleep for JS hydration
3. openclaw browser evaluate --target-id <full_id> --fn "<js>"

Key: Use FULL tab ID (not shortened). openclaw returns full 32-char ID.

Prerequisites:
- OpenClaw browser must be running (profile: openclaw)

Usage:
    bridge = BrowserBridge()
    products = bridge.extract_products("https://www.gymshark.com/products/...")
    print(products[0]["name"], products[0]["price"])
"""

import json
import subprocess
import time
import re
from typing import Optional


# ---------------------------------------------------------------------------
# JS Extraction Script
# ---------------------------------------------------------------------------

EXTRACT_PRODUCTS_JS = r"""
(function() {
    var r = [];
    var scripts = document.querySelectorAll('script[type="application/ld+json"]');
    for (var i = 0; i < scripts.length; i++) {
        try {
            var raw = JSON.parse(scripts[i].textContent);
            var items = [];
            if (Array.isArray(raw)) { items = raw; }
            else if (raw && typeof raw === 'object') { items = [raw]; }
            for (var j = 0; j < items.length; j++) {
                var item = items[j];
                if (item && item['@type'] === 'Product') {
                    r.push({
                        name: item.name || null,
                        brand: (item.brand && typeof item.brand === 'object') ? item.brand.name : (typeof item.brand === 'string' ? item.brand : null),
                        price: (item.offers && typeof item.offers === 'object') ? item.offers.price : null,
                        currency: (item.offers && typeof item.offers === 'object') ? item.offers.priceCurrency : null,
                        sku: item.sku || null,
                        description: item.description ? item.description.substring(0, 500) : null,
                        image: Array.isArray(item.image) ? item.image[0] : (item.image || null),
                        images: Array.isArray(item.image) ? item.image.slice(0, 5) : [],
                        ratingValue: item.aggregateRating ? item.aggregateRating.ratingValue : null,
                        reviewCount: item.aggregateRating ? (item.aggregateRating.reviewCount || item.aggregateRating.ratingCount) : null,
                        category: item.category || null,
                        color: item.color || null,
                        tags: item.keywords ? item.keywords.split(',').map(function(k) { return k.trim(); }).slice(0, 10) : []
                    });
                }
            }
        } catch(e) {}
    }
    return JSON.stringify(r);
})()
"""


# ---------------------------------------------------------------------------
# Bridge
# ---------------------------------------------------------------------------

class BrowserBridge:
    """
    Bridge between Python and OpenClaw Chrome browser.
    Uses CLI subprocess — no WebSocket needed.
    """

    JS_EXTRACT = EXTRACT_PRODUCTS_JS.strip()

    def __init__(self, render_wait: int = 4):
        self.render_wait = render_wait

    def extract_products(self, url: str) -> Optional[list[dict]]:
        """
        Opens URL in new OpenClaw browser tab, waits for JS hydration,
        extracts Product JSON-LD schemas, returns list of product dicts.
        """
        # Step 1: Open new tab
        nav = subprocess.run(
            ["openclaw", "browser", "open", url],
            capture_output=True, text=True, timeout=30,
        )

        if nav.returncode != 0:
            print(f"Bridge: open failed: {nav.stderr.strip()[:200]}")
            return None

        # Step 2: Parse the returned tab ID
        tab_id = self._parse_tab_id(nav.stdout)
        if not tab_id:
            print(f"Bridge: could not parse tab ID from output: {nav.stdout.strip()[:200]}")
            return None

        # Step 3: Wait for JS hydration
        time.sleep(self.render_wait)

        # Step 4: Evaluate JS extraction
        eval_result = subprocess.run(
            [
                "openclaw", "browser", "evaluate",
                "--target-id", tab_id,
                "--fn", self.JS_EXTRACT,
            ],
            capture_output=True, text=True, timeout=30,
        )

        if eval_result.returncode != 0:
            print(f"Bridge: evaluate failed: {eval_result.stderr.strip()[:200]}")
            return None

        raw = eval_result.stdout.strip()
        if not raw or raw == "undefined" or raw == "null" or raw == "no target":
            return []

        try:
            # Double-decode: CLI wraps JS JSON-string output in JSON
            products = json.loads(json.loads(raw))
            if not isinstance(products, list):
                return []
            return products
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Bridge: JSON parse error: {e}")
            print(f"Bridge: raw: {raw[:200]}")
            return None

    @staticmethod
    def _parse_tab_id(output: str) -> Optional[str]:
        """
        Parse tab ID from 'openclaw browser open' stdout.
        Format: "opened: <url>\nid: <id>"
        """
        # Try "id: <id>" format first
        match = re.search(r"^id:\s*(\S+)", output, re.MULTILINE)
        if match:
            return match.group(1)
        # Fallback: look for hex-like ID anywhere in output
        match = re.search(r"\b([0-9A-Fa-f]{16,})\b", output)
        if match:
            return match.group(1)
        return None


# ---------------------------------------------------------------------------
# CLI Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore")

    bridge = BrowserBridge(render_wait=4)

    test_urls = [
        "https://www.gymshark.com/products/gymshark-movement-sport-5-short-shorts",
        "https://www.gymshark.com/products/gymshark-geo-seamless-t-shirt-ss-tops-blue-ss26",
    ]

    print("=" * 70)
    print("Browser Bridge — Full Extraction Test")
    print("=" * 70)

    for url in test_urls:
        print(f"\n>>> {url}")
        products = bridge.extract_products(url)

        if products:
            print(f"  Found {len(products)} product(s):")
            for p in products:
                name = (p.get("name") or "N/A").replace("&quot;", '"').replace("&amp;", "&")[:60]
                brand = p.get("brand") or "N/A"
                price = p.get("price") or "?"
                currency = p.get("currency") or "USD"
                rating = p.get("ratingValue") or "?"
                reviews = p.get("reviewCount") or "?"
                cat = p.get("category") or "N/A"
                print(f"  ✅ {name}")
                print(f"     Brand: {brand} | Price: {currency} {price}")
                print(f"     Rating: {rating}/5 ({reviews} reviews) | Category: {cat}")
                if p.get("tags"):
                    print(f"     Tags: {', '.join(p['tags'][:3])}")
        else:
            print(f"  ❌ No products found")

    print("\n" + "=" * 70)
    print("Done.")
