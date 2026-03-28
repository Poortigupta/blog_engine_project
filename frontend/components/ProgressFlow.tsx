"use client";

import { CheckCircle2, Circle, Loader2, Search, Bot, Pencil, ShieldCheck } from "lucide-react";
import clsx from "clsx";

export type PipelineStep =
  | "idle"
  | "scraping"
  | "researching"
  | "writing"
  | "editing"
  | "validating"
  | "done"
  | "error";

const STEPS: {
  id: PipelineStep;
  label: string;
  sublabel: string;
  icon: React.ElementType;
}[] = [
  { id: "scraping",    label: "Analyzing SERP",         sublabel: "Scraping top 3 results",        icon: Search },
  { id: "researching", label: "Research Agent",          sublabel: "Identifying content gaps",       icon: Bot },
  { id: "writing",     label: "Writer Agent",            sublabel: "Drafting full blog post",        icon: Pencil },
  { id: "editing",     label: "SEO Editor Agent",        sublabel: "Enforcing keyword compliance",   icon: Bot },
  { id: "validating",  label: "Calculating SEO Metrics", sublabel: "Readability + AI detection",     icon: ShieldCheck },
];

function stepStatus(
  stepId: PipelineStep,
  current: PipelineStep
): "done" | "active" | "pending" {
  const order: PipelineStep[] = [
    "scraping", "researching", "writing", "editing", "validating", "done",
  ];
  const si = order.indexOf(stepId);
  const ci = order.indexOf(current);
  if (ci === -1 || current === "idle") return "pending";
  if (si < ci || current === "done") return "done";
  if (si === ci) return "active";
  return "pending";
}

interface ProgressFlowProps {
  currentStep: PipelineStep;
}

export default function ProgressFlow({ currentStep }: ProgressFlowProps) {
  if (currentStep === "idle") return null;

  return (
    <div className="bg-ink-soft border border-[#1e1e2a] rounded-lg p-4 space-y-1">
      <p className="text-[10px] font-mono text-frost-dim uppercase tracking-widest mb-3">
        Pipeline Status
      </p>
      {STEPS.map((step, i) => {
        const status = stepStatus(step.id, currentStep);
        const Icon = step.icon;
        return (
          <div
            key={step.id}
            className={clsx(
              "flex items-center gap-3 py-2 px-3 rounded-md transition-all duration-300",
              status === "active" && "bg-[rgba(200,241,53,0.06)] border border-[rgba(200,241,53,0.15)]",
              status === "done" && "opacity-60",
              status === "pending" && "opacity-30"
            )}
          >
            {/* Status icon */}
            <div className="w-5 h-5 flex-shrink-0">
              {status === "done" && (
                <CheckCircle2 className="w-5 h-5 text-signal-green" />
              )}
              {status === "active" && (
                <Loader2 className="w-5 h-5 text-acid animate-spin" />
              )}
              {status === "pending" && (
                <Circle className="w-5 h-5 text-frost-dim" />
              )}
            </div>

            {/* Step label */}
            <div className="flex-1 min-w-0">
              <p
                className={clsx(
                  "text-xs font-semibold font-display truncate",
                  status === "active" && "text-acid",
                  status === "done" && "text-signal-green",
                  status === "pending" && "text-frost-dim"
                )}
              >
                {step.label}
              </p>
              <p className="text-[10px] text-frost-dim truncate">{step.sublabel}</p>
            </div>

            {/* Step number */}
            <span className="text-[10px] font-mono text-frost-dim">{String(i + 1).padStart(2, "0")}</span>
          </div>
        );
      })}

      {currentStep === "error" && (
        <div className="mt-2 px-3 py-2 bg-[rgba(255,69,69,0.1)] border border-[rgba(255,69,69,0.2)] rounded text-signal-red text-xs font-mono">
          ✗ Pipeline failed. Check backend logs.
        </div>
      )}
    </div>
  );
}