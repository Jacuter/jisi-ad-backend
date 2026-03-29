#!/usr/bin/env python3
"""
meta_ad_scraper.py — Browser-based Meta Ad Library Scraper
Jisi × Shopify AI Video Ad System

Uses OpenClaw Chrome to:
1. Open Meta Ad Library
2. Search by keyword
3. Scroll to load more ads
4. Extract ad data from page

Requires: OpenClaw browser running (openclaw browser start)
"""

import subprocess
import time
import re
import json
import sys
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))


@dataclass
class MetaAd:
    ad_id: str
    page_name: str
    body_text: str
    cta_text: str
    platform: str
    active_status: str
    impressions: Optional[str] = None
    image_urls: list = field(default_factory=list)
    created_date: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class MetaAdScraper:
    """
    Browser-based Meta/Facebook Ad Library scraper.
    
    No API key, no proxy needed — uses OpenClaw Chrome directly.
    """

    BASE_URL = "https://www.facebook.com/ads/library/"
    SCROLL_PAUSE = 2  # seconds between scrolls
    MAX_SCROLLS = 5   # max times to scroll for more ads

    def __init__(self):
        self._tab_id: Optional[str] = None

    # ─── Browser Operations ───────────────────────────────────────────────

    def _run(self, *args) -> str:
        cmd = ["openclaw", "browser"] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.stdout.strip()

    def _open(self, url: str) -> str:
        output = self._run("open", url)
        match = re.search(r"id:\s*([A-F0-9]+)", output)
        if not match:
            raise RuntimeError(f"Could not parse tab ID: {output[:100]}")
        self._tab_id = match.group(1)
        print(f"  [Browser] Opened: {url[:60]}...")
        print(f"  [Browser] Tab ID: {self._tab_id}")
        return self._tab_id

    def _act(self, ref: str, kind: str = "click", text: Optional[str] = None):
        """Click or type on an element by ref."""
        if not self._tab_id:
            raise RuntimeError("No open tab")
        args = ["act", "--target-id", self._tab_id, "--kind", kind, "--ref", ref]
        if text:
            args.extend(["--text", text])
        return self._run(*args)

    def _evaluate(self, js_fn: str) -> Optional[str]:
        """Evaluate JS and return result."""
        if not self._tab_id:
            raise RuntimeError("No open tab")
        output = self._run("evaluate", "--target-id", self._tab_id, "--fn", js_fn)
        return output.strip()

    def _snapshot(self) -> str:
        if not self._tab_id:
            raise RuntimeError("No open tab")
        return self._run("snapshot", "--target-id", self._tab_id)

    def _close(self):
        if self._tab_id:
            try:
                self._run("close")
            except Exception:
                pass
            self._tab_id = None

    def _wait(self, seconds: int):
        time.sleep(seconds)

    # ─── Core Scraper ─────────────────────────────────────────────────────

    def search(self, keyword: str, country: str = "US",
               max_scrolls: int = 5) -> list[MetaAd]:
        """
        Search Meta Ad Library for keyword and extract ads.
        
        Args:
            keyword: Search term (e.g., "gymshark leggings")
            country: ISO country code (default: US)
            max_scrolls: How many times to scroll for more ads
        
        Returns:
            List of MetaAd objects
        """
        print(f"\n[MetaAdScraper] Searching: '{keyword}' in {country}")
        print(f"  Max scrolls: {max_scrolls}")
        
        # Build search URL
        params = {
            "active_status": "active",
            "ad_type": "all",
            "country": country,
            "q": keyword,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.BASE_URL}?{query}"
        
        # Open URL
        self._open(url)
        self._wait(4)  # Initial hydration

        # Check login status
        login_check = self._evaluate(
            "() => document.querySelector('[href*=\"login\"], form[action*=\"login\"]') ? 'needs_login' : 'ok'"
        )
        if "needs_login" in login_check or not login_check:
            print("  [MetaAdScraper] Warning: May need Facebook login")
        
        # Try to interact with search filters if visible
        self._try_set_country_filter(country)
        
        # Scroll to load more ads
        print(f"  [MetaAdScraper] Scrolling {max_scrolls} times...")
        for i in range(max_scrolls):
            self._scroll_down()
            self._wait(self.SCROLL_PAUSE)
            
            # Check how many ads are visible
            count = self._evaluate(
                "() => document.querySelectorAll('[data-pagelet*=\"AdCard\"], [data-adid], [href*=\"ads/about\"]').length"
            )
            try:
                c = int(count.strip('"'))
                print(f"    Scroll {i+1}: {c} elements visible")
            except (ValueError, TypeError):
                print(f"    Scroll {i+1}: checking...")

        # Extract ads
        print("  [MetaAdScraper] Extracting ad data...")
        ads = self._extract_ads()
        print(f"  [MetaAdScraper] Found {len(ads)} ads")
        
        self._close()
        return ads

    def _try_set_country_filter(self, country: str):
        """Try to set country filter if a country selector is visible."""
        try:
            snapshot = self._snapshot()
            if "combobox" in snapshot.lower():
                # Try to click the country combobox
                # Look for country selector in snapshot
                for line in snapshot.splitlines():
                    if country.lower() in line.lower() and "combobox" in line.lower():
                        # Extract ref
                        m = re.search(r'\[ref=(\w+)\]', line)
                        if m:
                            ref = m.group(1)
                            print(f"  [MetaAdScraper] Setting country to {country}...")
                            self._act(ref, "click")
                            self._wait(1)
                            self._act(ref, "type", country)
                            self._wait(1)
                            break
        except Exception as e:
            print(f"  [MetaAdScraper] Country filter skip: {e}")

    def _scroll_down(self):
        """Scroll the page down to trigger lazy loading."""
        self._evaluate(
            "() => { window.scrollBy(0, 800); }"
        )

    def _extract_ads(self) -> list[MetaAd]:
        """
        Extract ads from current page using JS.
        Meta Ad Library uses various DOM structures depending on version.
        """
        # Try multiple extraction strategies
        extraction_strategies = [
            self._extract_modern_ads,
            self._extract_legacy_ads,
            self._extract_text_based_ads,
        ]
        
        for strategy in extraction_strategies:
            try:
                ads = strategy()
                if len(ads) > 0:
                    print(f"  [MetaAdScraper] Strategy {strategy.__name__}: extracted {len(ads)}")
                    return ads
            except Exception as e:
                print(f"  [MetaAdScraper] Strategy {strategy.__name__} failed: {e}")
        
        return []

    def _extract_modern_ads(self) -> list[MetaAd]:
        """Extract from modern Meta Ad Library DOM (2024+)."""
        js = r"""
        (function() {
            var results = [];
            // Try multiple selectors for modern ad cards
            var selectors = [
                '[data-pagelet*="AdCard"]',
                '[data-adid]',
                'div[role="article"]',
                '[aria-label*="Ad"]'
            ];
            
            var cards = [];
            selectors.forEach(function(sel) {
                var found = document.querySelectorAll(sel);
                if (found.length > cards.length) {
                    cards = found;
                }
            });
            
            for (var i = 0; i < Math.min(cards.length, 50); i++) {
                var card = cards[i];
                var ad = {};
                
                // Get text content broadly
                var text = card.textContent || '';
                
                // Page name
                var pageEl = card.querySelector('[data-ad-preview="page-name"], [aria-label*="page"]');
                ad.page_name = pageEl ? pageEl.textContent.trim().slice(0, 80) : '';
                
                // Body text (ad copy)
                var bodyEl = card.querySelector('[data-ad-preview="message"], .userContent, [data-adid]');
                ad.body_text = bodyEl ? bodyEl.textContent.trim().slice(0, 500) : text.slice(0, 500);
                
                // CTA
                var ctaEl = card.querySelector('a[href*="l.facebook"], a[href*="l.instagram"], a[role="button"]');
                ad.cta_text = ctaEl ? ctaEl.textContent.trim().slice(0, 50) : '';
                
                // Platform
                ad.platform = text.includes('Instagram') ? 'Instagram' : 'Facebook';
                
                // Active status
                ad.active_status = text.includes('Active') || text.includes('Run') ? 'active' : 'inactive';
                
                // Ad ID
                ad.ad_id = card.getAttribute('data-adid') || card.id || String(i);
                
                // Images
                var imgs = card.querySelectorAll('img[src]');
                ad.images = [];
                for (var j = 0; j < Math.min(imgs.length, 3); j++) {
                    var src = imgs[j].src;
                    if (src && !src.includes('profile') && !src.includes('avatar')) {
                        ad.images.push(src);
                    }
                }
                
                // Skip if no useful content
                if (!ad.body_text && !ad.cta_text) continue;
                
                results.push(ad);
            }
            return JSON.stringify(results);
        })()
        """
        
        raw = self._evaluate(js)
        if not raw or raw in ("undefined", "null", ""):
            return []
        
        try:
            items = json.loads(raw)
            if isinstance(items, str):
                items = json.loads(items)
        except (json.JSONDecodeError, TypeError):
            return []
        
        return [MetaAd(
            ad_id=item.get("ad_id", str(i)),
            page_name=item.get("page_name", ""),
            body_text=item.get("body_text", ""),
            cta_text=item.get("cta_text", ""),
            platform=item.get("platform", "Facebook"),
            active_status=item.get("active_status", "active"),
            impressions=item.get("impressions"),
            image_urls=item.get("images", []),
        ) for i, item in enumerate(items)]

    def _extract_legacy_ads(self) -> list[MetaAd]:
        """Extract from legacy Meta Ad Library DOM."""
        js = r"""
        (function() {
            var results = [];
            var cards = document.querySelectorAll('div[id^="Mount_"], div[class*="adCard"]');
            
            for (var i = 0; i < Math.min(cards.length, 30); i++) {
                var card = cards[i];
                var result = {
                    ad_id: card.id || String(i),
                    page_name: '',
                    body_text: card.textContent.trim().slice(0, 500),
                    cta_text: '',
                    platform: 'Facebook',
                    active_status: 'active',
                    images: []
                };
                
                var links = card.querySelectorAll('a[href*="l.facebook"]');
                if (links.length > 0) {
                    result.cta_text = links[0].textContent.trim().slice(0, 50);
                }
                
                results.push(result);
            }
            return JSON.stringify(results);
        })()
        """
        
        raw = self._evaluate(js)
        if not raw or raw in ("undefined", "null", ""):
            return []
        
        try:
            items = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
        
        return [MetaAd(
            ad_id=item.get("ad_id", str(i)),
            page_name=item.get("page_name", ""),
            body_text=item.get("body_text", ""),
            cta_text=item.get("cta_text", ""),
            platform=item.get("platform", "Facebook"),
            active_status=item.get("active_status", "active"),
            image_urls=item.get("images", []),
        ) for i, item in enumerate(items)]

    def _extract_text_based_ads(self) -> list[MetaAd]:
        """
        Last resort: extract ads from text content only.
        Useful when the page renders but DOM selectors don't match.
        """
        js = r"""
        (function() {
            var text = document.body.innerText;
            
            // Split by common ad separators
            var segments = text.split(/Shop Now|Order Now|Get Yours|Learn More|Sign Up|See More/i);
            
            var results = [];
            for (var i = 1; i < Math.min(segments.length, 20); i++) {
                var seg = segments[i].trim().slice(0, 300);
                if (seg.length > 30) {
                    results.push({
                        ad_id: 'seg_' + i,
                        page_name: '',
                        body_text: seg,
                        cta_text: segments[i-1].trim().slice(-30),
                        platform: 'Facebook',
                        active_status: 'active'
                    });
                }
            }
            return JSON.stringify(results);
        })()
        """
        
        raw = self._evaluate(js)
        if not raw or raw in ("undefined", "null", ""):
            return []
        
        try:
            items = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
        
        return [MetaAd(
            ad_id=item.get("ad_id", str(i)),
            page_name=item.get("page_name", ""),
            body_text=item.get("body_text", ""),
            cta_text=item.get("cta_text", ""),
            platform=item.get("platform", "Facebook"),
            active_status=item.get("active_status", "active"),
        ) for i, item in enumerate(items)]


def save_ads(ads: list[MetaAd], keyword: str, output_path: str = "scraped_ads.json"):
    """Save ads to JSON file."""
    data = {
        "keyword": keyword,
        "count": len(ads),
        "ads": [ad.to_dict() for ad in ads]
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(ads)} ads to {output_path}")


if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else "gymshark leggings"
    country = sys.argv[2] if len(sys.argv) > 2 else "US"
    
    print(f"Meta Ad Library Scraper")
    print(f"=" * 50)
    
    scraper = MetaAdScraper()
    ads = scraper.search(keyword, country, max_scrolls=5)
    
    if ads:
        save_ads(ads, keyword, f"scraped_ads_{keyword.replace(' ', '_')}.json")
        
        print(f"\nSample ads:")
        for i, ad in enumerate(ads[:3], 1):
            print(f"\n  --- Ad #{i} ---")
            print(f"  ID: {ad.ad_id}")
            print(f"  Body: {ad.body_text[:150]}...")
            print(f"  CTA: {ad.cta_text}")
            print(f"  Platform: {ad.platform}")
    else:
        print("\nNo ads extracted. Debugging info:")
        scraper._open(f"https://www.facebook.com/ads/library/?active_status=active&q={keyword}&country={country}")
        time.sleep(5)
        snapshot = scraper.scraper__snapshot()
        print(f"Page snapshot ({len(snapshot)} chars):")
        print(snapshot[:2000])
        scraper._close()
