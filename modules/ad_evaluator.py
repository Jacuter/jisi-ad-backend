"""
Ad Evaluator — Module C (Evaluation Engine)
Jisi × Shopify AI Video Ad System

Rule-based evaluation engine for generated ad variants.
No LLM required — all rules are deterministic and interpretable.

Design Philosophy:
- Fast: Real-time scoring (no API calls needed)
- Reproducible: Same input → same score every time
- Interpretable: Shows exactly why an ad scored the way it did
- Trainable: Rules can be updated as we learn new patterns

See SPEC.md Section 4 for full evaluation framework.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Scoring Constants
# ---------------------------------------------------------------------------

# Hook type scores (1-10 scale)
HOOK_SCORES = {
    "numeric_social_proof": 9.0,   # "Over 1.3M sold"
    "immediate_offer": 8.5,         # "30% OFF today only"
    "problem_fix": 7.5,            # "Tired of X? Meet Y"
    "influencer_social": 7.0,      # "As seen on TikTok"
    "personal_quote": 7.0,         # User review quote
    "differentiation": 7.0,        # "Built different"
    "question": 5.5,               # "Is this the..."
    "statement": 3.0,              # No hook, just a statement
    "unknown": 5.0,
}

# Hook pattern regexes (order matters — more specific patterns first)
HOOK_PATTERNS = [
    # numeric_social_proof
    (
        "numeric_social_proof",
        re.compile(r"(over|more than|>\s*)\s*\d+[mkb]", re.I),
    ),
    (
        "numeric_social_proof",
        re.compile(r"\d+\s*(million|billion|thousand)\s+(sold|customers|women|men|people)", re.I),
    ),
    (
        "numeric_social_proof",
        re.compile(r"#\d+\s*(people|customers|women|men)", re.I),
    ),
    (
        "numeric_social_proof",
        re.compile(r"bestseller", re.I),
    ),
    # immediate_offer
    (
        "immediate_offer",
        re.compile(r"\d+%\s*off", re.I),
    ),
    (
        "immediate_offer",
        re.compile(r"flash\s+sale", re.I),
    ),
    (
        "immediate_offer",
        re.compile(r"limited\s+time", re.I),
    ),
    (
        "immediate_offer",
        re.compile(r"while\s+(supplies|last|stock)", re.I),
    ),
    (
        "immediate_offer",
        re.compile(r"(ends?|expires?)\s+\w+\s*\d+", re.I),
    ),
    # problem_fix
    (
        "problem_fix",
        re.compile(r"tired\s+of", re.I),
    ),
    (
        "problem_fix",
        re.compile(r"sick\s+of", re.I),
    ),
    (
        "problem_fix",
        re.compile(r"say\s+goodbye\s+to", re.I),
    ),
    (
        "problem_fix",
        re.compile(r"finally\s+(a|an|the)", re.I),
    ),
    (
        "problem_fix",
        re.compile(r"(the\s+)?secret\s+to", re.I),
    ),
    (
        "problem_fix",
        re.compile(r"this\s+changed\s+my", re.I),
    ),
    # influencer_social
    (
        "influencer_social",
        re.compile(r"(tiktok|instagram|youtube)\s*(made|says|said|recommends)", re.I),
    ),
    (
        "influencer_social",
        re.compile(r"(creator|influencer|koll?)\s", re.I),
    ),
    (
        "influencer_social",
        re.compile(r"(people|followers|women|men)\s+(trust|love|buy)", re.I),
    ),
    # personal_quote
    (
        "personal_quote",
        re.compile(r'"[^"]{20,150}"'),  # Quoted text 20-150 chars
    ),
    (
        "personal_quote",
        re.compile(r"-\s+[A-Z][a-z]+\s+[A-Z]\.", re.I),  # "- Name L."
    ),
    # differentiation
    (
        "differentiation",
        re.compile(r"built?\s+(different|tough|strong)", re.I),
    ),
    (
        "differentiation",
        re.compile(r"designed?\s+by\s+women", re.I),
    ),
    (
        "differentiation",
        re.compile(r"family-owned", re.I),
    ),
    # question
    (
        "question",
        re.compile(r"^\?", re.M),
    ),
    (
        "question",
        re.compile(r"^(is\s+this|is\s+there|do\s+you|what\s+if|how\s+do)", re.I),
    ),
]

# CTA scores
CTA_SCORES = {
    "shop_now": 9.0,
    "get_it_now": 8.5,
    "learn_more": 6.0,
    "get_your_code": 7.0,
    "get_started": 7.5,
    "try_it_now": 7.5,
    "order_now": 8.0,
    "buy_now": 8.5,
    "see_price": 5.0,
    "check_it_out": 5.5,
    "tap_for_deal": 6.5,
    "default": 5.0,
}

CTA_PATTERNS = [
    ("shop_now", re.compile(r"shop\s+now", re.I)),
    ("buy_now", re.compile(r"buy\s+now", re.I)),
    ("get_it_now", re.compile(r"get\s+it\s+now", re.I)),
    ("order_now", re.compile(r"order\s+now", re.I)),
    ("try_it_now", re.compile(r"try\s+it\s+now", re.I)),
    ("get_started", re.compile(r"get\s+started", re.I)),
    ("get_your_code", re.compile(r"get\s+your\s+code", re.I)),
    ("learn_more", re.compile(r"learn\s+more", re.I)),
    ("see_price", re.compile(r"see\s+(the\s+)?price", re.I)),
    ("check_it_out", re.compile(r"check\s+(it\s+out|details)", re.I)),
    ("tap_for_deal", re.compile(r"tap\s+for\s+(deal|more)", re.I)),
]

# Evaluation dimension weights (from SPEC.md Section 4.2)
DIMENSION_WEIGHTS = {
    "hook_strength": 0.35,
    "category_match": 0.25,
    "body_relevance": 0.20,
    "cta_clarity": 0.15,
    "technical_quality": 0.05,
}


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class EvaluationScores:
    """Scoring output for a single ad variant."""
    hook_strength: float = 0.0
    category_match: float = 0.0
    body_relevance: float = 0.0
    cta_clarity: float = 0.0
    technical_quality: float = 0.0
    overall: float = 0.0

    def weighted_sum(self) -> float:
        return (
            self.hook_strength * DIMENSION_WEIGHTS["hook_strength"]
            + self.category_match * DIMENSION_WEIGHTS["category_match"]
            + self.body_relevance * DIMENSION_WEIGHTS["body_relevance"]
            + self.cta_clarity * DIMENSION_WEIGHTS["cta_clarity"]
            + self.technical_quality * DIMENSION_WEIGHTS["technical_quality"]
        )

@dataclass
class EvaluationBreakdown:
    """Detailed breakdown for each dimension."""
    hook_strength: dict = field(default_factory=dict)
    category_match: dict = field(default_factory=dict)
    body_relevance: dict = field(default_factory=dict)
    cta_clarity: dict = field(default_factory=dict)
    technical_quality: dict = field(default_factory=dict)

@dataclass
class EvaluationReport:
    """Complete evaluation output."""
    variant_id: str
    overall_score: float
    scores: EvaluationScores
    breakdown: EvaluationBreakdown
    recommendations: list[str] = field(default_factory=list)
    percentile: Optional[int] = None  # What percentile this ad is in

    def summary(self) -> str:
        return (
            f"Variant: {self.variant_id}\n"
            f"Overall: {self.overall_score:.1f}/10\n"
            f"Hook: {self.scores.hook_strength:.1f} | "
            f"Category: {self.scores.category_match:.1f} | "
            f"Body: {self.scores.body_relevance:.1f} | "
            f"CTA: {self.scores.cta_clarity:.1f} | "
            f"Tech: {self.scores.technical_quality:.1f}"
        )


# ---------------------------------------------------------------------------
# Main Evaluator
# ---------------------------------------------------------------------------

class AdEvaluator:
    """
    Rule-based evaluation engine for video ad variants.
    No LLM required — all rules are deterministic.
    """

    def __init__(self):
        self.hook_cache: dict = {}  # cache for performance

    def evaluate(
        self,
        variant_body_text: str,
        variant_cta: str,
        hook_type_used: str,
        category: str,
        winning_pattern: Optional[dict] = None,
    ) -> EvaluationReport:
        """
        Evaluate a single ad variant.

        Args:
            variant_body_text: The ad body copy (first 500 chars is sufficient)
            variant_cta: The call-to-action text
            hook_type_used: The hook type this variant used (e.g., "numeric_social_proof")
            category: Product category (e.g., "athletic_leggings")
            winning_pattern: Optional winning pattern rules (from pattern store)

        Returns:
            EvaluationReport with scores and breakdown
        """
        variant_id = f"{category}_{hook_type_used}"

        # ---- Score each dimension ----
        hook_score, hook_breakdown = self._score_hook(variant_body_text, hook_type_used, winning_pattern)
        category_score, category_breakdown = self._score_category_match(
            hook_type_used, category, winning_pattern
        )
        body_score, body_breakdown = self._score_body_relevance(variant_body_text, winning_pattern)
        cta_score, cta_breakdown = self._score_cta(variant_cta, winning_pattern)
        tech_score, tech_breakdown = self._score_technical(variant_body_text, variant_cta)

        scores = EvaluationScores(
            hook_strength=round(hook_score, 2),
            category_match=round(category_score, 2),
            body_relevance=round(body_score, 2),
            cta_clarity=round(cta_score, 2),
            technical_quality=round(tech_score, 2),
        )
        scores.overall = round(scores.weighted_sum(), 2)

        breakdown = EvaluationBreakdown(
            hook_strength=hook_breakdown,
            category_match=category_breakdown,
            body_relevance=body_breakdown,
            cta_clarity=cta_breakdown,
            technical_quality=tech_breakdown,
        )

        # ---- Generate recommendations ----
        recommendations = self._generate_recommendations(scores, breakdown, hook_type_used)

        return EvaluationReport(
            variant_id=variant_id,
            overall_score=scores.overall,
            scores=scores,
            breakdown=breakdown,
            recommendations=recommendations,
        )

    def evaluate_batch(
        self,
        variants: list[dict],
        category: str,
        winning_pattern: Optional[dict] = None,
    ) -> list[EvaluationReport]:
        """
        Evaluate multiple ad variants and return sorted by overall score.
        """
        reports = []
        for v in variants:
            report = self.evaluate(
                variant_body_text=v.get("body_text", ""),
                variant_cta=v.get("cta_text", ""),
                hook_type_used=v.get("hook_type_used", "unknown"),
                category=category,
                winning_pattern=winning_pattern,
            )
            reports.append(report)

        # Sort descending by overall score
        reports.sort(key=lambda r: r.overall_score, reverse=True)

        # Assign percentile ranks
        if len(reports) > 1:
            for i, r in enumerate(reports):
                r.percentile = int(100 * (len(reports) - i - 1) / (len(reports) - 1))

        return reports

    # -------------------------------------------------------------------------
    # Dimension Scorers
    # -------------------------------------------------------------------------

    def _score_hook(
        self,
        text: str,
        claimed_hook_type: str,
        winning_pattern: Optional[dict],
    ) -> tuple[float, dict]:
        """Score the hook strength (dimension: hook_strength, weight: 35%)"""
        text_lower = text.lower().strip()
        text_first_200 = text_lower[:200]

        # Detect hook type from text
        detected_hook_type, matched_phrase = self._classify_hook(text_first_200)

        base_score = HOOK_SCORES.get(detected_hook_type, HOOK_SCORES["unknown"])

        # Bonus: matches claimed hook type
        if detected_hook_type == claimed_hook_type:
            base_score = min(10.0, base_score + 0.5)

        # Bonus: matches winning pattern for this category
        if winning_pattern:
            top_hook = winning_pattern.get("rules", {}).get("hook_formula", {}).get("type", "")
            if detected_hook_type == top_hook:
                base_score = min(10.0, base_score + 1.0)

        # Penalty: hook type doesn't match claimed
        if detected_hook_type != claimed_hook_type and claimed_hook_type != "unknown":
            base_score = max(1.0, base_score - 1.0)

        breakdown = {
            "detected_hook_type": detected_hook_type,
            "claimed_hook_type": claimed_hook_type,
            "matched_phrase": matched_phrase[:80] if matched_phrase else "",
            "base_score": base_score,
            "score": round(base_score, 2),
        }

        return round(base_score, 2), breakdown

    def _score_category_match(
        self,
        hook_type: str,
        category: str,
        winning_pattern: Optional[dict],
    ) -> tuple[float, dict]:
        """Score how well this ad matches category norms (dimension: category_match, weight: 25%)"""
        if not winning_pattern:
            # No pattern data — use generic category defaults
            return 7.0, {"note": "No winning pattern, used default score"}

        rules = winning_pattern.get("rules", {})

        # Check hook type match
        top_hook = rules.get("hook_formula", {}).get("type", "")
        hook_matches_top = hook_type == top_hook

        # Check video duration (if provided)
        duration_ok = True  # Would check against optimal_duration_range if available

        # Score
        score = 7.0
        if hook_matches_top:
            score += 1.5
        else:
            score -= 1.0  # Penalty for not matching top hook

        score = max(1.0, min(10.0, score))

        breakdown = {
            "category": category,
            "top_hook_for_category": top_hook,
            "hook_matches_top": hook_matches_top,
            "score": round(score, 2),
        }

        return round(score, 2), breakdown

    def _score_body_relevance(
        self,
        text: str,
        winning_pattern: Optional[dict],
    ) -> tuple[float, dict]:
        """Score body copy relevance and completeness (dimension: body_relevance, weight: 20%)"""
        if not text:
            return 1.0, {"score": 1.0, "reason": "Empty body text"}

        text_lower = text.lower()

        # Check for feature listing (emoji bullets or checkmarks)
        has_feature_list = bool(
            re.search(r"[✅✔✓💪🍑📦🏆⭐❤👏🛡️]", text) or
            re.search(r"(features|benefits|includes)\s*:", text_lower)
        )

        # Check for social proof elements
        has_social_proof = bool(
            re.search(r"(women|men|people|customers)\s+(trust|love|buy| wear)", text_lower) or
            re.search(r"★{2,}", text) or
            re.search(r"reviews?:?\s*\d+", text_lower)
        )

        # Check for brand mention
        has_brand = bool(re.search(r"(brand|company|family-owned|designed in)", text_lower))

        # Length check
        word_count = len(text.split())
        good_length = 30 <= word_count <= 200

        # Score
        score = 6.0
        if has_feature_list:
            score += 1.5
        if has_social_proof:
            score += 1.0
        if good_length:
            score += 0.5
        if has_brand:
            score += 0.5

        score = max(1.0, min(10.0, score))

        breakdown = {
            "word_count": word_count,
            "has_feature_list": has_feature_list,
            "has_social_proof": has_social_proof,
            "has_brand_mention": has_brand,
            "good_length": good_length,
            "score": round(score, 2),
        }

        return round(score, 2), breakdown

    def _score_cta(
        self,
        cta_text: str,
        winning_pattern: Optional[dict],
    ) -> tuple[float, dict]:
        """Score CTA clarity and urgency (dimension: cta_clarity, weight: 15%)"""
        if not cta_text:
            return 2.0, {"score": 2.0, "reason": "No CTA text"}

        cta_lower = cta_text.lower().strip()

        # Detect CTA type
        detected_type = "default"
        for cta_type, pattern in CTA_PATTERNS:
            if pattern.search(cta_lower):
                detected_type = cta_type
                break

        base_score = CTA_SCORES.get(detected_type, CTA_SCORES["default"])

        # Urgency modifiers
        urgency_bonus = 0.0
        if any(kw in cta_lower for kw in ["today", "now", "limited", "last", " hurry"]):
            urgency_bonus = 1.0

        score = min(10.0, base_score + urgency_bonus)

        # Check against winning pattern CTA
        if winning_pattern:
            top_cta = winning_pattern.get("rules", {}).get("cta_formula", {}).get("primary", "")
            if top_cta and top_cta.lower() in cta_lower:
                score = min(10.0, score + 0.5)

        breakdown = {
            "cta_detected": cta_text[:50],
            "cta_type": detected_type,
            "urgency_bonus": urgency_bonus,
            "score": round(score, 2),
        }

        return round(score, 2), breakdown

    def _score_technical(
        self,
        body_text: str,
        cta_text: str,
    ) -> tuple[float, dict]:
        """
        Score technical quality factors (dimension: technical_quality, weight: 5%).
        These are non-content factors like emoji usage, formatting.
        """
        if not body_text:
            return 5.0, {"score": 5.0}

        score = 7.0

        # Has emoji in body
        has_emoji = bool(re.search(r"[\U0001F300-\U0001F9FF]", body_text))
        if has_emoji:
            score += 0.5

        # Has numbers/prices (specificity)
        has_numbers = bool(re.search(r"\$\d+|\d+%\s*off|\d+\s*(women|men|people|customers)", body_text.lower()))
        if has_numbers:
            score += 0.5

        # CTA is present and clear
        has_cta = bool(cta_text and len(cta_text.strip()) > 0)
        if not has_cta:
            score -= 2.0

        score = max(1.0, min(10.0, score))

        breakdown = {
            "has_emoji": has_emoji,
            "has_numbers": has_numbers,
            "has_cta": has_cta,
            "score": round(score, 2),
        }

        return round(score, 2), breakdown

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def _classify_hook(self, text: str) -> tuple[str, str]:
        """
        Classify the hook type from ad body text.
        Returns (hook_type, matched_phrase).
        """
        text_lower = text.lower()

        for hook_type, pattern in HOOK_PATTERNS:
            match = pattern.search(text_lower)
            if match:
                return hook_type, match.group(0)

        # Check for quoted text (personal_quote)
        quote_match = re.search(r'"([^"]{20,150})"', text)
        if quote_match:
            return "personal_quote", quote_match.group(0)[:80]

        return "unknown", ""

    def _generate_recommendations(
        self,
        scores: EvaluationScores,
        breakdown: EvaluationBreakdown,
        hook_type_used: str,
    ) -> list[str]:
        """Generate actionable recommendations based on scores."""
        recs = []

        if scores.hook_strength < 7.0:
            hook_recs = {
                "numeric_social_proof": "Add a number-driven social proof hook (e.g., 'Over 1M sold')",
                "problem_fix": "Start with a pain point → solution hook ('Tired of X? Meet Y')",
                "immediate_offer": "Add a clear urgency hook (e.g., '30% OFF — today only')",
                "influencer_social": "Add a platform/social hook ('As seen on TikTok')",
                "personal_quote": "Open with a customer quote in quotes",
                "differentiation": "Lead with your unique positioning",
                "question": "Replace rhetorical question with a stronger hook type",
                "statement": "Add a hook — don't start with a plain statement",
                "unknown": "Add a clear attention-grabbing hook in the first 3 seconds",
            }
            rec = hook_recs.get(hook_type_used, hook_recs["unknown"])
            recs.append(f"Hook ({scores.hook_strength}/10): {rec}")

        if scores.category_match < 7.0:
            recs.append(
                f"Category match ({scores.category_match}/10): "
                "Adjust hook type to match your category's winning pattern"
            )

        if scores.body_relevance < 7.0:
            recs.append(
                f"Body relevance ({scores.body_relevance}/10): "
                "Add emoji feature lists (✅Pockets 🍑Squat Proof) and social proof"
            )

        if scores.cta_clarity < 7.0:
            recs.append(
                f"CTA ({scores.cta_clarity}/10): "
                "Use 'Shop Now' or 'Get it now' — most common high-performing CTA"
            )

        if scores.technical_quality < 7.0:
            recs.append(
                f"Technical quality ({scores.technical_quality}/10): "
                "Add specific numbers/prices and ensure CTA is present"
            )

        if not recs:
            recs.append("All dimensions look strong — no critical improvements needed.")

        return recs


# ---------------------------------------------------------------------------
# CLI Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    evaluator = AdEvaluator()

    # Real ad samples from our Facebook Ad Library research
    test_ads = [
        {
            "id": "ad_1_gymshark",
            "body_text": "Calling all sprinkle lovers!! These leggings were made for you. Over 1.3 Million Leggings Sold ✅ Pockets 🍑 Squat Proof 💦 Sweat Proof ❌ Never See Through 💥 Durable ❤️ Family-Owned 👏 Free Exchanges 📨 Shipped From Massachusetts, USA",
            "cta_text": "Shop Now",
            "hook_type_used": "numeric_social_proof",
        },
        {
            "id": "ad_2_flashsale",
            "body_text": "FLASH SALE on NEW women's athletic leggings. For a limited time 30% OFF! While supplies last. New items only.",
            "cta_text": "详细了解",
            "hook_type_used": "immediate_offer",
        },
        {
            "id": "ad_3_weak",
            "body_text": "We make great leggings. Check them out.",
            "cta_text": "Learn More",
            "hook_type_used": "statement",
        },
        {
            "id": "ad_4_tiktok",
            "body_text": "FOLLOW + DROP ANY WORD IF YOU WANT 🔗 DETAILS! 14 late-night scrolling purchases that have exceeded all expectations 🤭 which one would you grab first?!",
            "cta_text": "Shop Now",
            "hook_type_used": "influencer_social",
        },
    ]

    print("=" * 70)
    print("Ad Evaluator — Test Suite")
    print("=" * 70)

    reports = evaluator.evaluate_batch(
        test_ads,
        category="athletic_leggings",
        winning_pattern=None,  # No pattern in demo
    )

    for i, report in enumerate(reports):
        print(f"\n--- Rank #{i+1}: {report.variant_id} ---")
        print(f"Overall: {report.overall_score:.1f}/10")
        print(f"  Hook strength:     {report.scores.hook_strength:.1f}/10")
        print(f"  Category match:     {report.scores.category_match:.1f}/10")
        print(f"  Body relevance:     {report.scores.body_relevance:.1f}/10")
        print(f"  CTA clarity:       {report.scores.cta_clarity:.1f}/10")
        print(f"  Technical quality:  {report.scores.technical_quality:.1f}/10")
        if report.recommendations:
            print("  Recommendations:")
            for rec in report.recommendations:
                print(f"    → {rec}")

    print("\n" + "=" * 70)
    print("Done.")
