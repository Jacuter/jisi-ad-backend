"""
competitor_insights.py — Real Competitor Ad Data Analyzer
Jisi × Shopify AI Video Ad System

Loads crystal_jewelry_ads.json and extracts:
- Hook patterns (opening lines / emotional triggers)
- CTA patterns
- Emotional appeals (healing, protection, discount urgency)
- Body structure patterns

Used to enrich ad generation with real competitor intelligence.
"""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Optional


DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "crystal_jewelry_ads.json")


@dataclass
class CompetitorPattern:
    """Distilled patterns from real competitor ads."""
    hook_lines: list[str]           # Opening lines extracted from ad bodies
    cta_options: list[str]          # CTA texts used
    emotional_appeals: list[str]    # Emotional/benefit phrases
    discount_patterns: list[str]    # Discount/urgency phrases
    trust_signals: list[str]        # Social proof / trust phrases
    hashtag_themes: list[str]       # Common hashtag themes
    body_templates: list[str]       # Full body examples (top ads)
    source_count: int = 0


def _fix_body(body: str) -> str:
    """
    The JSON file stores emoji as double-escaped unicode (\\uXXXX literal text).
    Decode them to real characters, handling surrogate pairs for emoji.
    """
    # Replace \\uXXXX sequences (literal backslash-u) with real unicode chars
    def replace_escape(m):
        code = int(m.group(1), 16)
        try:
            return chr(code)
        except (ValueError, OverflowError):
            return m.group(0)

    result = re.sub(r'\\u([0-9a-fA-F]{4})', replace_escape, body)
    # Handle surrogate pairs: \uD800-\uDBFF followed by \uDC00-\uDFFF
    def fix_surrogates(s):
        out = []
        i = 0
        chars = list(s)
        while i < len(chars):
            c = chars[i]
            code = ord(c)
            if 0xD800 <= code <= 0xDBFF and i + 1 < len(chars):
                next_code = ord(chars[i+1])
                if 0xDC00 <= next_code <= 0xDFFF:
                    # Combine surrogate pair
                    full = 0x10000 + (code - 0xD800) * 0x400 + (next_code - 0xDC00)
                    out.append(chr(full))
                    i += 2
                    continue
            out.append(c)
            i += 1
        return ''.join(out)

    return fix_surrogates(result)


def _extract_first_line(body: str) -> Optional[str]:
    """Extract the first meaningful line from ad body."""
    lines = [l.strip() for l in body.split('\n') if l.strip()]
    if lines:
        # Strip leading emoji/punctuation for classification
        return lines[0]
    return None


def _classify_hook(line: str) -> str:
    """Classify hook type from first line."""
    low = line.lower()
    if any(w in low for w in ['%', 'off', 'sale', 'discount', 'save']):
        return 'discount_urgency'
    if any(w in low for w in ['heal', 'protect', 'balance', 'energy', 'chakra']):
        return 'healing_benefit'
    if any(w in low for w in ['handmade', 'hand-carved', 'artisan', 'one-of-a-kind']):
        return 'craftsmanship'
    if any(w in low for w in ['last day', 'limited', 'hurry', 'only']):
        return 'scarcity'
    if any(w in low for w in ['rated', 'trusted', 'loved', 'reviews', 'google', 'trustpilot']):
        return 'social_proof'
    if any(w in low for w in ['make real', 'everything is', 'true healing', 'your cells']):
        return 'spiritual_narrative'
    return 'brand_statement'


def load_competitor_patterns(data_path: str = DATA_PATH) -> CompetitorPattern:
    """
    Load and analyze crystal jewelry competitor ads.
    Returns distilled CompetitorPattern with real data.
    """
    with open(data_path, 'r', encoding='utf-8') as f:
        ads = json.load(f)

    hook_lines = []
    cta_options = []
    emotional_appeals = []
    discount_patterns = []
    trust_signals = []
    hashtag_themes = []
    body_templates = []

    # Patterns to extract
    discount_re = re.compile(r'\d+\s*%\s*off|\bsave\b|\bfree\b|\bdiscount\b|\bcode\b', re.IGNORECASE)
    trust_re = re.compile(r'top rated|trusted|google|trustpilot|guarantee|reviews|artisan|handmade|hand.carved|one.of.a.kind', re.IGNORECASE)
    healing_re = re.compile(r'heal|protect|balance|energy|chakra|crystal|gemstone|spiritual|intention|sacred|vibrational', re.IGNORECASE)

    seen_hooks = set()
    seen_ctas = set()

    for ad in ads:
        body = ad.get('body', '')
        if not body:
            continue

        decoded = _fix_body(body)

        # Extract hook (first line)
        first_line = _extract_first_line(decoded)
        if first_line and first_line not in seen_hooks and len(first_line) > 10:
            hook_lines.append(first_line)
            seen_hooks.add(first_line)

        # CTA
        cta = ad.get('ctaText', '').strip()
        if cta and cta not in seen_ctas and cta.lower() not in ('interested',):
            cta_options.append(cta)
            seen_ctas.add(cta)

        # Extract discount phrases
        for m in discount_re.finditer(decoded):
            start = decoded.rfind('\n', 0, m.start())
            end = decoded.find('\n', m.end())
            phrase = decoded[start+1:end if end != -1 else m.end()+40].strip()
            if phrase and len(phrase) > 10 and 'http' not in phrase and phrase not in discount_patterns:
                discount_patterns.append(phrase)

        # Extract trust signals
        for m in trust_re.finditer(decoded):
            # Get the full line containing the match
            start = decoded.rfind('\n', 0, m.start())
            end = decoded.find('\n', m.end())
            phrase = decoded[start+1:end if end != -1 else m.end()+60].strip()
            # Skip URL fragments, hashtag lines, and very short matches
            if (phrase and len(phrase) > 15 and 'http' not in phrase
                    and not phrase.startswith('#') and phrase.count('#') < 3
                    and phrase not in trust_signals):
                trust_signals.append(phrase)

        # Extract healing/emotional appeals
        for m in healing_re.finditer(decoded):
            start = decoded.rfind('\n', 0, m.start())
            end = decoded.find('\n', m.end())
            phrase = decoded[start+1:end if end != -1 else m.end()+60].strip()
            if phrase and len(phrase) > 20 and 'http' not in phrase and phrase not in emotional_appeals:
                emotional_appeals.append(phrase)

        # Hashtags
        tags = re.findall(r'#(\w+)', decoded)
        for t in tags:
            if t not in hashtag_themes:
                hashtag_themes.append(t)

        # Keep top body templates (ads with substantial body text, ecommerce focused)
        if len(decoded) > 100 and ad.get('ctaText', '').lower() in ('shop now', 'shop now', 'learn more', 'get offer'):
            body_templates.append(decoded[:400])

    return CompetitorPattern(
        hook_lines=hook_lines[:15],
        cta_options=list(dict.fromkeys(cta_options))[:6],
        emotional_appeals=list(dict.fromkeys(emotional_appeals))[:20],
        discount_patterns=list(dict.fromkeys(discount_patterns))[:10],
        trust_signals=list(dict.fromkeys(trust_signals))[:15],
        hashtag_themes=hashtag_themes[:30],
        body_templates=body_templates[:5],
        source_count=len(ads),
    )


def build_crystal_jewelry_ad(
    product_title: str,
    product_brand: str,
    product_price: Optional[str],
    product_description: Optional[str],
    hook_type: str,
    patterns: CompetitorPattern,
) -> dict:
    """
    Build a Facebook ad variant for crystal jewelry using real competitor patterns.

    hook_type options:
        'discount_urgency'   — lead with discount/offer
        'healing_benefit'    — lead with crystal healing benefit
        'craftsmanship'      — lead with handmade/artisan angle
        'scarcity'           — lead with limited stock urgency
        'social_proof'       — lead with ratings/trust
        'spiritual_narrative'— lead with deeper spiritual story
    """

    brand = product_brand or "Taliswind"
    title = product_title or "Crystal Bracelet"
    price = product_price or ""

    # --- Hook line ---
    hook_map = {
        'discount_urgency': f"✨ Limited Time: Get {title} — Special Offer Today Only",
        'healing_benefit': f"💎 {title} — Wear Your Intention. Feel the Shift.",
        'craftsmanship': f"🔮 Handcrafted with 4 Powerful Healing Crystals — {title}",
        'scarcity': f"⚠️ Almost Gone — {title} is Selling Fast",
        'social_proof': f"⭐ Top Rated Crystal Jewelry — {title} by {brand}",
        'spiritual_narrative': f"✨ Everything is energy. Your crystals carry it.",
    }
    hook_text = hook_map.get(hook_type, hook_map['healing_benefit'])

    # --- Body copy ---
    # Pull real emotional language from competitor data
    healing_phrase = next(
        (p for p in patterns.emotional_appeals
         if any(w in p.lower() for w in ['balance', 'strength', 'protect', 'energy', 'intention', 'vibrational'])
         and len(p) < 120 and 'http' not in p and p.count('#') < 2),
        "Crystals carry powerful vibrational energy to support your healing journey."
    )
    trust_phrase = next(
        (p for p in patterns.trust_signals
         if any(w in p.lower() for w in ['natural', 'genuine', 'handmade', 'artisan', 'guarantee', 'rated', 'trustpilot'])
         and len(p) < 100 and 'http' not in p and p.count('#') < 2),
        "Natural and genuine gemstones & crystals."
    )

    # Build body
    body_parts = [hook_text, ""]

    if product_description:
        desc_clean = re.sub(r'<[^>]+>', '', product_description)[:180].strip()
        if desc_clean:
            body_parts.append(desc_clean)
            body_parts.append("")

    body_parts.append(f"✨ {healing_phrase[:100]}")
    body_parts.append(f"✅ {trust_phrase[:80]}")
    body_parts.append("🚚 Free Shipping | 30-Day Guarantee")

    if hook_type == 'discount_urgency':
        body_parts.append("")
        body_parts.append("🔥 Limited Stock — Order Now")

    body_parts.append("")
    body_parts.append(f"Shop {title} →")

    body_text = "\n".join(body_parts)

    # --- CTA ---
    cta_map = {
        'discount_urgency': 'Shop Now',
        'healing_benefit': 'Shop Now',
        'craftsmanship': 'Shop Now',
        'scarcity': 'Shop Now',
        'social_proof': 'Shop Now',
        'spiritual_narrative': 'Learn More',
    }
    cta_text = cta_map.get(hook_type, 'Shop Now')

    return {
        'hook_type': hook_type,
        'hook_text': hook_text,
        'body_text': body_text,
        'cta_text': cta_text,
        'data_source': 'real_competitor_ads',
        'competitor_count': patterns.source_count,
    }


def get_crystal_jewelry_variants(
    product_title: str,
    product_brand: str,
    product_price: Optional[str] = None,
    product_description: Optional[str] = None,
    num_variants: int = 3,
    hook_order: Optional[list] = None,
) -> list[dict]:
    """
    Generate N ad variants for crystal jewelry using real competitor data.
    Returns list of variant dicts with hook_type, hook_text, body_text, cta_text.
    hook_order: optional list of hook types in priority order (from evolution engine).
    """
    patterns = load_competitor_patterns()

    default_hooks = [
        'healing_benefit',
        'craftsmanship',
        'discount_urgency',
        'social_proof',
        'spiritual_narrative',
        'scarcity',
    ]
    hook_types = hook_order if hook_order else default_hooks

    variants = []
    for hook_type in hook_types[:num_variants]:
        v = build_crystal_jewelry_ad(
            product_title=product_title,
            product_brand=product_brand,
            product_price=product_price,
            product_description=product_description,
            hook_type=hook_type,
            patterns=patterns,
        )
        variants.append(v)

    return variants


if __name__ == "__main__":
    # Quick test
    patterns = load_competitor_patterns()
    print(f"Loaded {patterns.source_count} competitor ads")
    print(f"Hook lines ({len(patterns.hook_lines)}):")
    for h in patterns.hook_lines[:5]:
        print(f"  - {h[:80]}")
    print(f"\nCTAs: {patterns.cta_options}")
    print(f"\nTrust signals ({len(patterns.trust_signals)}):")
    for t in patterns.trust_signals[:5]:
        print(f"  - {t[:80]}")

    print("\n--- Sample variant (healing_benefit) ---")
    variants = get_crystal_jewelry_variants(
        product_title="Four Crystal Guardian Bracelet",
        product_brand="Taliswind",
        product_price="$92.91",
        product_description="Handmade bracelet with 4 powerful healing crystals for protection and clarity.",
        num_variants=1,
    )
    print(variants[0]['body_text'])
