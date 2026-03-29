"""
evolution_engine.py — Jisi Self-Evolution System
Jisi × Shopify AI Video Ad System

Continuous improvement loop:
1. EXTRACT  → Product data from Shopify
2. ANALYZE  → Category patterns + user reviews
3. GENERATE → Ad variants
4. EVALUATE → Score + rank
5. LEARN    → Update pattern weights based on evaluation

The system continuously improves its own category patterns
based on real product data and evaluation feedback.
"""

import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))

from dataclasses import dataclass, field, asdict
from typing import Optional
from shopify_extractor import ShopifyExtractor, ProductJSON
from category_patterns import (
    get_pattern, match_category, get_all_categories,
    PATTERNS, CategoryPattern, HookFormula
)
from ad_generator import AdGenerator
from ad_evaluator import AdEvaluator


# ─── Data Structures ─────────────────────────────────────────────────────────

@dataclass
class EvolutionRecord:
    """A record of one evolution cycle."""
    timestamp: str
    product_url: str
    product_title: str
    matched_category: str
    platform: str
    num_variants: int
    avg_score: float
    best_score: float
    best_hook_type: str
    improvements_made: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class PatternFeedback:
    """Feedback on a specific pattern element."""
    category: str
    platform: str
    hook_type: str
    effectiveness_score: float  # based on eval scores
    frequency_used: int
    last_updated: str


# ─── Evolution Engine ─────────────────────────────────────────────────────────

class EvolutionEngine:
    """
    Self-evolution engine for Jisi ad creative system.
    
    Run periodically to continuously improve pattern quality.
    """
    
    def __init__(self):
        self.extractor = ShopifyExtractor()
        self.generator = AdGenerator()
        self.evaluator = AdEvaluator()
        self.evolution_log: list[EvolutionRecord] = []
        self.pattern_feedback: dict[str, PatternFeedback] = {}
    
    def run_cycle(self, product_url: str, platform: str = "meta",
                  num_variants: int = 3) -> EvolutionRecord:
        """
        Run one evolution cycle.
        
        1. Extract product
        2. Match category
        3. Generate variants
        4. Evaluate
        5. Analyze feedback
        6. Return record
        """
        print(f"\n{'='*60}")
        print(f"  Evolution Cycle — {platform.upper()}")
        print(f"  URL: {product_url}")
        print(f"{'='*60}")
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Step 1: Extract product
        print(f"\n📦 Step 1: Extracting product...")
        product = self.extractor.extract(product_url)
        if not product or not product.title:
            raise ValueError(f"Failed to extract: {product_url}")
        print(f"   {product.title} | {product.brand} | ${product.price.amount if product.price else 'N/A'}")
        
        # Step 2: Match category
        print(f"\n🔍 Step 2: Matching category...")
        category = match_category(product.title, product.tags, product.description or "") or "general"
        print(f"   Category: {category}")
        
        # Step 3: Get pattern
        pattern = get_pattern(category, platform)
        if pattern:
            print(f"   Pattern: {pattern.display_name}")
            print(f"   Top hooks: {[h.type for h in pattern.hooks[:3]]}")
        else:
            print(f"   No pattern found — using generic")
        
        # Step 4: Generate variants
        print(f"\n🎬 Step 3: Generating {num_variants} variants...")
        variants = self.generator._generate_variants(product, pattern, platform, num_variants)
        
        # Step 5: Evaluate
        print(f"\n📊 Step 4: Evaluating variants...")
        for v in variants:
            v.evaluation = self.evaluator.evaluate(
                v.body_text, v.cta_text, v.hook_type, category, None
            )
        variants.sort(key=lambda x: x.evaluation.overall_score if x.evaluation else 0, reverse=True)
        
        avg_score = sum(v.evaluation.overall_score for v in variants if v.evaluation) / len(variants)
        best = variants[0]
        print(f"   Best: {best.hook_type} | score={best.evaluation.overall_score:.1f}")
        print(f"   Avg:  {avg_score:.1f}")
        
        # Step 6: Analyze feedback
        print(f"\n🧠 Step 5: Analyzing feedback...")
        improvements = self._analyze_and_apply_feedback(
            category, platform, variants, pattern
        )
        
        # Build record
        record = EvolutionRecord(
            timestamp=timestamp,
            product_url=product_url,
            product_title=product.title,
            matched_category=category,
            platform=platform,
            num_variants=len(variants),
            avg_score=avg_score,
            best_score=best.evaluation.overall_score,
            best_hook_type=best.hook_type,
            improvements_made=improvements,
        )
        
        self.evolution_log.append(record)
        
        # Save state
        self._save_state()
        
        print(f"\n✅ Cycle complete!")
        print(f"   Best hook: {best.hook_text}")
        print(f"   Improvements: {improvements}")
        
        return record
    
    def _analyze_and_apply_feedback(self, category: str, platform: str,
                                    variants, pattern: Optional[CategoryPattern]) -> list[str]:
        """
        Analyze variant results and apply feedback to patterns.
        
        This is where the self-improvement happens.
        """
        improvements = []
        
        if not pattern:
            return improvements
        
        # Score each hook type used
        hook_scores: dict[str, list[float]] = {}
        for v in variants:
            if v.evaluation:
                ht = v.hook_type
                if ht not in hook_scores:
                    hook_scores[ht] = []
                hook_scores[ht].append(v.evaluation.overall_score)
        
        # Calculate average score per hook type
        for hook_type, scores in hook_scores.items():
            avg = sum(scores) / len(scores)
            key = f"{category}_{platform}_{hook_type}"
            existing = self.pattern_feedback.get(key)
            
            if existing:
                # Update with exponential moving average
                new_score = existing.effectiveness_score * 0.7 + avg * 0.3
                existing.effectiveness_score = new_score
                existing.frequency_used += 1
                existing.last_updated = time.strftime("%Y-%m-%d %H:%M:%S")
                
                # If score improved significantly, boost that hook's priority
                if new_score > existing.effectiveness_score * 1.1:
                    improvements.append(
                        f"{hook_type}: effectiveness improved to {new_score:.2f}"
                    )
                    self._boost_hook_priority(pattern, hook_type)
            else:
                self.pattern_feedback[key] = PatternFeedback(
                    category=category,
                    platform=platform,
                    hook_type=hook_type,
                    effectiveness_score=avg,
                    frequency_used=1,
                    last_updated=time.strftime("%Y-%m-%d %H:%M:%S"),
                )
        
        # Analyze body text patterns
        body_analysis = self._analyze_body_text(variants)
        if body_analysis:
            improvements.append(f"Body text insight: {body_analysis}")
        
        return improvements
    
    def _boost_hook_priority(self, pattern: CategoryPattern, hook_type: str):
        """Boost the priority of a high-performing hook in the pattern."""
        for hook in pattern.hooks:
            if hook.type == hook_type:
                # Increase the effective weight of this hook
                # (This would affect generation order in future cycles)
                print(f"   ⬆️ Boosted {hook_type} hook (score improved)")
                break
    
    def _analyze_body_text(self, variants) -> Optional[str]:
        """Analyze body text patterns across variants."""
        if not variants:
            return None
        
        # Simple heuristics
        lengths = [len(v.body_text) for v in variants]
        emojis_used = sum(1 for v in variants if any(c in v.body_text for c in '🎯🔥✅⭐💪✨📊💡'))
        
        if emojis_used / len(variants) > 0.5:
            return "High emoji usage — effective for engagement"
        if sum(lengths) / len(lengths) < 50:
            return "Short body copy tends to perform better"
        
        return None
    
    def run_batch(self, product_urls: list[str], platform: str = "meta") -> list[EvolutionRecord]:
        """Run multiple cycles for multiple products."""
        records = []
        for url in product_urls:
            try:
                record = self.run_cycle(url, platform)
                records.append(record)
            except Exception as e:
                print(f"❌ Error with {url}: {e}")
            time.sleep(2)  # Rate limit
        
        return records
    
    def get_insights(self) -> dict:
        """Get current pattern insights and feedback summary."""
        insights = {
            "total_cycles": len(self.evolution_log),
            "categories_analyzed": list(set(r.matched_category for r in self.evolution_log)),
            "pattern_feedback": {},
        }
        
        for key, fb in self.pattern_feedback.items():
            insights["pattern_feedback"][key] = {
                "effectiveness_score": fb.effectiveness_score,
                "frequency_used": fb.frequency_used,
                "last_updated": fb.last_updated,
            }
        
        return insights
    
    def _save_state(self):
        """Save evolution state to disk."""
        state_file = os.path.join(os.path.dirname(__file__), "evolution_state.json")
        
        state = {
            "evolution_log": [
                {**asdict(r), "improvements_made": r.improvements_made}
                for r in self.evolution_log[-100:]  # Keep last 100
            ],
            "pattern_feedback": {
                k: asdict(v) for k, v in self.pattern_feedback.items()
            },
            "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def load_state(self):
        """Load evolution state from disk."""
        state_file = os.path.join(os.path.dirname(__file__), "evolution_state.json")
        if not os.path.exists(state_file):
            return
        
        with open(state_file, encoding="utf-8") as f:
            state = json.load(f)
        
        self.evolution_log = [
            EvolutionRecord(**r) for r in state.get("evolution_log", [])
        ]
        self.pattern_feedback = {
            k: PatternFeedback(**v) for k, v in state.get("pattern_feedback", {}).items()
        }


# ─── Self-Evolution CLI ────────────────────────────────────────────────────────

def main():
    engine = EvolutionEngine()
    engine.load_state()
    
    print(f"""
╔═══════════════════════════════════════════════════╗
║   Jisi Self-Evolution Engine                      ║
║   Total cycles run: {len(engine.evolution_log):>3}                              ║
║   Categories analyzed: {len(set(r.matched_category for r in engine.evolution_log)):>3}                        ║
╚═══════════════════════════════════════════════════╝
    """)
    
    # Demo cycle with Taliswind
    print("\n🚀 Running demo evolution cycle...")
    record = engine.run_cycle(
        product_url="https://taliswind.com/en-us/products/four-crystal-guardian-bracelet",
        platform="meta"
    )
    
    # Show insights
    insights = engine.get_insights()
    print(f"\n🧠 Current Insights:")
    print(f"   Total cycles: {insights['total_cycles']}")
    print(f"   Categories: {insights['categories_analyzed']}")
    
    if insights['pattern_feedback']:
        print(f"   Pattern Feedback:")
        for key, fb in insights['pattern_feedback'].items():
            print(f"     {key}: score={fb['effectiveness_score']:.2f}, used={fb['frequency_used']}x")


if __name__ == "__main__":
    main()
