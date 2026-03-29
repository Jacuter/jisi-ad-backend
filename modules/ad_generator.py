"""
AdGenerator — Generates Ad Variants from Product + Category Patterns
Jisi × Shopify AI Video Ad System

Takes Shopify product data + category winning patterns → generates
ad variants with body text, CTA, hook type, and storyboard suggestions.

Plan A: Uses category patterns as templates
Plan B: Uses real-time scraped patterns (when available)
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from dataclasses import dataclass
from typing import Optional
from category_patterns import (
    CategoryPattern, get_pattern, match_category, 
    get_all_categories, get_pattern_summary, HookFormula
)
from ad_evaluator import AdEvaluator, EvaluationReport
from shopify_extractor import ShopifyExtractor, ProductJSON


@dataclass
class AdVariant:
    """A single generated ad variant"""
    hook_type: str
    hook_text: str
    body_text: str
    cta_text: str
    platform: str  # "meta" or "tiktok"
    storyboard: list[dict]  # [{time, action, subtitle, note}]
    category_pattern_id: str
    evaluation: Optional[EvaluationReport] = None


@dataclass
class GenerationResult:
    """Complete generation result with variants and metadata"""
    product: ProductJSON
    matched_category: str
    platform: str
    variants: list[AdVariant]
    pattern_summary: dict
    generation_note: str = ""


def _fill_template(template: str, **vars) -> str:
    """Fill a template string with variables."""
    text = template
    for k, v in vars.items():
        text = text.replace(f"{{{k}}}", str(v))
    return text


def _build_meta_storyboard(product: ProductJSON, hook_text: str, 
                           body_text: str, cta_text: str,
                           pattern: Optional[CategoryPattern]) -> list[dict]:
    """Build Meta ad storyboard (8-15s, fast-paced)."""
    
    rating_display = ""
    if product.rating:
        rating_display = f"★ {product.rating.value}/5 — {product.rating.count:,}+ Reviews"
    elif product.reviews_sample:
        rating_display = "★ 4.8/5 — Loved by Customers"
    
    return [
        {
            "time": "0:00-0:03",
            "action": "快速切换运动/使用场景 + 产品露出",
            "subtitle": hook_text,
            "note": "前3秒：必须建立信任/紧迫感"
        },
        {
            "time": "0:03-0:08", 
            "action": "产品特写 + 功能展示（emoji列表）",
            "subtitle": _get_feature_list(product, pattern),
            "note": "快速扫描，信息密度高"
        },
        {
            "time": "0:08-0:12",
            "action": "社会证明 + 用户反馈截图",
            "subtitle": rating_display,
            "note": "增强信任，降低购买阻力"
        },
        {
            "time": "0:12+",
            "action": "立即CTA + 紧迫感",
            "subtitle": f"{cta_text} → Free Shipping",
            "note": "最后推动转化"
        },
    ]


def _build_tiktok_storyboard(product: ProductJSON, hook_text: str,
                             body_text: str, cta_text: str,
                             pattern: Optional[CategoryPattern]) -> list[dict]:
    """Build TikTok ad storyboard (15-45s, organic feel)."""
    
    return [
        {
            "time": "0:00-0:03",
            "action": "真实场景开场（不露品牌，不完美 ok）",
            "subtitle": hook_text,
            "note": "前3秒：不能像广告，要像内容"
        },
        {
            "time": "0:03-0:15",
            "action": "产品自然出现 + 真实使用场景",
            "subtitle": body_text[:80] if body_text else f"Meet {product.title}",
            "note": "软性植入，不是硬介绍"
        },
        {
            "time": "0:15-0:20",
            "action": "满足感/情绪释放",
            "subtitle": "真的太好用了... 😍",
            "note": "情绪共鸣，不催购买"
        },
        {
            "time": "0:20+",
            "action": "自然收尾，引导互动",
            "subtitle": "Save this for later | Link in bio",
            "note": "不说Buy Now，给收藏理由"
        },
    ]


def _get_feature_list(product: ProductJSON, pattern: Optional[CategoryPattern]) -> str:
    """Extract a feature list string."""
    features = []
    if pattern:
        features = pattern.language.common_phrases[:4]
    if not features and product.tags:
        features = [t for t in product.tags[:4] if len(t) < 20]
    if not features:
        features = [product.title] if product.title else []
    
    return " | ".join([f"✅ {f}" for f in features[:3]])


class AdGenerator:
    """
    Generates conversion-optimized ad variants from product data.
    
    Usage:
        gen = AdGenerator()
        result = gen.generate(product_url="https://...", platform="meta")
        for variant in result.variants:
            print(variant.body_text, variant.evaluation.overall_score)
    """
    
    def __init__(self):
        self.extractor = ShopifyExtractor()
        self.evaluator = AdEvaluator()
    
    def generate(self, product_url: str, platform: str = "meta",
                 num_variants: int = 3, 
                 category_hint: Optional[str] = None) -> GenerationResult:
        """
        Generate ad variants for a product.
        
        Args:
            product_url: Shopify product URL
            platform: "meta" or "tiktok" 
            num_variants: Number of variants to generate (default: 3)
            category_hint: Force a category override (optional)
        
        Returns:
            GenerationResult with variants and metadata
        """
        # Step 1: Extract product data
        product = self.extractor.extract(product_url)
        if not product or not product.title:
            raise ValueError(f"Failed to extract product from {product_url}")
        
        # Step 2: Match category
        if category_hint:
            matched_category = category_hint
        else:
            matched_category = match_category(
                product.title,
                product.tags,
                product.description or ""
            ) or "general"
        
        # Step 3: Get pattern
        pattern = get_pattern(matched_category, platform)
        if not pattern:
            matched_category = "general"
            pattern = None
        
        # Step 4: Generate variants
        variants = self._generate_variants(product, pattern, platform, num_variants)
        
        # Step 5: Evaluate each variant
        for variant in variants:
            report = self.evaluator.evaluate(
                variant_body_text=variant.body_text,
                variant_cta=variant.cta_text,
                hook_type_used=variant.hook_type,
                category=matched_category,
                winning_pattern=None
            )
            variant.evaluation = report
        
        # Sort by score
        variants.sort(key=lambda v: v.evaluation.overall_score if v.evaluation else 0, reverse=True)
        
        # Step 6: Get pattern summary
        summary = get_pattern_summary(matched_category) or {}
        if pattern:
            pattern_note = f"Pattern: {pattern.display_name} ({platform})"
        else:
            pattern_note = "Using general patterns (category not matched)"
        
        return GenerationResult(
            product=product,
            matched_category=matched_category,
            platform=platform,
            variants=variants,
            pattern_summary=summary,
            generation_note=pattern_note
        )
    
    def _generate_variants(self, product: ProductJSON, pattern: Optional[CategoryPattern],
                          platform: str, num_variants: int) -> list[AdVariant]:
        """Generate ad variants based on product and pattern."""
        
        if pattern:
            return self._generate_from_pattern(product, pattern, platform, num_variants)
        else:
            return self._generate_generic(product, platform, num_variants)
    
    def _generate_from_pattern(self, product: ProductJSON, pattern: CategoryPattern,
                               platform: str, num_variants: int) -> list[AdVariant]:
        """Generate variants using category pattern hooks."""
        
        brand = product.brand or "This brand"
        title = product.title or "product"
        price = f"${product.price.amount}" if product.price else ""
        
        variants = []
        for i, hook in enumerate(pattern.hooks[:num_variants]):
            rating_val = f"{product.rating.value}" if product.rating else "4.8/5"
            hook_text = _fill_template(
                hook.template,
                brand=brand, title=title, price=price, N="500,000+",
                X="30", Problem="Sagging & Riding Up",
                Benefit="Protection & Clarity",
                Time="3 months",
                Nutrient="Vitamin D",
                Product=title,
                Competitor="AirPods",
                Feature="Active Noise Cancellation",
                Scenario="Working from home",
                Pet="dog",
                Step="cleanser",
                Brand=brand,
                Result="Visible Results",
                Rating=rating_val,
            )
            
            body_text = self._build_body(product, pattern, hook)
            cta_text = pattern.cta.primary if platform == "meta" else "Link in bio"
            
            if platform == "meta":
                storyboard = _build_meta_storyboard(product, hook_text, body_text, cta_text, pattern)
            else:
                storyboard = _build_tiktok_storyboard(product, hook_text, body_text, cta_text, pattern)
            
            variants.append(AdVariant(
                hook_type=hook.type,
                hook_text=hook_text,
                body_text=body_text,
                cta_text=cta_text,
                platform=platform,
                storyboard=storyboard,
                category_pattern_id=f"{pattern.category}_{platform}"
            ))
        
        return variants
    
    def _build_body(self, product: ProductJSON, pattern: CategoryPattern, 
                   hook: HookFormula) -> str:
        """Build body copy based on pattern."""
        
        parts = []
        
        # Use product description
        if product.description:
            desc = product.description.replace("<", "").replace(">", "")[:150]
            if desc:
                parts.append(desc)
        
        # Add pattern-specific language
        if pattern.language.common_phrases:
            parts.append(" | ".join(pattern.language.common_phrases[:2]))
        
        return " ".join(parts) if parts else f"Premium quality {product.title}"
    
    def _generate_generic(self, product: ProductJSON, platform: str,
                         num_variants: int) -> list[AdVariant]:
        """Generate generic variants without category pattern."""
        
        hook_specs = [
            ("numeric", "Over 100,000 Sold — Find Out Why"),
            ("problem_fix", f"Say Goodbye to {product.title} Problems"),
            ("immediate_offer", f"🔥 Limited Time: {product.title} — Shop Now"),
        ]
        
        cta = "Shop Now" if platform == "meta" else "Link in bio"
        variants = []
        
        for i, (hook_type, hook_text) in enumerate(hook_specs[:num_variants]):
            body = f"{product.brand or ''} {product.title}".strip()
            storyboard = _build_meta_storyboard(product, hook_text, body, cta, None) if platform == "meta" \
                else _build_tiktok_storyboard(product, hook_text, body, cta, None)
            
            variants.append(AdVariant(
                hook_type=hook_type,
                hook_text=hook_text,
                body_text=body,
                cta_text=cta,
                platform=platform,
                storyboard=storyboard,
                category_pattern_id="general"
            ))
        
        return variants
