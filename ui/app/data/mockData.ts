export const mockProduct = {
  title: "高腰无缝运动紧身裤",
  brand: "LuxeActive",
  price: "¥299",
  currency: "CNY",
  rating: 4.8,
  reviewCount: 2847,
  category: "athletic_leggings",
  description: "采用四向弹力面料，提供极致舒适感与支撑力。高腰设计塑造完美曲线，适合瑜伽、跑步、健身等多种运动场景。",
  tags: ["运动", "瑜伽", "健身", "紧身裤", "高腰"],
  images: ["/placeholder-product.jpg"],
};

export const mockCompetitorAds = [
  {
    id: 1,
    brand: "Lululemon",
    hook: "穿上它的第一天，我就爱上了运动",
    platform: "Meta",
    engagement: "12.4K 互动",
    pattern: "情感共鸣 + 生活方式",
  },
  {
    id: 2,
    brand: "Gymshark",
    hook: "47,000+ 女性的首选训练裤",
    platform: "TikTok",
    engagement: "89K 点赞",
    pattern: "社交证明 + 数字",
  },
  {
    id: 3,
    brand: "Alo Yoga",
    hook: "从瑜伽垫到街头，一条裤子搞定",
    platform: "Meta",
    engagement: "8.2K 互动",
    pattern: "场景多样性 + 实用性",
  },
];

export const mockStrategies = {
  meta: {
    platform: "Meta 广告",
    icon: "📱",
    primaryHook: "数字社交证明",
    hookExample: "47,000+ 女性选择的训练裤",
    format: "单图 + 轮播",
    duration: "静态图片",
    audience: "25-40岁女性，健身爱好者",
    keyPoints: ["高腰塑形效果展示", "面料细节特写", "真实用户穿搭"],
    cta: "立即购买",
  },
  tiktok: {
    platform: "TikTok 广告",
    icon: "🎵",
    primaryHook: "即时效果展示",
    hookExample: "穿上的瞬间，你会明白为什么",
    format: "竖版短视频",
    duration: "15-30秒",
    audience: "18-35岁女性，潮流运动人群",
    keyPoints: ["穿搭变身对比", "运动场景展示", "KOL真实测评"],
    cta: "点击购买",
  },
};

export const mockVariants = [
  {
    id: 1,
    hookType: "numeric_social_proof",
    hookText: "47,000+ 女性的首选 — 这条裤子到底有什么魔力？",
    bodyText:
      "高腰四向弹力设计，穿上的瞬间感受到不同。无论是晨跑、瑜伽还是日常穿搭，LuxeActive 紧身裤都能完美适配。现在下单享受首单优惠。",
    ctaText: "立即抢购 →",
    score: 8.7,
    storyboard: [
      { time: "0-3s", action: "产品特写镜头", subtitle: "47,000+ 女性的首选", note: "高清面料纹理" },
      { time: "3-8s", action: "穿搭展示", subtitle: "四向弹力，自由运动", note: "瑜伽动作展示" },
      { time: "8-15s", action: "用户评价", subtitle: "真实用户反馈", note: "截图评论展示" },
      { time: "15-20s", action: "CTA 画面", subtitle: "立即抢购，限时优惠", note: "价格+按钮" },
    ],
  },
  {
    id: 2,
    hookType: "problem_fix",
    hookText: "运动裤总是往下滑？这个问题终于解决了",
    bodyText:
      "专利高腰防滑设计，剧烈运动也不走位。超细纤维面料轻薄透气，深蹲不透明。告别运动时的尴尬，专注你的每一次训练。",
    ctaText: "解决问题，立即购买",
    score: 8.2,
    storyboard: [
      { time: "0-3s", action: "痛点场景", subtitle: "运动裤总是往下滑？", note: "夸张表情展示" },
      { time: "3-10s", action: "产品解决方案", subtitle: "专利防滑腰带设计", note: "技术细节展示" },
      { time: "10-18s", action: "对比测试", subtitle: "深蹲测试，完全不透明", note: "实测视频" },
      { time: "18-25s", action: "购买引导", subtitle: "解决问题，立即购买", note: "优惠信息" },
    ],
  },
  {
    id: 3,
    hookType: "lifestyle_aspiration",
    hookText: "从健身房到咖啡馆，一条裤子的全天穿搭",
    bodyText:
      "不只是运动裤，更是你的生活方式。简约设计搭配多种颜色，运动后直接出街毫无违和感。LuxeActive，让运动成为你最美的日常。",
    ctaText: "探索全系列",
    score: 7.9,
    storyboard: [
      { time: "0-3s", action: "晨间健身场景", subtitle: "从健身房开始的一天", note: "阳光健身房" },
      { time: "3-10s", action: "日常穿搭转换", subtitle: "一条裤子，多种场景", note: "快速切换镜头" },
      { time: "10-18s", action: "咖啡馆街拍", subtitle: "运动即时尚", note: "城市街头风格" },
      { time: "18-25s", action: "产品系列展示", subtitle: "探索全系列", note: "多色展示" },
    ],
  },
];
