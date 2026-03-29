#!/usr/bin/env python3
"""
api_backend.py — Jisi Ad Creative Backend
Called by Next.js API route to generate ad creative results.

Usage:
    python3 api_backend.py <product_url> <platform> [mock_category]
    python3 api_backend.py "https://taliswind.com/..." meta
    python3 api_backend.py mock meta athletic_leggings
    python3 api_backend.py --fetch-ads "healing crystal jewelry"
"""

import sys, os, json, subprocess, re, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from modules.shopify_extractor import ShopifyExtractor, ProductJSON, PriceInfo, RatingInfo, ProductImage
from modules.category_patterns import match_category, get_pattern
from modules.ad_generator import AdGenerator, AdVariant, _build_meta_storyboard, _build_tiktok_storyboard
from modules.ad_evaluator import AdEvaluator
from modules.competitor_insights import get_crystal_jewelry_variants, load_competitor_patterns

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


# ─── Apify Fetch ──────────────────────────────────────────────────────────────

def _query_to_filename(query: str) -> str:
    """Convert a search query to a safe filename slug."""
    slug = re.sub(r'[^a-z0-9]+', '_', query.lower()).strip('_')
    return f"{slug}_ads.json"


def fetch_competitor_ads(query: str, country: str = "US") -> str:
    """
    Fetch competitor ads from Meta Ad Library via Apify CLI.
    Saves results to data/<slug>_ads.json and returns the output path.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    out_path = os.path.join(DATA_DIR, _query_to_filename(query))

    run_input = json.dumps({
        "country": country,
        "searchQuery": query,
        "pageId": "",
        "activeStatus": "active",
        "adType": "all",
        "mediaType": "all",
        "isTargetedCountry": False,
        "sortMode": "total_impressions",
        "sortDirection": "desc",
        "maxConcurrency": 1,
        "requestHandlerTimeoutSecs": 900,
    })

    print(f"[fetch_competitor_ads] Fetching '{query}' via Apify CLI...")
    result = subprocess.run(
        ["apify", "call", "whoareyouanas/meta-ad-scraper", "--silent", "--output-dataset"],
        input=run_input,
        capture_output=True,
        text=True,
        timeout=1200,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Apify CLI failed: {result.stderr[:300]}")

    # Parse the dataset output (JSON array printed to stdout)
    raw = result.stdout.strip()
    if not raw:
        raise RuntimeError("Apify CLI returned empty output")

    ads = json.loads(raw)
    if not isinstance(ads, list):
        # Some versions wrap in {"items": [...]}
        ads = ads.get("items", ads)

    # Normalize to the format competitor_insights.py expects
    normalized = []
    for item in ads:
        normalized.append({
            "body": item.get("ad_text") or item.get("body") or "",
            "ctaText": item.get("cta_text") or item.get("ctaText") or "",
            "page_name": item.get("page_name", ""),
            "likes": item.get("likes", 0),
        })

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)

    print(f"[fetch_competitor_ads] Saved {len(normalized)} ads to {out_path}")
    return out_path


# ─── Evolution Engine (lightweight wrapper) ───────────────────────────────────

EVOLUTION_STATE_PATH = os.path.join(os.path.dirname(__file__), "modules", "evolution_state.json")


def _load_evolution_state() -> dict:
    if os.path.exists(EVOLUTION_STATE_PATH):
        with open(EVOLUTION_STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"evolution_log": [], "pattern_feedback": {}}


def _save_evolution_state(state: dict):
    with open(EVOLUTION_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _record_generation(category: str, platform: str, variants: list, feedback_score=None):
    """
    Record this generation run into evolution_state.json.
    Updates effectiveness scores for each hook type used.
    """
    state = _load_evolution_state()
    feedback = state.setdefault("pattern_feedback", {})
    now = time.strftime("%Y-%m-%d %H:%M:%S")

    for v in variants:
        hook_type = v.hook_type if hasattr(v, "hook_type") else v.get("hook_type", "unknown")
        eval_score = (v.evaluation.overall_score if hasattr(v, "evaluation") and v.evaluation else 0)
        # If user provided explicit feedback, blend it in (scale 1-5 → 0-10)
        if feedback_score is not None:
            eval_score = eval_score * 0.5 + float(feedback_score) * 2 * 0.5

        key = f"{category}_{platform}_{hook_type}"
        if key in feedback:
            existing = feedback[key]
            existing["effectiveness_score"] = existing["effectiveness_score"] * 0.7 + eval_score * 0.3
            existing["frequency_used"] = existing.get("frequency_used", 0) + 1
            existing["last_updated"] = now
        else:
            feedback[key] = {
                "category": category,
                "platform": platform,
                "hook_type": hook_type,
                "effectiveness_score": eval_score,
                "frequency_used": 1,
                "last_updated": now,
            }

    # Append a summary log entry
    log = state.setdefault("evolution_log", [])
    scores = [v.evaluation.overall_score for v in variants if hasattr(v, "evaluation") and v.evaluation]
    log.append({
        "timestamp": now,
        "category": category,
        "platform": platform,
        "num_variants": len(variants),
        "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "feedback_score": feedback_score,
    })
    state["evolution_log"] = log[-100:]  # keep last 100

    _save_evolution_state(state)


def _get_evolved_hook_order(category: str, platform: str, default_hooks: list) -> list:
    """
    Return hook types sorted by evolved effectiveness score (best first).
    Falls back to default_hooks order if no data exists.
    """
    state = _load_evolution_state()
    feedback = state.get("pattern_feedback", {})

    scored = []
    for hook in default_hooks:
        key = f"{category}_{platform}_{hook}"
        score = feedback.get(key, {}).get("effectiveness_score", 5.0)  # neutral default
        scored.append((hook, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [h for h, _ in scored]



MOCK_PRODUCTS = {
    "athletic_leggings": ProductJSON(
        product_id="mock-001",
        url="https://gymshark.com/products/movement-sport-5-shorts",
        shopify_domain="gymshark.com",
        handle="movement-sport-5-shorts",
        title='Movement Sport 5" Shorts',
        brand="Gymshark",
        description="High-performance sport shorts with squat-proof fabric, moisture-wicking technology, and deep side pockets. Perfect for intense workouts, running, or everyday wear.",
        price=PriceInfo(amount=48.00, currency="USD"),
        images=[ProductImage(url="https://cdn.shopify.com/s/example-1.jpg", alt_text="Front view", is_main=True)],
        rating=RatingInfo(value=4.7, count=8420),
        reviews_sample=[], category="athletic_leggings",
        tags=["gym", "athletic", "squat proof", "workout shorts"],
        errors=[], extraction_method="mock"
    ),
    "skincare": ProductJSON(
        product_id="mock-002",
        url="https://example.com/products/vitamin-c-serum",
        shopify_domain="skincare.example.com",
        handle="vitamin-c-serum",
        title="20% Vitamin C Brightening Serum",
        brand="GlowLab",
        description="Powerful 20% Vitamin C serum with ferulic acid and vitamin E. Clinically proven to reduce dark spots and improve skin radiance within 4 weeks.",
        price=PriceInfo(amount=34.99, currency="USD"),
        images=[],
        rating=RatingInfo(value=4.8, count=12800),
        reviews_sample=[], category="skincare",
        tags=["skincare", "vitamin c", "serum", "brightening"],
        errors=[], extraction_method="mock"
    ),
    "wireless_earbuds": ProductJSON(
        product_id="mock-003",
        url="https://example.com/products/pro-earbuds",
        shopify_domain="audio.example.com",
        handle="pro-earbuds",
        title="ProSound X3 Wireless Earbuds",
        brand="ProSound",
        description="True wireless earbuds with 40-hour battery life, active noise cancellation, and IPX7 waterproof rating. Crystal clear audio with deep bass.",
        price=PriceInfo(amount=79.99, currency="USD"),
        images=[],
        rating=RatingInfo(value=4.6, count=5200),
        reviews_sample=[], category="wireless_earbuds",
        tags=["earbuds", "wireless", "noise cancelling", "waterproof"],
        errors=[], extraction_method="mock"
    ),
    "home_storage": ProductJSON(
        product_id="mock-004",
        url="https://example.com/products/storage-bins",
        shopify_domain="home.example.com",
        handle="storage-bins",
        title="Stackable Storage Bins Set of 6",
        brand="OrganizeIt",
        description="Heavy-duty stackable storage bins with lids. Perfect for closets, garages, and pantries. BPA-free, dishwasher safe.",
        price=PriceInfo(amount=39.99, currency="USD"),
        images=[],
        rating=RatingInfo(value=4.5, count=3100),
        reviews_sample=[], category="home_storage",
        tags=["storage", "organization", "bins", "stackable"],
        errors=[], extraction_method="mock"
    ),
}


def generate(product_url: str, platform: str = "meta", mock_category: str = None,
             fetch_competitor_ads_query: str = None,
             record_feedback: bool = False,
             feedback_score=None) -> dict:
    """Generate ad creative for a product URL."""

    generator = AdGenerator()
    evaluator = AdEvaluator()

    # Optional: fetch fresh competitor data before generating
    if fetch_competitor_ads_query:
        try:
            fetch_competitor_ads(fetch_competitor_ads_query)
        except Exception as e:
            print(f"[generate] Apify fetch failed (continuing): {e}", file=sys.stderr)

    # Step 1: Extract product (or use mock)
    if mock_category or product_url == "mock":
        cat = mock_category or "athletic_leggings"
        product = MOCK_PRODUCTS.get(cat, MOCK_PRODUCTS["athletic_leggings"])
    else:
        extractor = ShopifyExtractor()
        product = extractor.extract(product_url)
        if not product or not product.title:
            return {"error": f"Failed to extract product from {product_url}"}

    # Step 2: Match category
    category = match_category(
        product.title,
        product.tags,
        product.description or ""
    ) or "general"

    # Step 3: Get pattern
    pattern = get_pattern(category, platform)

    # Step 4: Generate variants — use real competitor data for crystal_jewelry
    num = 3 if platform == "meta" else 2

    if category == "crystal_jewelry":
        price_str = f"${product.price.amount}" if product.price else None

        # Apply evolved hook ordering
        default_hooks = ['healing_benefit', 'craftsmanship', 'discount_urgency',
                         'social_proof', 'spiritual_narrative', 'scarcity']
        evolved_hooks = _get_evolved_hook_order(category, platform, default_hooks)

        raw_variants = get_crystal_jewelry_variants(
            product_title=product.title,
            product_brand=product.brand,
            product_price=price_str,
            product_description=product.description,
            num_variants=num,
            hook_order=evolved_hooks,
        )
        # Wrap into AdVariant objects so the rest of the pipeline is unchanged
        variants = []
        for rv in raw_variants:
            storyboard = _build_meta_storyboard(product, rv['hook_text'], rv['body_text'], rv['cta_text'], pattern) \
                if platform == "meta" else \
                _build_tiktok_storyboard(product, rv['hook_text'], rv['body_text'], rv['cta_text'], pattern)
            variants.append(AdVariant(
                hook_type=rv['hook_type'],
                hook_text=rv['hook_text'],
                body_text=rv['body_text'],
                cta_text=rv['cta_text'],
                platform=platform,
                storyboard=storyboard,
                category_pattern_id=f"crystal_jewelry_{platform}_real_data",
            ))
        pattern_note = f"Crystal Jewelry — Real Competitor Data ({rv['competitor_count']} ads analyzed)"
    else:
        variants = generator._generate_variants(product, pattern, platform, num)
        pattern_note = f"{pattern.display_name} ({platform})" if pattern else "general pattern"

    # Step 5: Evaluate each variant
    for v in variants:
        v.evaluation = evaluator.evaluate(
            v.body_text, v.cta_text, v.hook_type, category, None
        )

    # Sort by score
    variants.sort(key=lambda x: x.evaluation.overall_score if x.evaluation else 0, reverse=True)

    # Step 6: Record into evolution state
    if record_feedback or feedback_score is not None:
        try:
            _record_generation(category, platform, variants, feedback_score)
        except Exception as e:
            print(f"[generate] Evolution record failed (continuing): {e}", file=sys.stderr)

    # Build response
    return {
        "success": True,
        "product": {
            "title": product.title,
            "brand": product.brand,
            "price": f"{product.price.amount} {product.price.currency}" if product.price else None,
            "description": product.description,
            "images": [img.url for img in product.images],
            "rating": f"{product.rating.value}/5" if product.rating else None,
            "review_count": product.rating.count if product.rating else None,
        },
        "category": category,
        "platform": platform,
        "pattern_note": pattern_note,
        "variants": [
            {
                "rank": i + 1,
                "hook_type": v.hook_type,
                "hook_text": v.hook_text,
                "body_text": v.body_text,
                "cta_text": v.cta_text,
                "score": v.evaluation.overall_score if v.evaluation else 0,
                "storyboard": v.storyboard,
                "recommendations": v.evaluation.recommendations if v.evaluation else [],
            }
            for i, v in enumerate(variants)
        ],
    }


if __name__ == "__main__":
    args = sys.argv[1:]

    # --fetch-ads "query" — standalone Apify fetch mode
    if args and args[0] == "--fetch-ads":
        query = args[1] if len(args) > 1 else "crystal jewelry"
        out = fetch_competitor_ads(query)
        print(json.dumps({"success": True, "saved_to": out}, indent=2))
        sys.exit(0)

    url = args[0] if args else "mock"
    platform = args[1] if len(args) > 1 else "meta"
    mock_cat = args[2] if len(args) > 2 else None

    result = generate(url, platform, mock_cat, record_feedback=True)
    print(json.dumps(result, indent=2, ensure_ascii=False))
