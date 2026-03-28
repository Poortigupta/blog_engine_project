"use client";

import { useState, useRef } from "react";
import {
  Zap,
  ChevronDown,
  AlertCircle,
  Sparkles,
  Terminal,
} from "lucide-react";
import clsx from "clsx";

import BlogDisplay from "@/components/BlogDisplay";
import MetricsPanel from "@/components/metricsPanel";
import ProgressFlow, { PipelineStep } from "@/components/ProgressFlow";
import { generateBlog, BlogGenerationResponse } from "@/libs/api";

// ── Tone options ──────────────────────────────────────────────────────────────

const TONES = [
  { value: "informative",  label: "Informative",  desc: "Clear, authoritative" },
  { value: "persuasive",   label: "Persuasive",   desc: "Builds urgency" },
  { value: "casual",       label: "Casual",       desc: "Conversational" },
  { value: "professional", label: "Professional", desc: "B2B formal" },
] as const;

type ToneValue = (typeof TONES)[number]["value"];

// ── Pipeline step sequencer ───────────────────────────────────────────────────

const STEP_SEQUENCE: PipelineStep[] = [
  "scraping", "researching", "writing", "editing", "validating", "done",
];

// ── Page component ────────────────────────────────────────────────────────────

export default function HomePage() {
  const [keyword, setKeyword] = useState("");
  const [tone, setTone] = useState<ToneValue>("informative");
  const [step, setStep] = useState<PipelineStep>("idle");
  const [result, setResult] = useState<BlogGenerationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [toneOpen, setToneOpen] = useState(false);
  const stepTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const currentTone = TONES.find((t) => t.value === tone)!;
  const isGenerating = step !== "idle" && step !== "done" && step !== "error";

  // Simulate step progress during API call (the real steps happen in backend)
  function startStepSimulation() {
    let idx = 0;
    setStep(STEP_SEQUENCE[0]);
    // Advance through "fake" steps every ~20s to give visual feedback
    // Real completion comes when the API returns
    stepTimerRef.current = setInterval(() => {
      idx++;
      if (idx < STEP_SEQUENCE.length - 1) {
        setStep(STEP_SEQUENCE[idx]);
      }
    }, 22_000);
  }

  function stopStepSimulation() {
    if (stepTimerRef.current) {
      clearInterval(stepTimerRef.current);
      stepTimerRef.current = null;
    }
  }

  async function handleGenerate() {
    if (!keyword.trim()) return;
    setError(null);
    setResult(null);
    startStepSimulation();

    try {
      const data = await generateBlog({ keyword: keyword.trim(), tone });
      stopStepSimulation();
      setStep("done");
      setResult(data);
    } catch (err: any) {
      stopStepSimulation();
      setStep("error");
      const msg =
        err?.response?.data?.detail ??
        err?.message ??
        "Unknown error. Is the backend running on :8000?";
      setError(msg);
    }
  }

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{
        backgroundImage:
          "linear-gradient(rgba(200,241,53,0.025) 1px, transparent 1px), linear-gradient(90deg, rgba(200,241,53,0.025) 1px, transparent 1px)",
        backgroundSize: "40px 40px",
      }}
    >
      {/* ── Header ─────────────────────────────────────────────────── */}
      <header className="border-b border-[#1e1e2a] bg-ink/80 backdrop-blur-sm px-6 py-3 flex items-center justify-between z-10 sticky top-0">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-acid rounded flex items-center justify-center">
            <Zap className="w-4 h-4 text-ink" />
          </div>
          <span className="text-sm font-display font-bold tracking-tight text-frost">
            BlogForge
          </span>
          <span className="hidden sm:block text-[10px] text-frost-dim border border-[#1e1e2a] rounded px-1.5 py-0.5 font-mono">
            v1.0 · local LLM
          </span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-signal-green animate-pulse-acid" />
            <span className="text-[10px] text-frost-dim font-mono">API :8000</span>
          </div>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-[10px] text-frost-dim hover:text-acid transition-colors font-mono"
          >
            <Terminal className="w-3 h-3" />
            Swagger
          </a>
        </div>
      </header>

      {/* ── Main layout ────────────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── LEFT: Input + Blog Preview ─────────────────────────── */}
        <div className="flex flex-col w-full lg:w-[60%] border-r border-[#1e1e2a] overflow-hidden">

          {/* Input panel */}
          <div className="border-b border-[#1e1e2a] p-5 space-y-4 bg-ink-soft flex-shrink-0">
            <div>
              <label className="block text-[10px] font-mono text-frost-dim uppercase tracking-widest mb-2">
                Target Keyword
              </label>
              <input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !isGenerating && handleGenerate()}
                placeholder="e.g. best productivity apps for developers"
                disabled={isGenerating}
                className={clsx(
                  "w-full bg-ink-muted border rounded-md px-4 py-2.5 text-sm text-frost placeholder-frost-dim",
                  "font-body outline-none transition-all duration-200",
                  "border-[#1e1e2a] focus:border-acid focus:ring-1 focus:ring-[rgba(200,241,53,0.2)]",
                  isGenerating && "opacity-50 cursor-not-allowed"
                )}
              />
            </div>

            <div className="flex items-end gap-3">
              {/* Tone selector */}
              <div className="flex-1">
                <label className="block text-[10px] font-mono text-frost-dim uppercase tracking-widest mb-2">
                  Tone
                </label>
                <div className="relative">
                  <button
                    onClick={() => setToneOpen((o) => !o)}
                    disabled={isGenerating}
                    className={clsx(
                      "w-full flex items-center justify-between bg-ink-muted border border-[#1e1e2a]",
                      "rounded-md px-4 py-2.5 text-sm text-frost transition-all",
                      "hover:border-frost-dim focus:border-acid outline-none",
                      isGenerating && "opacity-50 cursor-not-allowed"
                    )}
                  >
                    <div className="flex items-center gap-2 text-left">
                      <span>{currentTone.label}</span>
                      <span className="text-[10px] text-frost-dim">{currentTone.desc}</span>
                    </div>
                    <ChevronDown
                      className={clsx("w-4 h-4 text-frost-dim transition-transform", toneOpen && "rotate-180")}
                    />
                  </button>

                  {toneOpen && (
                    <div className="absolute top-full mt-1 left-0 right-0 bg-ink-soft border border-[#1e1e2a] rounded-md overflow-hidden z-20 shadow-2xl">
                      {TONES.map((t) => (
                        <button
                          key={t.value}
                          onClick={() => { setTone(t.value); setToneOpen(false); }}
                          className={clsx(
                            "w-full flex items-center justify-between px-4 py-2.5 text-left text-sm transition-colors",
                            tone === t.value
                              ? "bg-[rgba(200,241,53,0.08)] text-acid"
                              : "text-frost hover:bg-ink-muted"
                          )}
                        >
                          <span>{t.label}</span>
                          <span className="text-[10px] text-frost-dim">{t.desc}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Generate button */}
              <button
                onClick={handleGenerate}
                disabled={isGenerating || !keyword.trim()}
                className={clsx(
                  "flex items-center gap-2 px-5 py-2.5 rounded-md text-sm font-semibold font-display",
                  "transition-all duration-200 whitespace-nowrap",
                  isGenerating || !keyword.trim()
                    ? "bg-ink-muted text-frost-dim cursor-not-allowed"
                    : "bg-acid text-ink hover:bg-acid-glow active:scale-95"
                )}
              >
                {isGenerating ? (
                  <>
                    <span className="w-4 h-4 border-2 border-frost-dim border-t-transparent rounded-full animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Generate Blog
                  </>
                )}
              </button>
            </div>

            {/* Error banner */}
            {error && (
              <div className="flex items-start gap-2 px-3 py-2.5 bg-[rgba(255,69,69,0.08)] border border-[rgba(255,69,69,0.2)] rounded-md">
                <AlertCircle className="w-4 h-4 text-signal-red mt-0.5 flex-shrink-0" />
                <p className="text-xs text-signal-red font-mono">{error}</p>
              </div>
            )}
          </div>

          {/* Blog content area */}
          <div className="flex-1 overflow-hidden">
            <BlogDisplay
              content={result?.final_blog ?? ""}
              wordCount={result?.metrics?.word_count}
            />
          </div>
        </div>

        {/* ── RIGHT: Pipeline + Metrics ──────────────────────────── */}
        <div className="hidden lg:flex flex-col w-[40%] overflow-y-auto p-5 gap-5 bg-ink-soft">
          {/* Pipeline progress */}
          <ProgressFlow currentStep={step} />

          {/* Divider */}
          {step !== "idle" && (
            <div className="border-t border-[#1e1e2a]" />
          )}

          {/* Metrics */}
          <MetricsPanel
            metrics={result?.metrics ?? null}
            keyword={keyword || "—"}
          />

          {/* Outline preview (collapsible-ish) */}
          {result?.outline && (
            <details className="group">
              <summary className="flex items-center gap-2 text-[10px] font-mono text-frost-dim uppercase tracking-widest cursor-pointer select-none hover:text-acid transition-colors list-none">
                <ChevronDown className="w-3 h-3 transition-transform group-open:rotate-180" />
                Research Outline
              </summary>
              <div className="mt-3 bg-ink border border-[#1e1e2a] rounded-md p-4 max-h-64 overflow-y-auto">
                <pre className="text-[11px] text-frost-dim font-mono whitespace-pre-wrap leading-relaxed">
                  {result.outline}
                </pre>
              </div>
            </details>
          )}

          {/* Empty state hint */}
          {step === "idle" && !result && (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center py-8 opacity-40">
              <Zap className="w-8 h-8 text-acid" />
              <p className="text-xs font-display text-frost-dim">
                Enter a keyword and click Generate<br />to start the pipeline
              </p>
              <p className="text-[10px] font-mono text-frost-dim">
                Powered by CrewAI + Ollama (llama3)
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}