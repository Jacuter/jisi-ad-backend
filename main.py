"""
main.py — Jisi Ad Creative API Server
FastAPI-based REST API for the Jisi ad creative system.

Endpoints:
    POST /generate     — Generate ad creative variants
    GET  /health       — Health check
    POST /fetch-ads    — Fetch competitor ads via Apify
    GET  /evolution    — Get evolution state
"""

import os, sys, json, subprocess, re
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ─── Config ─────────────────────────────────────────────────────────────────

API_TOKEN = os.environ.get("JISI_API_TOKEN", "dev-token-change-me")
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

sys.path.insert(0, str(Path(__file__).parent))
from modules.shopify_extractor import ShopifyExtractor
from modules.category_patterns import match_category, get_pattern
from modules.ad_generator import AdGenerator
from modules.competitor_insights import load_competitor_patterns, get_crystal_jewelry_variants

# ─── FastAPI App ─────────────────────────────────────────────────────────────

app = FastAPI(title="Jisi Ad Creative API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request/Response Models ──────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    url: Optional[str] = None
    platform: str = "meta"
    mock: bool = False
    mock_category: Optional[str] = None
    fetch_competitor_ads: bool = False
    record_feedback: Optional[float] = None

class GenerateResponse(BaseModel):
    success: bool
    product: dict = {}
    category: str = ""
    platform: str = ""
    pattern_note: str = ""
    variants: list = []

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _load_evolution_state() -> dict:
    state_path = Path(__file__).parent / "modules" / "evolution_state.json"
    if state_path.exists():
        return json.loads(state_path.read_text())
    return {"evolution_log": [], "pattern_feedback": {}}

def _record_evolution(product_url: str, product_title: str, category: str,
                      platform: str, num_variants: int, score: float = None):
    state = _load_evolution_state()
    log = state.setdefault("evolution_log", [])
    log.append({
        "timestamp": str(subprocess.check_output(["date", "+%Y-%m-%d %H:%M:%S"]).decode().strip()),
        "product_url": product_url,
        "product_title": product_title,
        "category": category,
        "platform": platform,
        "num_variants": num_variants,
        "avg_score": score or 6.0,
    })
    log[-100:]  # keep last 100
    state_path = Path(__file__).parent / "modules" / "evolution_state.json"
    state_path.write_text(json.dumps(state, indent=2))

# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "jisi-ad-creative"}

@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    try:
        # ── 1. Extract product data ──────────────────────────────────────────
        if req.mock or not req.url:
            product = {
                "title": f"Demo {req.mock_category or 'Product'}",
                "brand": "Demo Brand",
                "price": "$49.99",
                "description": "High quality product with premium features.",
                "images": [],
            }
            category = req.mock_category or "athletic_leggings"
            pattern_note = f"{category} pattern (demo mode)"
        else:
            extractor = ShopifyExtractor()
            prod = extractor.extract(req.url)
            product = {
                "title": prod.title,
                "brand": prod.brand or "Unknown",
                "price": f"{prod.price.currency} {prod.price.amount}" if prod.price else "N/A",
                "description": prod.description or "",
                "images": prod.images or [],
            }
            category = match_category(product.get("description", "")) or req.mock_category or "general"
            pattern_note = f"Generated for {category}"

        # ── 2. Load competitor patterns ────────────────────────────────────
        patterns = load_competitor_patterns(category)
        if patterns:
            pattern_note = f"Real Competitor Data — {len(patterns.get('ads', []))} ads analyzed"

        # ── 3. Load evolution state ──────────────────────────────────────────
        evo_state = _load_evolution_state()
        top_hooks = []
        pf = evo_state.get("pattern_feedback", {})
        for key, val in pf.items():
            if val.get("category") == category and val.get("platform") == req.platform:
                top_hooks.append((val["hook_type"], val["effectiveness_score"]))
        top_hooks.sort(key=lambda x: -x[1])

        # ── 4. Generate variants ─────────────────────────────────────────────
        gen = AdGenerator()
        if category == "crystal_jewelry" and patterns:
            variants_data = get_crystal_jewelry_variants(
                product["title"],
                product.get("description", ""),
                top_hooks=[h[0] for h in top_hooks[:3]]
            )
        else:
            variants_data = gen.generate(
                product_title=product["title"],
                product_description=product.get("description", ""),
                category=category,
                platform=req.platform,
                num_variants=3,
            )

        # ── 5. Format response ──────────────────────────────────────────────
        variants = []
        for v in variants_data[:3]:
            variants.append({
                "rank": v.get("rank", 1),
                "hook_type": v.get("hook_type", "generic"),
                "hook_text": v.get("hook_text", ""),
                "body_text": v.get("body_text", ""),
                "cta_text": v.get("cta_text", "Shop Now"),
            })

        # ── 6. Record evolution ────────────────────────────────────────────
        if req.url:
            _record_evolution(req.url, product["title"], category, req.platform, len(variants))

        return GenerateResponse(
            success=True,
            product=product,
            category=category,
            platform=req.platform,
            pattern_note=pattern_note,
            variants=variants,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fetch-ads")
def fetch_ads(query: str, country: str = "US"):
    """Fetch competitor ads via Apify CLI."""
    try:
        slug = re.sub(r'[^a-z0-9]+', '_', query.lower()).strip('_')
        out_path = DATA_DIR / f"{slug}_ads.json"

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

        result = subprocess.run(
            ["apify", "call", "whoareyouanas/meta-ad-scraper", "--silent", "--output-dataset"],
            input=run_input,
            capture_output=True,
            text=True,
            timeout=600,
        )

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Apify failed: {result.stderr[:200]}")

        raw = result.stdout.strip()
        if not raw:
            raise HTTPException(status_code=500, detail="Apify returned empty output")

        ads = json.loads(raw)
        out_path.write_text(json.dumps(ads, indent=2))

        return {"success": True, "query": query, "count": len(ads), "saved_to": str(out_path)}

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Apify fetch timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/evolution")
def get_evolution():
    """Get current evolution state."""
    return _load_evolution_state()
