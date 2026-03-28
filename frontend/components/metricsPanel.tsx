"use client";

import { BlogMetrics } from "@/libs/api";
import {
  TrendingUp,
  Eye,
  Cpu,
  FileText,
  Hash,
  BarChart3,
} from "lucide-react";
import clsx from "clsx";

interface MetricsPanelProps {
  metrics: BlogMetrics | null;
  keyword: string;
}

// ── Circular gauge ──────────────────────────────────────────────────────────

function CircularGauge({
  value,
  max = 100,
  label,
  sublabel,
  color,
}: {
  value: number;
  max?: number;
  label: string;
  sublabel?: string;
  color: string; // stroke color hex
}) {
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(Math.max(value / max, 0), 1);
  const offset = circumference * (1 - pct);

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative w-24 h-24">
        <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
          <circle
            cx="50" cy="50" r={radius}
            fill="none"
            stroke="#1e1e2a"
            strokeWidth="8"
          />
          <circle
            cx="50" cy="50" r={radius}
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 1s ease" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-bold font-display" style={{ color }}>
            {Math.round(value)}
          </span>
          <span className="text-[9px] text-frost-dim uppercase tracking-wider">/ {max}</span>
        </div>
      </div>
      <p className="text-xs font-semibold text-frost text-center leading-tight">{label}</p>
      {sublabel && <p className="text-[10px] text-frost-dim text-center">{sublabel}</p>}
    </div>
  );
}

// ── Horizontal bar metric ────────────────────────────────────────────────────

function BarMetric({
  label,
  value,
  max,
  unit = "",
  icon: Icon,
  color,
}: {
  label: string;
  value: number;
  max: number;
  unit?: string;
  icon: React.ElementType;
  color: string;
}) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Icon className="w-3.5 h-3.5" style={{ color }} />
          <span className="text-[11px] text-frost-muted font-medium">{label}</span>
        </div>
        <span className="text-[11px] font-mono font-bold text-frost">
          {value}{unit}
        </span>
      </div>
      <div className="h-1.5 bg-ink-muted rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

// ── Stat chip ────────────────────────────────────────────────────────────────

function StatChip({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
}) {
  return (
    <div className="flex items-center gap-2 bg-ink-muted rounded-md px-3 py-2">
      <Icon className="w-3.5 h-3.5 text-acid flex-shrink-0" />
      <div>
        <p className="text-[10px] text-frost-dim uppercase tracking-wider">{label}</p>
        <p className="text-sm font-bold font-display text-frost">{value}</p>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function MetricsPanel({ metrics, keyword }: MetricsPanelProps) {
  if (!metrics) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-3 text-center px-6 py-12">
        <BarChart3 className="w-10 h-10 text-frost-dim opacity-40" />
        <p className="text-sm text-frost-dim font-display">
          Metrics will appear after generation
        </p>
        <p className="text-[11px] text-frost-dim opacity-60">
          SEO score, readability, and AI detection
        </p>
      </div>
    );
  }

  // Derive SEO score if not returned (fallback heuristic)
  const seoScore = metrics.seo_score ?? Math.min(
    Math.round(
      (metrics.word_count >= 1500 ? 30 : metrics.word_count >= 800 ? 15 : 5) +
      (metrics.heading_count >= 5 ? 20 : metrics.heading_count >= 3 ? 10 : 0) +
      (metrics.naturalness_score >= 70 ? 25 : 15) +
      25 // base for completing generation
    ), 100
  );

  const aiPct = metrics.ai_detection_percentage ?? 0;
  const readabilityScore = metrics.readability_score ?? 0;
  const wordCount = metrics.word_count ?? 0;

  // Color helpers
  const seoColor = seoScore >= 75 ? "#35f1a0" : seoScore >= 50 ? "#c8f135" : "#ffb830";
  const aiColor = aiPct <= 30 ? "#35f1a0" : aiPct <= 60 ? "#ffb830" : "#ff4545";
  const readColor = readabilityScore >= 60 ? "#35f1a0" : readabilityScore >= 40 ? "#c8f135" : "#ffb830";

  return (
    <div className="space-y-5 animate-fade-up">
      {/* Keyword badge */}
      <div className="flex items-center gap-2 px-3 py-2 bg-[rgba(200,241,53,0.06)] border border-[rgba(200,241,53,0.15)] rounded-md">
        <Hash className="w-3.5 h-3.5 text-acid flex-shrink-0" />
        <span className="text-xs font-mono text-acid truncate">{keyword}</span>
      </div>

      {/* Main gauges */}
      <div className="grid grid-cols-3 gap-2">
        <CircularGauge
          value={seoScore}
          label="SEO Score"
          sublabel="On-page"
          color={seoColor}
        />
        <CircularGauge
          value={readabilityScore}
          label="Readability"
          sublabel="Flesch 0-100"
          color={readColor}
        />
        <CircularGauge
          value={aiPct}
          label="AI Detected"
          sublabel="% AI-like"
          color={aiColor}
        />
      </div>

      {/* Detail bars */}
      <div className="bg-ink-soft border border-[#1e1e2a] rounded-lg p-4 space-y-3">
        <p className="text-[10px] font-mono text-frost-dim uppercase tracking-widest mb-1">
          Readability Breakdown
        </p>
        <BarMetric
          label="Flesch-Kincaid Grade"
          value={metrics.flesch_kincaid_grade ?? 0}
          max={20}
          icon={Eye}
          color="#c8f135"
        />
        <BarMetric
          label="Gunning Fog Index"
          value={metrics.gunning_fog ?? 0}
          max={20}
          icon={TrendingUp}
          color="#9499b0"
        />
        <BarMetric
          label="Naturalness Score"
          value={metrics.naturalness_score ?? 0}
          max={100}
          unit="%"
          icon={Cpu}
          color={aiColor}
        />
      </div>

      {/* Stat chips */}
      <div className="grid grid-cols-2 gap-2">
        <StatChip icon={FileText} label="Word Count" value={wordCount.toLocaleString()} />
        <StatChip icon={Hash} label="Headings" value={metrics.heading_count ?? 0} />
        <StatChip
          icon={Cpu}
          label="Detection"
          value={metrics.detection_method === "model" ? "Model" : "Heuristic"}
        />
        <StatChip
          icon={TrendingUp}
          label="FK Grade"
          value={`G${metrics.flesch_kincaid_grade ?? "—"}`}
        />
      </div>

      {/* Confidence note */}
      <p className="text-[10px] text-frost-dim text-center font-mono">
        AI detection via{" "}
        <span className="text-acid">
          {metrics.detection_method === "model"
            ? "RoBERTa classifier"
            : "heuristic analysis"}
        </span>{" "}
        · confidence: {metrics.detection_confidence ?? "n/a"}
      </p>
    </div>
  );
}