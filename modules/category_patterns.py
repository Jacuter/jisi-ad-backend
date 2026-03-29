"""
CategoryPatterns — Pre-built Winning Pattern Templates
Jisi × Shopify AI Video Ad System

Each category has platform-specific winning patterns derived from
Meta Ad Library analysis. These serve as the "intelligence" that
informs ad generation without requiring real-time scraping.

Plan B core: These templates are the fallback intelligence
when live scraping is unavailable.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class HookFormula:
    type: str
    template: str
    examples: list[str]
    score: float


@dataclass
class BodyFormula:
    structure: str
    feature_list_style: str
    required_elements: list[str]


@dataclass
class CTAFormula:
    primary: str
    secondary: str
    placement: str


@dataclass
class VideoStructure:
    optimal_duration: tuple[int, int]
    first_3_seconds: str
    middle_section: str
    ending: str
    pacing_tips: list[str]


@dataclass
class LanguageStyle:
    formality: str
    emoji_frequency: str
    common_phrases: list[str]


@dataclass
class CategoryPattern:
    category: str
    display_name: str
    region: str
    platform: str
    hooks: list[HookFormula]
    body: BodyFormula
    cta: CTAFormula
    video: VideoStructure
    language: LanguageStyle
    color_tone: str
    music_style: str


PATTERNS: dict = {}


def _r(p: CategoryPattern):
    if p.category not in PATTERNS:
        PATTERNS[p.category] = {}
    PATTERNS[p.category][p.platform] = p


# ═══════════════════════════════════════════════════════════════════
# ATHLETIC LEGGINGS / SPORTS WEAR
# ═══════════════════════════════════════════════════════════════════

_r(CategoryPattern(
    category="athletic_leggings",
    display_name="Athletic Wear / Leggings",
    region="US",
    platform="meta",
    hooks=[
        HookFormula("numeric", "Over {N} Sold — Find Out Why", ["Over 500,000 Sold", "Over 1.3M Women Trust This Brand"], 9.0),
        HookFormula("immediate_offer", "{X}% OFF + Free Shipping — Today Only", ["40% OFF Weekend Flash Sale", "30% OFF Today Only"], 8.5),
        HookFormula("problem_fix", "Say Goodbye to {Problem}", ["Say Goodbye to Sagging", "Finally: Leggings That Don't Quit"], 7.7),
    ],
    body=BodyFormula("list", "emoji", ["squat proof", "pockets", "waistband", "moisture wicking"]),
    cta=CTAFormula("Shop Now", "Free Shipping Over $50", "first_3s"),
    video=VideoStructure((8, 15), "数字背书钩子+快速场景切换", "产品特写+emoji功能列表+多场景", "立即CTA+紧迫感", ["前3秒用数字建立信任", "3-8秒3-4个场景切换", "保持能量感和速度感"]),
    language=LanguageStyle("casual", "high", ["Squat Proof", "No Gaping", "Stay Put Waistband"]),
    color_tone="明亮充满能量感（白色背景+彩色产品）",
    music_style="upbeat EDM / 商业健身BGM"
))

_r(CategoryPattern(
    category="athletic_leggings",
    display_name="Athletic Wear / Leggings",
    region="US",
    platform="tiktok",
    hooks=[
        HookFormula("problem_fix", "POV: You finally found leggings that don't quit", ["POV: You quit buying leggings that sag", "POV: It's leg day and your old leggings fail"], 8.5),
        HookFormula("question", "Wait... these did WHAT?", ["Wait... these actually hide my stomach?", "These actually don't move?"], 7.5),
    ],
    body=BodyFormula("testimonial", "mixed", ["真实场景", "自然展示", "素人感"]),
    cta=CTAFormula("Link in bio", "Save this for later", "last_3s"),
    video=VideoStructure((15, 45), "痛点场景/POV开场（真实不完美），不能像广告", "产品自然植入，展示真实使用场景，有情绪共鸣", "自然收尾，不催购买，引导收藏", ["前3秒不能有任何品牌露出", "单镜头Hold比快速剪辑更有效", "真实情绪代替专业表演"]),
    language=LanguageStyle("casual", "medium", ["this changed everything", "literally obsessed", "can't go back"]),
    color_tone="自然光/手机拍摄质感，不要影棚感",
    music_style="TikTok热门原声或流行音乐"
))

# ═══════════════════════════════════════════════════════════════════
# SKINCARE / BEAUTY
# ═══════════════════════════════════════════════════════════════════

_r(CategoryPattern(
    category="skincare",
    display_name="Skincare / Beauty",
    region="US",
    platform="meta",
    hooks=[
        HookFormula("problem_fix", "Tired of {Problem}? Meet Your Solution", ["Tired of Dry, Dull Skin?", "Finally: A Routine That Works"], 8.0),
        HookFormula("numeric", "{X}% Saw Results in {Time}", ["95% Saw Results in 4 Weeks", "Dermatologist-Recommended Formula"], 8.0),
        HookFormula("social_proof", "★{Rating} From {N}+ Real Customers", ["4.8/5 from 12,000+ Reviews", "★ 4.7 — Loved by 50,000+"], 7.5),
    ],
    body=BodyFormula("testimonial", "text", ["核心功效成分", "使用前后对比", "安全性说明"]),
    cta=CTAFormula("Shop Now", "30-Day Money Back Guarantee", "last_3s"),
    video=VideoStructure((10, 20), "皮肤问题特写（不完美ok）+ 痛点共鸣", "产品使用过程（before→after）+ 真实用户反馈", "安全感CTA（退款保证）+ 立即购买", ["真实感 > 专业感", "before/after要可信", "强调安全性减少购买焦虑"]),
    language=LanguageStyle("neutral", "medium", ["Clean Ingredients", "Dermatologist Tested", "Cruelty Free", "Glow"]),
    color_tone="柔光/自然色调，突出产品质感",
    music_style="轻松自然BGM或无音乐"
))

_r(CategoryPattern(
    category="skincare",
    display_name="Skincare / Beauty",
    region="US",
    platform="tiktok",
    hooks=[
        HookFormula("problem_fix", "POV: You're still using the wrong {Step}", ["POV: You still haven't found a cleanser", "Getting ready but your skin looks like THIS"], 8.0),
        HookFormula("testimonial", "{N} months later and my skin is...", ["6 months later — my acne is finally gone", "3 months later and my skin changed completely"], 8.5),
    ],
    body=BodyFormula("testimonial", "mixed", ["真实使用过程", "时间线展示", "自然口碑"]),
    cta=CTAFormula("Save this for later", "Dupe for $XXX", "last_3s"),
    video=VideoStructure((20, 60), "自然场景开场（浴室/梳妆台），不露品牌", "产品使用+真实感受描述+逐步展示效果", "不催购买，自然种草引导", ["素人视角最有效", "具象化感受描述", "用时间线建立信任"]),
    language=LanguageStyle("casual", "low", ["skin barrier", "game changer", "holy grail", "glow up"]),
    color_tone="自然采光，手机拍摄，浴室/卧室场景",
    music_style="轻音乐或热门原声"
))

# ═══════════════════════════════════════════════════════════════════
# WIRELESS EARBUDS / 3C ACCESSORIES
# ═══════════════════════════════════════════════════════════════════

_r(CategoryPattern(
    category="wireless_earbuds",
    display_name="Wireless Earbuds / Tech Accessories",
    region="US",
    platform="meta",
    hooks=[
        HookFormula("numeric", "{N}+ 5-Star Reviews", ["50,000+ 5-Star Reviews", "Over 100,000 Happy Customers"], 8.0),
        HookFormula("comparison", "Better Than {Competitor} at {X}% the Price", ["Half the Price of AirPods — Twice the Battery", "Sounds Better Than $300 Headphones"], 7.5),
        HookFormula("feature", "New {Feature} — Now Available", ["Active Noise Cancellation — Finally Under $100", "Transparency Mode Built In"], 7.0),
    ],
    body=BodyFormula("comparison", "text", ["核心规格对比", "价格锚定", "使用场景"]),
    cta=CTAFormula("Shop Now", "Free Returns Within 30 Days", "first_3s"),
    video=VideoStructure((10, 20), "惊艳产品特写或开箱瞬间", "核心功能演示（降噪/续航/佩戴感）+ 真实使用场景", "规格总结 + 价格锚定 + 立即CTA", ["不要过度渲染参数", "真实体验展示功能", "对比竞品不要攻击性太强"]),
    language=LanguageStyle("neutral", "low", ["Active Noise Cancellation", "Transparency Mode", "All-Day Battery", "IPX Rating"]),
    color_tone="科技感/专业感，深色背景突出产品",
    music_style="科技感BGM，无歌词"
))

_r(CategoryPattern(
    category="wireless_earbuds",
    display_name="Wireless Earbuds / Tech Accessories",
    region="US",
    platform="tiktok",
    hooks=[
        HookFormula("testimonial", "{Scenario} — these are everything", ["Working from home with these = game changer", "Testing noise cancellation on a flight"], 8.0),
        HookFormula("unboxing", "Finally got my hands on...", ["Unboxing the earbuds everyone is talking about", "They just arrived — first impressions"], 7.5),
    ],
    body=BodyFormula("testimonial", "mixed", ["真实使用场景", "自然功能展示", "个人感受"]),
    cta=CTAFormula("Link in bio", "Full review on my page", "last_3s"),
    video=VideoStructure((15, 45), "真实场景（地铁/办公室/健身房），不露品牌", "产品出现+自然功能演示+真实反馈", "不催购买，给出评价建议", ["POV/场景类内容最有效", "展示产品在真实生活中的融入感", "结尾给出诚实评价"]),
    language=LanguageStyle("casual", "low", ["game changer", "actually impressed", "worth it", "sound quality"]),
    color_tone="自然场景，手机拍摄，真实生活场景",
    music_style="热门原声或背景音乐"
))

# ═══════════════════════════════════════════════════════════════════
# HOME ORGANIZATION / STORAGE
# ═══════════════════════════════════════════════════════════════════

_r(CategoryPattern(
    category="home_storage",
    display_name="Home Organization / Storage",
    region="US",
    platform="meta",
    hooks=[
        HookFormula("problem_fix", "Your {Problem} Is Solved", ["Your Kitchen Clutter Is Finally Solved", "The Organization Hack Everyone is Talking About"], 8.0),
        HookFormula("numeric", "{N}-Star Review: 'I Can't Live Without This'", ["4.8/5 — 'This Changed My Whole Pantry'", "★ 4.9 — 'Organized My Entire Closet'"], 7.5),
        HookFormula("immediate_offer", "{X}% OFF — The Organization Sale You Needed", ["35% OFF All Storage Solutions — Weekend Only", "Flash Sale: 30% OFF Home Organization"], 8.5),
    ],
    body=BodyFormula("list", "emoji", ["产品功能", "使用场景", "收纳效果"]),
    cta=CTAFormula("Shop the Sale", "Free Shipping on Orders Over $35", "first_3s"),
    video=VideoStructure((15, 30), "痛点场景（杂乱/找东西/空间不足）", "产品展示+整理过程（ASMR感）+整齐效果", "情绪满足感+立即CTA", ["ASMR/整理过程有高完播率", "Before/After对比是核心", "情绪满足感是最终驱动"]),
    language=LanguageStyle("casual", "high", ["No-Mess", "Space-Saving", "Easy Install", "BPA-Free"]),
    color_tone="明亮整洁，突出产品融入家居环境",
    music_style="轻快BGM或ASMR音效"
))

_r(CategoryPattern(
    category="home_storage",
    display_name="Home Organization / Storage",
    region="US",
    platform="tiktok",
    hooks=[
        HookFormula("problem_fix", "POV: You finally organized your {Space}", ["POV: You finally organized your junk drawer", "POV: Your partner stopped complaining about the pantry"], 8.5),
        HookFormula("transformation", "Day 1 vs Day 30 with {Product}", ["Day 1 vs Day 30 with this pantry organizer", "Before/After my entire closet transformation"], 8.0),
    ],
    body=BodyFormula("testimonial", "mixed", ["真实整理过程", "时间线展示", "家人/伴侣反应"]),
    cta=CTAFormula("Save this", "Link in bio", "last_3s"),
    video=VideoStructure((20, 60), "杂乱场景+痛点共鸣（不要刻意摆拍）", "产品使用+逐步改变+情绪反应", "满足感释放+自然推荐", ["真实 > 完美", "时间线/对比是强有力的叙事工具", "家庭成员反应增加人性化"]),
    language=LanguageStyle("casual", "medium", ["organized my", "game changer", "can't live without", "future self"]),
    color_tone="自然家居场景，整洁vs杂乱对比",
    music_style="轻快音乐或原声"
))


# ═══════════════════════════════════════════════════════════════════
# CATEGORY MATCHING
# ═══════════════════════════════════════════════════════════════════

CATEGORY_KEYWORDS = {
    "athletic_leggings": ["leggings", "yoga pants", "workout pants", "athletic wear", "gym leggings", "compression pants", "squat proof", "butt lift", "workout shorts", "sports bra", "gym wear", "fitness apparel", "athletic shorts", "running pants"],
    "skincare": ["skincare", "face cream", "moisturizer", "serum", "cleanser", "sunscreen", "beauty", "glow", "anti-aging", "acne", "face mask", "eye cream", "toner", "skincare set", "beauty serum", "skin care"],
    "wireless_earbuds": ["earbuds", "headphones", "wireless earphones", "bluetooth earbuds", "noise cancelling", "airpods", "buds", "audio", "over-ear headphones", "on-ear headphones", "headset"],
    "home_storage": ["storage", "organizer", "container", "drawer organizer", "pantry", "closet", "shelf", "basket", "bins", "收纳", "organizer basket", "storage box"],
}


def match_category(product_title: str, product_tags: list[str],
                   product_description: str = "") -> Optional[str]:
    text = f"{product_title} {product_description} {' '.join(product_tags)}".lower()
    scores: dict[str, float] = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scores[cat] = score
    if not scores:
        return None
    return max(scores, key=scores.get)


def get_pattern(category: str, platform: str = "meta") -> Optional[CategoryPattern]:
    if category not in PATTERNS:
        return None
    return PATTERNS[category].get(platform)


def get_all_categories() -> list[str]:
    return list(PATTERNS.keys())


def get_pattern_summary(category: str) -> Optional[dict]:
    if category not in PATTERNS:
        return None
    summary = {}
    for platform, pattern in PATTERNS[category].items():
        summary[platform] = {
            "display_name": pattern.display_name,
            "optimal_duration": f"{pattern.video.optimal_duration[0]}-{pattern.video.optimal_duration[1]}s",
            "top_hooks": [h.type for h in pattern.hooks[:2]],
            "primary_cta": pattern.cta.primary,
            "key_phrases": pattern.language.common_phrases[:3],
        }
    return summary


# ═══════════════════════════════════════════════════════════════════
# SUPPLEMENTS / HEALTH PRODUCTS
# ═══════════════════════════════════════════════════════════════════

_r(CategoryPattern(
    category='supplements',
    display_name='Health / Nutritional Supplements',
    region='US',
    platform='meta',
    hooks=[
        HookFormula('numeric', '{X}% of People Are Deficient in {Nutrient}', ['87% of Americans Are Vitamin D Deficient', '8/10 People Lack This Nutrient'], 8.5),
        HookFormula('social_proof', '★{Rating} From {N}+ Customers — {Result}', ['4.9/5 — 50,000+ Happy Customers', 'Trusted by Pro Athletes and Trainers'], 8.0),
        HookFormula('authority', '{N}+ Doctors Recommend {Product}', ['2000+ Doctors Recommend This', 'Clinical-Strength Formula'], 7.5),
    ],
    body=BodyFormula('list', 'text', ['核心成分', '功效说明', '安全性/天然']),
    cta=CTAFormula('Shop Now', '60-Day Money Back Guarantee', 'first_3s'),
    video=VideoStructure((15, 30), '统计数据/权威背书开场', '成分展示+功效说明+用户见证', '安全保障CTA+立即购买', ['前3秒用惊人数据抓住注意力', '自然导出产品而非强行推销', '安全性/退款保证降低购买阻力']),
    language=LanguageStyle('neutral', 'medium', ['Clinically Proven', 'All-Natural', 'Third-Party Tested', 'GMP Certified']),
    color_tone='专业医疗感/绿色健康色调',
    music_style='轻松自然BGM，信任感'
))

_r(CategoryPattern(
    category='supplements',
    display_name='Health / Nutritional Supplements',
    region='US',
    platform='tiktok',
    hooks=[
        HookFormula('testimonial', '{Time} taking {Product} and here is what happened', ['6 months taking vitamin D and my energy changed', '3 months in and my doctor noticed'], 8.5),
        HookFormula('problem_fix', 'If you always feel tired, it might be {Nutrient}', ['If you always feel tired, it might be low vitamin D', 'No matter how much you sleep, still tired?'], 8.0),
    ],
    body=BodyFormula('testimonial', 'mixed', ['真实使用过程', '时间线效果', '身体感受变化']),
    cta=CTAFormula('Save this', 'Link in bio for what I take', 'last_3s'),
    video=VideoStructure((20, 60), '日常场景开场（起床/疲劳感），不露品牌', '产品自然出现+每日使用展示+效果感受', '诚实评价，不催购买', ['素人视角最有效', '时间线建立信任', '诚实评价比过度承诺更可信']),
    language=LanguageStyle('casual', 'low', ['game changer', 'actually feel better', 'no energy crash', 'my doctor was surprised']),
    color_tone='自然日常场景，卧室/厨房/办公室',
    music_style='轻快日常音乐或无音乐'
))

# ═══════════════════════════════════════════════════════════════════
# PET PRODUCTS
# ═══════════════════════════════════════════════════════════════════

_r(CategoryPattern(
    category='pet_products',
    display_name='Pet Products / Pet Care',
    region='US',
    platform='meta',
    hooks=[
        HookFormula('problem_fix', 'Finally: A {Product} Your {Pet} Will Love', ['Finally: A Leash That Won\'t Pull', 'The Dog Bed That Dogs Actually Sleep In'], 8.0),
        HookFormula('numeric', '★ {Rating} — {N}+ Happy {Pet} Parents', ['4.8/5 — 20,000+ Dog Parents', 'Trusted by 100,000+ Pet Parents'], 7.5),
        HookFormula('immediate_offer', '{X}% OFF — For Your {Pet}', ['30% OFF Dog Food — This Week Only', 'BOGO: Buy One Get One Free on Treats'], 8.5),
    ],
    body=BodyFormula('list', 'emoji', ['材质安全', '宠物喜好', '易于清洁', '耐用']),
    cta=CTAFormula('Shop Now', 'Free Shipping on Orders Over $49', 'first_3s'),
    video=VideoStructure((10, 20), '宠物可爱画面开场+产品露出', '产品功能展示+宠物真实反应', '立即CTA+促销信息', ['前3秒用宠物可爱抓住注意力', '展示宠物真实反应（不是摆拍）', '主人视角增加代入感']),
    language=LanguageStyle('casual', 'high', ['Pet-Safe', 'Durable', 'Machine Washable', 'Vet Approved']),
    color_tone='温暖家庭感，宠物是主角',
    music_style='欢快/可爱风格BGM'
))

_r(CategoryPattern(
    category='pet_products',
    display_name='Pet Products / Pet Care',
    region='US',
    platform='tiktok',
    hooks=[
        HookFormula('testimonial', 'My {Pet} is obsessed with this', ['My dog is literally obsessed with this bed', 'Cat approves this new toy'], 8.5),
        HookFormula('problem_fix', 'POV: Your {Pet} destroying {Problem}', ['POV: Your dog still anxious during thunderstorms', 'POV: Cat knocking everything off the shelf'], 8.0),
    ],
    body=BodyFormula('testimonial', 'mixed', ['宠物真实反应', '产品使用场景', '宠物性格']),
    cta=CTAFormula('Save this for later', 'Link in bio', 'last_3s'),
    video=VideoStructure((15, 45), '宠物场景开场，不露品牌', '产品出现+宠物真实反应/玩耍', '自然收尾，引导收藏', ['宠物是主角，不是产品', '真实反应比摆拍更可爱', '主人/宠物互动增加温度']),
    language=LanguageStyle('casual', 'high', ['obsessed', 'won\'t stop asking for', 'game changer for', 'finally sleeping through']),
    color_tone='家居场景，宠物自然活动空间',
    music_style='欢快/可爱/宠物相关原声'
))

# ═══════════════════════════════════════════════════════════════════
# CRYSTAL JEWELRY
# ═══════════════════════════════════════════════════════════════════

_r(CategoryPattern(
    category='crystal_jewelry',
    display_name='Crystal / Handmade Jewelry',
    region='US',
    platform='meta',
    hooks=[
        HookFormula('numeric', '{N}+ People Wear This Crystal for {Benefit}', ['5000+ People Wear Crystal Bracelets for Protection', 'Over 10,000 Crystal Lovers Chose This'], 8.5),
        HookFormula('authority', 'Handmade by {N} Crystal Artisans', ['Handmade by Master Crystal Artisans', 'Sourced and Blessed by Crystal Experts'], 7.5),
        HookFormula('social_proof', '★ {Rating} — {N}+ 5-Star Reviews', ['4.9/5 — 2,000+ Happy Crystal Lovers', 'Trusted by Crystal Healers Worldwide'], 8.0),
    ],
    body=BodyFormula('list', 'text', ['Crystal names', 'Healing properties', 'Handmade quality', 'Gift-ready packaging']),
    cta=CTAFormula('Shop Now', 'Free Shipping on Orders Over $79', 'first_3s'),
    video=VideoStructure((10, 20), 'Crystal珠宝特写+自然光展示+能量感', '手工细节+晶石特写+用户佩戴展示', '立即CTA+品牌故事', ['前3秒用晶石特写抓住注意力', '自然光展示最能呈现水晶美感', '用户真实佩戴增加代入感']),
    language=LanguageStyle('casual', 'low', ['Handmade', 'One-of-a-Kind', 'Gift-Ready', 'Nickel-Free', 'Healing Properties']),
    color_tone='自然光/柔和暖色调，突出水晶质感',
    music_style='轻柔自然音乐/水晶颂钵/和平氛围'
))

_r(CategoryPattern(
    category='crystal_jewelry',
    display_name='Crystal / Handmade Jewelry',
    region='US',
    platform='tiktok',
    hooks=[
        HookFormula('testimonial', 'I have been wearing this crystal bracelet for {Time} and...', ['I have been wearing this crystal bracelet for 3 months and...', 'My crystal healer recommended this bracelet and...'], 8.5),
        HookFormula('unboxing', 'Opening my new crystal bracelet from {Brand}', ['Opening my new Crystal Valley bracelet', 'This bracelet just arrived and I am obsessed'], 8.0),
    ],
    body=BodyFormula('testimonial', 'mixed', ['真实佩戴感受', 'Crystal能量描述', '日常场景展示']),
    cta=CTAFormula('Save this', 'Link in bio', 'last_3s'),
    video=VideoStructure((15, 45), '开箱/佩戴场景开场，不露品牌', 'Crystal自然展示+真实感受描述+能量感', '自然种草，不催购买', ['真实感最重要，不要过度专业化', 'Crystal能量感受的描述增加共鸣', '展示日常生活中佩戴的场景']),
    language=LanguageStyle('casual', 'low', ['energy', 'vibes', 'manifest', 'healing', 'obsessed']),
    color_tone='自然日常场景，自然光',
    music_style='轻柔背景音乐或无音乐'
))


# ═══════════════════════════════════════════════════════════════════
# CATEGORY KEYWORDS (expanded)
# ═══════════════════════════════════════════════════════════════════

CATEGORY_KEYWORDS['supplements'] = [
    'supplement', 'vitamin', 'gummy', 'probiotic', 'collagen', 'protein',
    'health', 'immune', 'energy', 'sleep', 'anti-aging', 'omega', 'acai'
]
CATEGORY_KEYWORDS['pet_products'] = [
    'dog', 'cat', 'pet', 'leash', 'collar', 'bed', 'toy', 'treats',
    'food', 'pet carrier', 'grooming', 'pet supplies', 'puppy'
]
CATEGORY_KEYWORDS['crystal_jewelry'] = [
    'crystal', 'bracelet', 'jewelry', 'jewellery', 'gemstone', 'necklace',
    'crystal healing', 'handmade jewelry', 'semi-precious', 'taliswind',
    'protection bracelet', 'healing crystal', 'pendant', 'earring'
]
