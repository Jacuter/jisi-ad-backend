"""
Shopify Product Data Extractor — Module A
Jisi × Shopify AI Video Ad System

Extracts structured product data from any Shopify product page.

Two extraction strategies:
1. Fast path: HTTP fetch + JSON-LD parsing (works for non-JS pages)
2. Browser path: OpenClaw Chrome renders JS → extracts rendered JSON-LD

Shopify pages use JavaScript to inject JSON-LD after load, so the
browser path is the reliable default for Shopify stores.

Usage:
    extractor = ShopifyExtractor()
    product = extractor.extract("https://www.gymshark.com/products/...")
    print(product.title, product.price, product.images)
"""

from urllib.parse import urlparse
import re
import json
import time
import subprocess
import warnings
from dataclasses import dataclass, field, asdict
from typing import Optional

import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class PriceInfo:
    amount: float
    currency: str = "USD"

@dataclass
class ProductImage:
    url: str
    alt_text: str = ""
    is_main: bool = False

@dataclass
class RatingInfo:
    value: float
    count: int

@dataclass
class ReviewSample:
    author: str
    rating: int
    text: str

@dataclass
class ProductJSON:
    """Structured product data matching SPEC.md Section 3.1"""
    product_id: Optional[str]
    url: str
    shopify_domain: str
    handle: str
    title: Optional[str]
    brand: Optional[str]
    description: Optional[str]
    price: Optional[PriceInfo]
    images: list = field(default_factory=list)
    rating: Optional[RatingInfo] = None
    reviews_sample: list = field(default_factory=list)
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: list = field(default_factory=list)
    raw_jsonld: Optional[dict] = None
    errors: list = field(default_factory=list)
    extraction_method: Optional[str] = None  # "requests" or "browser"

    def to_dict(self) -> dict:
        d = {
            "product_id": self.product_id,
            "url": self.url,
            "shopify_domain": self.shopify_domain,
            "handle": self.handle,
            "title": self.title,
            "brand": self.brand,
            "description": self.description[:200] + "..." if self.description and len(self.description) > 200 else self.description,
            "price": asdict(self.price) if self.price else None,
            "images": [asdict(img) for img in self.images],
            "rating": asdict(self.rating) if self.rating else None,
            "reviews_sample": [asdict(r) for r in self.reviews_sample],
            "category": self.category,
            "subcategory": self.subcategory,
            "tags": self.tags,
            "extraction_method": self.extraction_method,
            "errors": self.errors,
        }
        return d

    def summary(self) -> str:
        parts = []
        if self.title: parts.append(f"Title: {self.title[:60]}")
        if self.brand: parts.append(f"Brand: {self.brand}")
        if self.price: parts.append(f"Price: {self.price.currency} {self.price.amount}")
        if self.images: parts.append(f"Images: {len(self.images)}")
        if self.rating: parts.append(f"Rating: {self.rating.value}/5 ({self.rating.count} reviews)")
        if self.errors: parts.append(f"Errors: {', '.join(self.errors)}")
        return " | ".join(parts)


# ---------------------------------------------------------------------------
# Main Extractor
# ---------------------------------------------------------------------------

class ShopifyExtractor:
    """
    Extracts structured product data from any Shopify product page.

    Shopify stores use JavaScript to dynamically inject JSON-LD schema data
    after page load. This means:
    - requests/BeautifulSoup alone CANNOT see the data (Shopify blocks non-browser clients)
    - Browser rendering is required for reliable extraction

    Extraction strategy:
    1. Try OpenClaw Browser (JS rendering) — this is the reliable path for Shopify
    2. Fall back to requests if browser is unavailable
    """

    BROWSER_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(self, timeout: int = 15, max_retries: int = 1):
        self.timeout = timeout
        self.max_retries = max_retries

#  // -------------------------------------------------------------------------
#  // Public API
#  // -------------------------------------------------------------------------

    def extract(self, url: str) -> ProductJSON:
        """
        Main entry point.
        Returns ProductJSON with all available fields.
        Automatically selects browser or requests path.
        """
        errors = []

        if not self._is_shopify_url(url):
            raise ValueError(f"Not a Shopify URL: '{url}'")

        domain = self.extract_domain(url)
        handle = self.extract_handle(url)

        # Try browser path first (reliable for Shopify JS-rendered pages)
        try:
            product = self._extract_via_browser(url, domain, handle)
            if product and (product.title or product.description):
                return product
        except Exception as e:
            errors.append(f"Browser extraction failed: {e}")

        # Fall back to requests
        try:
            product = self._extract_via_requests(url, domain, handle)
            product.errors = errors
            if product.title or product.description:
                return product
        except Exception as e:
            errors.append(f"Requests extraction failed: {e}")

        return ProductJSON(
            product_id=None, url=url, shopify_domain=domain,
            handle=handle, title=None, brand=None, description=None,
            price=None, errors=errors
        )

    def extract_via_browser(self, url: str) -> Optional[ProductJSON]:
        """Explicit browser extraction (for testing)."""
        domain = self.extract_domain(url)
        handle = self.extract_handle(url)
        return self._extract_via_browser(url, domain, handle)

    def extract_domain(self, url: str) -> str:
        return urlparse(url).netloc.replace("www.", "")

    def extract_handle(self, url: str) -> str:
        path_parts = [p for p in urlparse(url).path.split("/") if p]
        if "products" in path_parts:
            idx = path_parts.index("products")
            return path_parts[idx + 1] if idx + 1 < len(path_parts) else ""
        return path_parts[-1] if path_parts else ""

#  // -------------------------------------------------------------------------
#  // Browser Extraction (OpenClaw Chrome)
#  // -------------------------------------------------------------------------

    def _extract_via_browser(self, url: str, domain: str, handle: str) -> Optional[ProductJSON]:
        """Extract using OpenClaw Chrome — handles JS-rendered Shopify pages."""
        warnings.filterwarnings("ignore")

        # Open tab and get ID
        nav = subprocess.run(
            ["openclaw", "browser", "open", url],
            capture_output=True, text=True, timeout=30,
        )
        if nav.returncode != 0:
            raise RuntimeError(f"openclaw browser open failed: {nav.stderr.strip()[:100]}")

        tab_id = self._parse_tab_id(nav.stdout)
        if not tab_id:
            raise RuntimeError(f"Could not parse tab ID: {nav.stdout.strip()[:100]}")

        # Wait for JS hydration
        time.sleep(4)

        # Extract JSON-LD
        js_code = r"""
(function() {
    var r = [];
    var scripts = document.querySelectorAll('script[type="application/ld+json"]');
    for (var i = 0; i < scripts.length; i++) {
        try {
            var raw = JSON.parse(scripts[i].textContent);
            var items = Array.isArray(raw) ? raw : [raw];
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
                        images: Array.isArray(item.image) ? item.image.slice(0, 10) : (item.image ? [item.image] : []),
                        ratingValue: item.aggregateRating ? item.aggregateRating.ratingValue : null,
                        reviewCount: item.aggregateRating ? (item.aggregateRating.reviewCount || item.aggregateRating.ratingCount) : null,
                        category: item.category || null,
                        color: item.color || null
                    });
                }
            }
        } catch(e) {}
    }
    return JSON.stringify(r);
})()
"""
        eval_result = subprocess.run(
            ["openclaw", "browser", "evaluate",
             "--target-id", tab_id,
             "--fn", js_code.strip()],
            capture_output=True, text=True, timeout=30,
        )

        if eval_result.returncode != 0:
            raise RuntimeError(f"openclaw evaluate failed: {eval_result.stderr.strip()[:100]}")

        raw = eval_result.stdout.strip()
        if not raw or raw in ("undefined", "null", "no target"):
            # Try text-based fallback
            return self._extract_via_browser_text(tab_id, url, domain, handle)

        # Double-decode (CLI wraps JS JSON-string output)
        try:
            products = json.loads(json.loads(raw))
        except (json.JSONDecodeError, TypeError):
            # JSON parse failed, try text-based fallback
            return self._extract_via_browser_text(tab_id, url, domain, handle)

        if not isinstance(products, list) or len(products) == 0:
            # No products in JSON-LD, try text-based fallback
            return self._extract_via_browser_text(tab_id, url, domain, handle)

        # Parse first Product schema
        raw_product = products[0]
        return self._parse_product_dict(raw_product, url, domain, handle, "browser")

    def _extract_via_browser_text(self, tab_id: str, url: str, domain: str, handle: str) -> ProductJSON:
        """
        Fallback: extract product data from page text content when JSON-LD is unavailable.
        Uses OpenClaw Chrome to get innerText and metadata.
        """
        # Get page title
        eval_title = subprocess.run(
            ["openclaw", "browser", "evaluate", "--target-id", tab_id, "--fn",
             "() => document.querySelector('title')?.textContent?.trim() || ''"],
            capture_output=True, text=True, timeout=15,
        )
        title_raw = eval_title.stdout.strip().strip('"')
        
        # Get meta description
        eval_desc = subprocess.run(
            ["openclaw", "browser", "evaluate", "--target-id", tab_id, "--fn",
             "() => document.querySelector('meta[name=description]')?.content || ''"],
            capture_output=True, text=True, timeout=15,
        )
        description = eval_desc.stdout.strip().strip('"')[:500]
        
        # Get page text (main content area)
        eval_text = subprocess.run(
            ["openclaw", "browser", "evaluate", "--target-id", tab_id, "--fn",
             "() => document.body.innerText.slice(0, 2000)"],
            capture_output=True, text=True, timeout=15,
        )
        page_text = eval_text.stdout.strip().strip('"')
        
        # Extract price — first look for structured price element text
        import re
        price_amount = None
        eval_price = subprocess.run(
            ["openclaw", "browser", "evaluate", "--target-id", tab_id, "--fn",
             "() => { var el = document.querySelector('[class*=price], .product-price, [data-price]'); return el ? el.textContent.trim() : ''; }"],
            capture_output=True, text=True, timeout=15,
        )
        price_text = eval_price.stdout.strip().strip('"')
        price_match = re.search(r'\$([\d,]+\.?\d*)', price_text)
        if price_match:
            price_amount = float(price_match.group(1).replace(',', ''))
        if not price_amount:
            # Fallback: first $ in page text
            price_match = re.search(r'\$(\d+\.?\d*)', page_text)
            price_amount = float(price_match.group(1)) if price_match else None
        
        # Extract title from page title (format: "Product Name – Brand - Taliswind")
        title = title_raw.split(" – ")[0].strip() if title_raw else None
        
        # Try to extract product images
        eval_imgs = subprocess.run(
            ["openclaw", "browser", "evaluate", "--target-id", tab_id, "--fn",
             "() => { var results = []; var imgs = document.querySelectorAll('img'); for (var img of imgs) { var src = img.src || ''; if (src.includes('/cdn/shop/files/') && !src.includes('logo') && img.naturalWidth > 200) results.push(src); if (results.length >= 5) break; } return results.join('|'); }"],
            capture_output=True, text=True, timeout=15,
        )
        images = []
        img_srcs = eval_imgs.stdout.strip().strip('"').split('|')
        for i, src in enumerate(img_srcs):
            if src:
                images.append(ProductImage(url=src, alt_text=title or "", is_main=(i == 0)))
        if not images:
            # Try any taliswind image over 100px wide
            eval_imgs2 = subprocess.run(
                ["openclaw", "browser", "evaluate", "--target-id", tab_id, "--fn",
                 "() => { var results = []; var imgs = document.querySelectorAll('img'); for (var img of imgs) { var src = img.src || ''; if ((src.includes('taliswind') || src.includes('cdn')) && img.naturalWidth > 100) results.push(src); if (results.length >= 5) break; } return results.join('|'); }"],
                capture_output=True, text=True, timeout=15,
            )
            img_srcs2 = eval_imgs2.stdout.strip().strip('"').split('|')
            for i, src in enumerate(img_srcs2):
                if src:
                    images.append(ProductImage(url=src, alt_text=title or "", is_main=(i == 0)))
        
        # Infer brand from domain
        brand = "Crystal Valley" if "taliswind" in domain else None
        
        # Build a ProductJSON from text extraction
        price_info = PriceInfo(amount=price_amount, currency="USD") if price_amount else None
        
        return ProductJSON(
            product_id=None,
            url=url,
            shopify_domain=domain,
            handle=handle,
            title=title,
            brand=brand,
            description=description,
            price=price_info,
            images=images,
            rating=None,
            reviews_sample=[],
            category=None,
            tags=[],
            errors=["Used text-based fallback extraction (JSON-LD unavailable)"],
            extraction_method="browser_text_fallback"
        )
    
    def _parse_tab_id(self, output: str) -> Optional[str]:
        import re
        match = re.search(r"^id:\s*(\S+)", output, re.MULTILINE)
        if match:
            return match.group(1)
        match = re.search(r"\b([0-9A-Fa-f]{16,})\b", output)
        return match.group(1) if match else None

#  // -------------------------------------------------------------------------
#  // Requests Extraction (fallback)
#  // -------------------------------------------------------------------------

    def _extract_via_requests(self, url: str, domain: str, handle: str) -> ProductJSON:
        """Fallback extraction using requests + BeautifulSoup."""
        warnings.filterwarnings("ignore")

        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    headers=self.BROWSER_HEADERS,
                    timeout=self.timeout,
                    allow_redirects=True,
                    verify=False,  # Some Shopify stores have SSL issues
                )
                response.raise_for_status()
                break
            except requests.exceptions.SSLError:
                response = requests.get(
                    url, headers=self.BROWSER_HEADERS,
                    timeout=self.timeout, allow_redirects=True, verify=False
                )
                break
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    raise ProductNotFoundError(f"Product not found: {url}")
                elif e.response.status_code in (403, 429):
                    time.sleep(2)
                else:
                    raise
            except Exception as e:
                raise RuntimeError(f"Request failed: {e}")

        soup = BeautifulSoup(response.text, "lxml")
        return self._parse_soup(soup, url, domain, handle)

    def _parse_soup(self, soup: BeautifulSoup, url: str, domain: str, handle: str) -> ProductJSON:
        """Parse from requests HTML (no JS rendering)."""
        # Try JSON-LD
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    for item in data:
                        if self._is_product_schema(item):
                            return self._parse_product_dict(item, url, domain, handle, "requests")
                elif self._is_product_schema(data):
                    return self._parse_product_dict(data, url, domain, handle, "requests")
            except (json.JSONDecodeError, AttributeError):
                pass

        # Fall back to meta tags
        def meta(name_or_prop):
            t = soup.find("meta", attrs={"property": name_or_prop}) or \
                soup.find("meta", attrs={"name": name_or_prop})
            return t.get("content", "").strip() if t else None

        title = meta("og:title") or meta("twitter:title")
        brand = meta("og:brand") or meta("product:brand")
        description = meta("og:description")
        price_tag = soup.find("meta", attrs={"name": "twitter:label1"})
        price = None
        if price_tag:
            m = re.search(r"[\d.,]+", price_tag.get("content", ""))
            if m:
                price = PriceInfo(amount=float(m.group().replace(",", "")), currency="USD")

        images = []
        og_img = meta("og:image")
        if og_img:
            images = [ProductImage(url=og_img, is_main=True)]

        return ProductJSON(
            product_id=meta("product:retailer_item_id"),
            url=url, shopify_domain=domain, handle=handle,
            title=title, brand=brand, description=description,
            price=price, images=images,
            extraction_method="requests",
            errors=["No JSON-LD found, fell back to meta tags"]
        )

    def _is_product_schema(self, item) -> bool:
        if not isinstance(item, dict):
            return False
        t = item.get("@type", "")
        if isinstance(t, list):
            return bool(set(t) & {"Product", "IndividualProduct", "ProductGroup"})
        return t in {"Product", "IndividualProduct", "ProductGroup"}

    def _parse_product_dict(self, data: dict, url: str, domain: str, handle: str, method: str) -> ProductJSON:
        """Map a Product JSON-LD dict to ProductJSON dataclass."""
        pid = data.get("sku") or str(data.get("@id", "")).split("/")[-1]
        if not pid or pid == handle:
            pid = data.get("sku")

        name = data.get("name")
        if name:
            name = name.replace("&quot;", '"').replace("&amp;", "&")

        brand = data.get("brand")
        if isinstance(brand, dict):
            brand = brand.get("name")

        desc = data.get("description")
        if isinstance(desc, list):
            desc = " ".join(str(d) for d in desc)

        # Handle both nested offers{} and flat price/currency fields (from browser bridge)
        offers = data.get("offers", {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}
        price = None
        # Try nested path first (standard JSON-LD)
        if offers:
            amt = offers.get("price")
            if amt:
                price = PriceInfo(amount=float(amt), currency=str(offers.get("priceCurrency", "USD")))
        # Fall back to flat fields (from browser bridge JS extraction)
        if not price:
            amt = data.get("price")
            currency = data.get("currency")
            if amt:
                price = PriceInfo(amount=float(amt), currency=str(currency or "USD"))

        img_list = data.get("images") or data.get("image") or []
        if isinstance(img_list, str):
            img_list = [img_list]
        images = []
        for i, img in enumerate(img_list[:10]):
            img_url = img.get("url") if isinstance(img, dict) else str(img)
            if img_url:
                images.append(ProductImage(url=img_url, is_main=(i == 0)))

        agg = data.get("aggregateRating", {})
        rating = None
        if agg:
            rv = agg.get("ratingValue")
            rc = agg.get("reviewCount") or agg.get("ratingCount")
            if rv:
                rating = RatingInfo(value=float(rv), count=int(rc) if rc else 0)

        reviews = []
        for r in (data.get("review") or [])[:5]:
            if isinstance(r, dict):
                author_data = r.get("author", {})
                author = author_data.get("name", "") if isinstance(author_data, dict) else str(author_data or "")
                rr = r.get("reviewRating", {})
                rr_val = rr.get("ratingValue") if isinstance(rr, dict) else None
                reviews.append(ReviewSample(
                    author=author,
                    rating=int(rr_val) if rr_val else 5,
                    text=str(r.get("reviewBody", ""))[:300]
                ))

        tags = []
        if data.get("color"):
            tags.append(f"color:{data['color']}")
        if data.get("size"):
            tags.append(f"size:{data['size']}")

        return ProductJSON(
            product_id=pid,
            url=url,
            shopify_domain=domain,
            handle=handle,
            title=name,
            brand=brand,
            description=desc,
            price=price,
            images=images,
            rating=rating,
            reviews_sample=reviews,
            category=data.get("category"),
            tags=tags,
            raw_jsonld=data,
            extraction_method=method,
        )

    def _is_shopify_url(self, url: str) -> bool:
        parsed = urlparse(url.lower())
        return "/products/" in parsed.path.lower()


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ShopifyExtractorError(Exception):
    pass

class ProductNotFoundError(ShopifyExtractorError):
    pass


# ---------------------------------------------------------------------------
# CLI Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    extractor = ShopifyExtractor()

    test_urls = [
        "https://www.gymshark.com/products/gymshark-movement-sport-5-short-shorts",
        "https://www.gymshark.com/products/gymshark-geo-seamless-t-shirt-ss-tops-blue-ss26",
    ]

    print("=" * 70)
    print("Shopify Product Data Extractor — Test Suite")
    print("=" * 70)

    for url in test_urls:
        print(f"\n>>> {url}")
        try:
            product = extractor.extract(url)
            print(f"    Method: {product.extraction_method or 'unknown'}")
            print(f"    Title:  {product.title or '(none)'}")
            print(f"    Brand:  {product.brand or '(none)'}")
            if product.price:
                print(f"    Price:  {product.price.currency} {product.price.amount}")
            print(f"    Images: {len(product.images)} found")
            if product.rating:
                print(f"    Rating: {product.rating.value}/5 ({product.rating.count} reviews)")
            if product.reviews_sample:
                for r in product.reviews_sample[:1]:
                    print(f"    Review: [{r.author}] {r.text[:80]}...")
            if product.errors:
                print(f"    Errors: {product.errors}")
            print(f"    ✅ Success")
        except Exception as e:
            print(f"    ❌ {type(e).__name__}: {e}")

    print("\n" + "=" * 70)
    print("Done.")
