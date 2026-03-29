"""
apify_integration.py — Jisi × Apify Meta Ad Library Integration
Jisi × Shopify AI Video Ad System

Uses Apify's Meta Ad Scraper (whoareyouanas~meta-ad-scraper) to
fetch real competitor ad data from Facebook Ad Library.

Setup:
    pip install apify-client

Actor: whoareyouanas~meta-ad-scraper (free, works with RESIDENTIAL proxy)
API: Uses Python SDK (not REST API) for reliability

NOTE: The REST API had issues accessing runs/datasets from this environment.
Use Python SDK which works correctly.
"""

import os
import json
import time
from dataclasses import dataclass
from typing import Optional

# Optional: install on demand
try:
    from apify_client import ApifyClient
except ImportError:
    os.system("pip install apify-client")
    from apify_client import ApifyClient


# Default token - can also use environment variable APIFY_TOKEN
DEFAULT_TOKEN = "YOUR_APIFY_TOKEN_HERE"
ACTOR_NAME = "whoareyouanas~meta-ad-scraper"


@dataclass
class ApifyAdData:
    """Normalized ad data from Apify Meta Ad Scraper"""
    page_name: str
    ad_text: str
    likes: int
    comments: int
    shares: int
    love: int
    wow: int
    haha: int
    sad: int
    angry: int
    care: int
    image_urls: list
    page_url: str
    search_term: str = ""
    country: str = "US"

    def to_dict(self) -> dict:
        return {
            "page_name": self.page_name,
            "ad_text": self.ad_text,
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "reactions": {
                "love": self.love, "wow": self.wow, "haha": self.haha,
                "sad": self.sad, "angry": self.angry, "care": self.care
            },
            "image_urls": self.image_urls,
            "page_url": self.page_url,
            "search_term": self.search_term,
            "country": self.country,
        }


class ApifyMetaScraper:
    """
    Fetches competitor ad data from Meta/Facebook Ad Library via Apify.
    
    Usage:
        scraper = ApifyMetaScraper()
        ads = scraper.scrape(keyword="gymshark", country="US")
        for ad in ads:
            print(ad.ad_text[:100])
    """
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or DEFAULT_TOKEN
        # Try environment variable first, then token
        self.client = ApifyClient(os.environ.get("APIFY_TOKEN", self.token))
    
    def scrape(self, keyword: str, country: str = "US",
               max_ads: int = 50, timeout: int = 120) -> list[ApifyAdData]:
        """
        Scrape ads from Meta Ad Library for a keyword.
        
        Args:
            keyword: Search term (e.g., "gymshark leggings")
            country: ISO country code (default: US)
            max_ads: Maximum number of ads to fetch
            timeout: Timeout in seconds
        
        Returns:
            List of ApifyAdData objects
        """
        print(f"[ApifyMetaScraper] Scraping '{keyword}' in {country}...")
        
        actor = self.client.actor(ACTOR_NAME)
        
        # Start the run - NOTE: fields must match what Apify Console sends
        run = actor.start(
            run_input={
                "country": country,
                "searchQuery": keyword,
                "pageId": "",
                "activeStatus": "active",
                "adType": "all",
                "mediaType": "all",
                "isTargetedCountry": False,
                "sortMode": "total_impressions",
                "sortDirection": "desc",
                "maxConcurrency": 1,
                "requestHandlerTimeoutSecs": 900,
            }
        )
        
        run_id = run["id"]
        print(f"[ApifyMetaScraper] Run started: {run_id}")
        
        # Poll until completion
        start_time = time.time()
        while time.time() - start_time < timeout:
            run_info = self.client.run(run_id).get()
            status = run_info.get("status")
            
            if status == "SUCCEEDED":
                print(f"[ApifyMetaScraper] Run succeeded!")
                break
            elif status in ["FAILED", "ABORTED", "ERROR"]:
                print(f"[ApifyMetaScraper] Run failed: {status}")
                print(f"Error: {run_info.get('errorMessage', 'unknown')}")
                return []
            
            time.sleep(5)
            elapsed = int(time.time() - start_time)
            print(f"[ApifyMetaScraper] Status: {status} ({elapsed}s)")
        else:
            print(f"[ApifyMetaScraper] Timeout after {timeout}s")
            return []
        
        # Fetch results
        dataset_id = run_info.get("storageIds", {}).get("datasets", {}).get("default")
        if not dataset_id:
            print("[ApifyMetaScraper] No dataset ID returned")
            return []
        
        print(f"[ApifyMetaScraper] Fetching dataset: {dataset_id}")
        
        ads = []
        try:
            for item in self.client.dataset(dataset_id).iterate_items():
                ad = self._parse_ad(item, keyword, country)
                if ad:
                    ads.append(ad)
                    if len(ads) >= max_ads:
                        break
        except Exception as e:
            print(f"[ApifyMetaScraper] Error fetching items: {e}")
        
        print(f"[ApifyMetaScraper] Got {len(ads)} ads")
        return ads
    
    def _parse_ad(self, item: dict, keyword: str, country: str) -> Optional[ApifyAdData]:
        """Parse a raw ad item into ApifyAdData."""
        try:
            return ApifyAdData(
                page_name=item.get("page_name", ""),
                ad_text=item.get("ad_text", ""),
                likes=item.get("likes", 0) or 0,
                comments=item.get("comments", 0) or 0,
                shares=item.get("shares", 0) or 0,
                love=item.get("love", 0) or 0,
                wow=item.get("wow", 0) or 0,
                haha=item.get("haha", 0) or 0,
                sad=item.get("sad", 0) or 0,
                angry=item.get("angry", 0) or 0,
                care=item.get("care", 0) or 0,
                image_urls=item.get("image_urls", []) or [],
                page_url=item.get("page_url", ""),
                search_term=keyword,
                country=country,
            )
        except Exception:
            return None
    
    def scrape_and_save(self, keyword: str, country: str = "US",
                        output_path: str = "scraped_ads.json") -> list[ApifyAdData]:
        """Scrape ads and save to JSON file."""
        ads = self.scrape(keyword, country)
        
        data = {
            "keyword": keyword,
            "country": country,
            "count": len(ads),
            "ads": [ad.to_dict() for ad in ads],
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[ApifyMetaScraper] Saved {len(ads)} ads to {output_path}")
        return ads


# ─── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    keyword = sys.argv[1] if len(sys.argv) > 1 else "gymshark"
    country = sys.argv[2] if len(sys.argv) > 2 else "US"
    
    scraper = ApifyMetaScraper()
    ads = scraper.scrape(keyword, country)
    
    print(f"\nGot {len(ads)} ads:")
    for i, ad in enumerate(ads[:5], 1):
        print(f"\n--- Ad #{i} ---")
        print(f"  Page: {ad.page_name}")
        print(f"  Text: {ad.ad_text[:150]}...")
        print(f"  Likes: {ad.likes} | Comments: {ad.comments}")
