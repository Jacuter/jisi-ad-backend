"use client";

import { useState } from "react";

interface Product {
  title: string;
  brand: string;
  price: string | null;
  description: string;
  images: string[];
  rating: string | null;
  review_count: number | null;
}

interface Variant {
  rank: number;
  hook_type: string;
  hook_text: string;
  body_text: string;
  cta_text: string;
  score: number;
  storyboard: { time: string; action: string; subtitle: string; note?: string }[];
  recommendations: string[];
}

interface GenerationResult {
  success: boolean;
  product: Product;
  category: string;
  platform: string;
  pattern_note: string;
  variants: Variant[];
}

// ─── Step Indicator ──────────────────────────────────────────────────────────

function StepIndicator({ current }: { current: number }) {
  const steps = ["输入链接", "商品理解", "爆款研究", "创意策略", "输出结果"];
  return (
    <div className="flex items-center justify-center gap-1 sm:gap-2 mb-8 flex-wrap">
      {steps.map((label, i) => (
        <div key={i} className="flex items-center gap-1 sm:gap-2">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all duration-300 ${
              i + 1 === current
                ? "bg-black text-white shadow-md"
                : i + 1 < current
                ? "bg-green-500 text-white"
                : "bg-gray-100 text-gray-400"
            }`}
          >
            {i + 1 < current ? "✓" : i + 1}
          </div>
          <span className={`text-xs sm:text-sm hidden sm:block transition-colors ${i + 1 === current ? "font-semibold text-gray-900" : "text-gray-400"}`}>
            {label}
          </span>
          {i < steps.length - 1 && (
            <div className={`w-4 sm:w-8 h-0.5 transition-colors ${i + 1 < current ? "bg-green-500" : "bg-gray-200"}`} />
          )}
        </div>
      ))}
    </div>
  );
}

// ─── URL Input ────────────────────────────────────────────────────────────────

function URLInput({ onSubmit, onDemo }: { onSubmit: (url: string, platform: string) => void; onDemo: (platform: string) => void }) {
  const [url, setUrl] = useState("");
  const [platform, setPlatform] = useState("meta");

  return (
    <div className="flex flex-col items-center justify-center min-h-[65vh] px-4">
      <div className="w-full max-w-2xl text-center">
        <div className="inline-block px-3 py-1 bg-black text-white text-xs font-semibold rounded-full mb-6 tracking-widest uppercase">
          Jisi AI Ad Creative
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4 leading-tight">
          一个链接<br />
          <span className="text-gray-400">生成爆款广告创意</span>
        </h1>
        <p className="text-gray-500 mb-10 text-base sm:text-lg">
          输入 Shopify 商品链接，自动分析爆款规律，生成高转化广告内容
        </p>

        <div className="relative mb-6">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && url && onSubmit(url, platform)}
            placeholder="粘贴商品页链接，如 https://..."
            className="w-full h-16 px-6 pr-36 text-base rounded-2xl border border-gray-200 shadow-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-all bg-white"
          />
          <button
            onClick={() => url && onSubmit(url, platform)}
            className="absolute right-3 top-3 px-5 h-10 bg-black text-white rounded-xl text-sm font-semibold hover:bg-gray-800 active:scale-95 transition-all disabled:opacity-50"
            disabled={!url}
          >
            开始分析
          </button>
        </div>

        <div className="text-center mb-6">
          <button
            onClick={() => onDemo(platform)}
            className="text-sm text-gray-400 hover:text-gray-700 underline underline-offset-2 transition-colors"
          >
            没有链接？试试 Demo 模式（运动服装品类）
          </button>
        </div>

        <div className="flex flex-wrap justify-center gap-3 mb-10">
          {[
            { key: "meta", label: "Meta 广告", icon: "📱" },
            { key: "tiktok", label: "TikTok 广告", icon: "🎵" },
            { key: "both", label: "双平台", icon: "🌐" },
          ].map(({ key, label, icon }) => (
            <button
              key={key}
              onClick={() => setPlatform(key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all ${
                platform === key
                  ? "bg-black text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              <span>{icon}</span>
              <span>{label}</span>
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { icon: "⚡", label: "3分钟生成" },
            { icon: "📊", label: "爆款规律驱动" },
            { icon: "🎯", label: "双平台适配" },
            { icon: "✨", label: "智能评分排序" },
          ].map(({ icon, label }) => (
            <div key={label} className="flex flex-col items-center gap-1 px-3 py-3 bg-white rounded-2xl border border-gray-100 shadow-sm">
              <span className="text-xl">{icon}</span>
              <span className="text-xs text-gray-600 font-medium whitespace-nowrap">{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Product Card ─────────────────────────────────────────────────────────────

function ProductCard({ product }: { product: Product }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
        <span className="text-xl">📦</span> 商品理解
      </h3>
      <div className="space-y-2.5 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">品牌</span>
          <span className="font-medium">{product.brand || "—"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">产品</span>
          <span className="font-medium text-right max-w-[60%] leading-tight">{product.title}</span>
        </div>
        {product.price && (
          <div className="flex justify-between">
            <span className="text-gray-500">价格</span>
            <span className="font-medium text-green-600">{product.price}</span>
          </div>
        )}
        {product.rating && (
          <div className="flex justify-between">
            <span className="text-gray-500">评分</span>
            <span className="font-medium">★ {product.rating} ({product.review_count?.toLocaleString()} reviews)</span>
          </div>
        )}
        <div className="flex justify-between">
          <span className="text-gray-500">图片</span>
          <span className="font-medium">{product.images.length} 张</span>
        </div>
      </div>
    </div>
  );
}

// ─── Loading Card ────────────────────────────────────────────────────────────

function LoadingCard({ message = "正在处理..." }: { message?: string }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
        <span className="text-xl">🔥</span> 爆款广告研究
      </h3>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 border-2 border-gray-200 border-t-black rounded-full animate-spin" />
          <span className="text-gray-500 text-sm">{message}</span>
        </div>
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-14 bg-gray-50 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Research Complete Card ───────────────────────────────────────────────────

function ResearchCompleteCard({ patternNote, images }: { category?: string; patternNote: string; images: string[] }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
        <span className="text-xl">🔥</span> 爆款广告研究
      </h3>
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-sm text-green-600 font-medium">
          <span>✓</span> 品类匹配完成
        </div>
        <div className="text-sm text-gray-600 bg-gray-50 rounded-lg px-3 py-2">
          {patternNote}
        </div>
        {images.length > 0 && (
          <div>
            <div className="text-xs text-gray-400 mb-2">商品图片</div>
            <div className="flex gap-2 overflow-x-auto pb-1">
              {images.slice(0, 3).map((img, i) => (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  key={i}
                  src={img}
                  alt={`Product ${i + 1}`}
                  className="w-20 h-20 object-cover rounded-lg shrink-0 border border-gray-100"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                />
              ))}
            </div>
          </div>
        )}
        <div className="flex items-center gap-2 text-sm text-green-600 font-medium">
          <span>✓</span> 爆款规律分析完成
        </div>
        <div className="flex items-center gap-2 text-sm text-green-600 font-medium">
          <span>✓</span> 广告创意生成完成
        </div>
      </div>
    </div>
  );
}

// ─── Strategy Cards ─────────────────────────────────────────────────────────

function StrategyCards({ platform }: { platform: string }) {
  const isMeta = platform === "meta";
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-2xl">📱</span>
          <h3 className="font-semibold">Meta 广告</h3>
          {isMeta && <span className="ml-auto px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">推荐</span>}
        </div>
        <p className="text-sm text-gray-500 mb-4">转化导向 · 功能驱动 · 0-15秒效率最高</p>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">时长</span>
            <span className="font-medium">8-15秒</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">CTA</span>
            <span className="font-medium">Shop Now</span>
          </div>
          <div>
            <span className="text-gray-400 text-sm">Hook类型</span>
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {["数字背书", "限时促销", "社会证明"].map((h) => (
                <span key={h} className="px-2 py-0.5 bg-gray-100 rounded-full text-xs">{h}</span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-2xl">🎵</span>
          <h3 className="font-semibold">TikTok 广告</h3>
          {platform === "tiktok" && <span className="ml-auto px-2 py-0.5 bg-pink-100 text-pink-700 text-xs rounded-full">推荐</span>}
        </div>
        <p className="text-sm text-gray-500 mb-4">娱乐原生 · 情感共鸣 · 21-60秒完播率最高</p>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">时长</span>
            <span className="font-medium">15-45秒</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">CTA</span>
            <span className="font-medium">Link in bio</span>
          </div>
          <div>
            <span className="text-gray-400 text-sm">Hook类型</span>
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {["POV场景", "自然种草", "真实感"].map((h) => (
                <span key={h} className="px-2 py-0.5 bg-gray-100 rounded-full text-xs">{h}</span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Variant Card ────────────────────────────────────────────────────────────

function VariantCard({ variant, platform }: { variant: Variant; platform: string }) {
  const platformLabel = platform === "meta" ? "Meta" : "TikTok";
  const platformIcon = platform === "meta" ? "📱" : "🎵";
  const isTop = variant.rank === 1;

  return (
    <div className={`bg-white rounded-2xl border shadow-sm p-5 ${isTop ? "border-black ring-1 ring-black" : "border-gray-100"}`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`text-2xl font-bold ${isTop ? "text-black" : "text-gray-200"}`}>#{variant.rank}</span>
          {isTop && <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded-full font-medium">最佳</span>}
          <span className="px-2 py-0.5 bg-black text-white text-xs rounded-full font-medium">
            {variant.hook_type}
          </span>
        </div>
        <div className="text-right">
          <div className={`text-xl font-bold ${isTop ? "text-black" : "text-gray-700"}`}>{variant.score.toFixed(1)}/10</div>
          <div className="text-xs text-gray-400">预测转化分</div>
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">Hook</div>
          <div className="text-sm font-medium text-gray-900 leading-snug">{variant.hook_text}</div>
        </div>
        <div>
          <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">Body</div>
          <div className="text-sm text-gray-600 leading-snug">{variant.body_text}</div>
        </div>
        <div className="flex justify-between items-center pt-2 border-t border-gray-100">
          <div>
            <div className="text-xs text-gray-400">CTA</div>
            <div className="text-sm font-medium">{variant.cta_text}</div>
          </div>
          <div className="text-xs text-gray-400">
            {platformIcon} {platformLabel}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Storyboard ──────────────────────────────────────────────────────────────

function StoryboardView({ variant }: { variant: Variant }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
      <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
        <span className="text-xl">📋</span> 分镜脚本 — Variant #{variant.rank}
      </h3>
      <div className="space-y-3">
        {variant.storyboard.map((shot, i) => (
          <div key={i} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className="w-9 h-9 rounded-full bg-gray-100 flex items-center justify-center text-xs font-semibold text-gray-500 shrink-0">
                {shot.time.split("-")[0]}
              </div>
              {i < variant.storyboard.length - 1 && <div className="w-0.5 flex-1 bg-gray-100 my-0.5" />}
            </div>
            <div className="flex-1 pb-3">
              <div className="text-sm font-medium text-gray-800 leading-snug">{shot.action}</div>
              <div className="text-sm text-gray-500 mt-0.5">{shot.subtitle}</div>
              {shot.note && <div className="text-xs text-gray-400 mt-1">💡 {shot.note}</div>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────

export default function Home() {
  const [step, setStep] = useState(1);
  const [inputUrl, setInputUrl] = useState("");
  const [platform, setPlatform] = useState("meta");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [isDemo, setIsDemo] = useState(false);

  const handleStart = async (url: string, plat: string, demo = false) => {
    if (!url.trim() && !demo) return;
    setInputUrl(demo ? "Demo 模式 — Gymshark 运动短裤" : url);
    setPlatform(plat);
    setIsDemo(demo);
    setLoading(true);
    setError(null);
    setStep(2);

    try {
      await new Promise((r) => setTimeout(r, 1500));
      setStep(3);

      const body = demo
        ? { mock: true, mockCategory: "athletic_leggings", platform: plat }
        : { url: url.trim(), platform: plat };

      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data = await res.json();

      if (!res.ok || data.error) {
        throw new Error(data.error || "Generation failed");
      }

      setResult(data);
      setStep(4);

      // Step 4 → 5: Strategy + output
      await new Promise((r) => setTimeout(r, 1500));
      setStep(5);
    } catch (err) {
      setError(String(err));
      setStep(1);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setStep(1);
    setInputUrl("");
    setResult(null);
    setError(null);
    setPlatform("meta");
    setIsDemo(false);
  };

  // ── Step 1: URL Input ──────────────────────────────────────────────────
  if (step === 1) {
    return (
      <main className="min-h-screen bg-gray-50">
        <StepIndicator current={1} />
        <URLInput onSubmit={handleStart} onDemo={(plat) => handleStart("", plat, true)} />
      </main>
    );
  }

  // ── Steps 2-4: Loading ─────────────────────────────────────────────────
  if (loading || step <= 4) {
    const messages = {
      2: "正在提取商品信息...",
      3: "正在分析品类和爆款规律...",
      4: "正在生成广告创意方案...",
    };
    return (
      <main className="min-h-screen bg-gray-50 px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <StepIndicator current={step} />
          <div className="mb-4 px-4 py-2 bg-gray-100 rounded-lg text-sm text-gray-500">
            <span className="font-medium">URL:</span> {inputUrl}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {step >= 2 ? <ProductCard product={result?.product || { title: "加载中...", brand: "", price: null, description: "", images: [], rating: null, review_count: null }} /> : <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6"><h3 className="text-base font-semibold mb-4 flex items-center gap-2"><span className="text-xl">📦</span> 商品理解</h3><div className="space-y-2"><div className="h-4 bg-gray-100 rounded animate-pulse" /><div className="h-4 bg-gray-100 rounded animate-pulse" /><div className="h-4 bg-gray-100 rounded animate-pulse" /></div></div>}
            <LoadingCard message={messages[step as 2 | 3 | 4] || "处理中..."} />
          </div>
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
              ❌ {error}
              <button onClick={handleReset} className="ml-4 underline">重试</button>
            </div>
          )}
        </div>
      </main>
    );
  }

  // ── Step 5: Results ────────────────────────────────────────────────────
  return (
    <main className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <StepIndicator current={5} />
        <div className="mb-4 px-4 py-2 bg-gray-100 rounded-lg text-sm text-gray-500">
          <span className="font-medium">URL:</span> {inputUrl}
        </div>

        {/* Product + Strategy */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          {result?.product && <ProductCard product={result.product} />}
          <ResearchCompleteCard
            category={result?.category || ""}
            patternNote={result?.pattern_note || ""}
            images={result?.product?.images || []}
          />
        </div>

        {/* Strategy */}
        <div className="mb-6">
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <span>💡</span> 创意思路 — {result?.pattern_note}
          </h2>
          <StrategyCards platform={platform} />
        </div>

        {/* Variants */}
        <div className="mb-6">
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <span>🎬</span> 广告创意方案
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {result?.variants.map((v) => (
              <VariantCard key={v.rank} variant={v} platform={platform} />
            ))}
          </div>
        </div>

        {/* Storyboard + Tips */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          {result?.variants[0] && (
            <StoryboardView variant={result.variants[0]} />
          )}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
            <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
              <span className="text-xl">✨</span> 最佳实践建议
            </h3>
            <ul className="space-y-2.5 text-sm">
              {(result?.variants[0]?.recommendations || []).map((rec, i) => (
                <li key={i} className="flex gap-3">
                  <span className="text-green-500 font-bold shrink-0">✓</span>
                  <span className="text-gray-600">{rec}</span>
                </li>
              ))}
              {!(result?.variants[0]?.recommendations?.length) && (
                <>
                  {[
                    "前3秒用数字背书建立信任",
                    "功能列表用emoji增加扫描效率",
                    "社会证明放在中段增强转化",
                    "CTA配合紧迫感（Free Shipping / Today Only）",
                    "视频时长控制在8-15秒内效率最高",
                  ].map((tip, i) => (
                    <li key={i} className="flex gap-3">
                      <span className="text-green-500 font-bold shrink-0">✓</span>
                      <span className="text-gray-600">{tip}</span>
                    </li>
                  ))}
                </>
              )}
            </ul>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4 justify-center">
          <button
            onClick={handleReset}
            className="px-6 py-3 bg-black text-white rounded-xl font-medium hover:bg-gray-800 transition-colors"
          >
            🔄 再试一次
          </button>
        </div>
      </div>
    </main>
  );
}
