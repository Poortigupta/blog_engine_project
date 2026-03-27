"""
main.py — FastAPI application entry point
Run with: uvicorn main:app --reload --port 8000
"""

import asyncio
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from scraper import scrape_serp
from agents.research_agent import run_research
from agents.writer_agent import run_writer
from agents.seo_agent import run_seo_editor
from validation.readability import get_readability_scores
from validation.ai_detector import get_ai_detection_score

SCRAPE_TIMEOUT_SECONDS = 30.0
RESEARCH_TIMEOUT_SECONDS = 60.0
WRITER_TIMEOUT_SECONDS = 90.0
SEO_TIMEOUT_SECONDS = 60.0
READABILITY_TIMEOUT_SECONDS = 20.0
AI_DETECTION_TIMEOUT_SECONDS = 45.0

# ─── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Blog Generation Engine API",
    description="AI-powered, GEO-optimized blog generation using CrewAI + Ollama.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request / Response Schemas ───────────────────────────────────────────────

class GenerateRequest(BaseModel):
    keyword: str
    tone: Optional[str] = "informative"  # e.g. informative, persuasive, casual


class SerpResponse(BaseModel):
    keyword: str
    combined_text: str
    headings: list[str]
    source_urls: list[str]


class BlogGenerationResponse(BaseModel):
    keyword: str
    tone: str
    outline: str
    draft_blog: str
    final_blog: str
    metrics: dict


def _elapsed_ms(start: float) -> int:
    """Return elapsed milliseconds from perf_counter start time."""
    return int((time.perf_counter() - start) * 1000)


def _fallback_outline(keyword: str, serp_data: dict) -> str:
    """Create a deterministic outline when the research agent is unavailable."""
    title = f"# {keyword.title()}: Complete Guide"
    serp_headings = [h for h in serp_data.get("headings", []) if h and len(h.strip()) > 5][:6]

    sections = [
        "## What Is " + keyword.title() + "?\n- Define the topic clearly and set expectations for readers.\n### Why It Matters\n### Common Misconceptions",
        "## Core Features to Look For\n- Break down must-have capabilities and evaluation criteria.\n### Accuracy and Context\n### Workflow Integration",
        "## How to Choose the Right Option\n- Explain a practical decision framework based on use case and budget.\n### Use Case Fit\n### Cost vs Value",
        "## Best Practices for Real-World Use\n- Show how to adopt safely and effectively in day-to-day work.\n### Quality Control\n### Security and Privacy",
        "## Common Mistakes and How to Avoid Them\n- Identify pitfalls and corrective actions.\n### Over-Reliance Risks\n### Validation Checklist",
        "## Conclusion\n- Summarize key takeaways and next steps with a clear CTA.",
    ]

    if serp_headings:
        sections.insert(
            2,
            "## Related Topics from Current Search Results\n"
            + "\n".join(f"### {h}" for h in serp_headings[:4]),
        )

    return "\n\n".join([title, "## Introduction\n- Briefly introduce the problem and promise a practical guide."] + sections)


def _fallback_draft(keyword: str, tone: str, outline: str) -> str:
    """Create a deterministic markdown draft when the writer agent fails."""
    heading_lines = [line.strip() for line in outline.splitlines() if line.startswith("## ")]
    if not heading_lines:
        heading_lines = [
            "## Introduction",
            "## Key Concepts",
            "## Best Practices",
            "## Common Mistakes",
            "## Conclusion",
        ]

    style_hint = {
        "informative": "clear and educational",
        "persuasive": "benefit-driven and action-oriented",
        "casual": "friendly and conversational",
        "professional": "formal and business-oriented",
    }.get(tone, "clear and educational")

    blocks = [
        f"# {keyword.title()}\n",
        f"This article explains **{keyword}** in a {style_hint} way and focuses on practical outcomes for readers.",
        "> **Quick Answer:** The best approach to **{keyword}** is to combine clear criteria, practical testing, and continuous refinement.",
    ]

    for h2 in heading_lines[:8]:
        heading = h2.removeprefix("## ").strip()
        blocks.append(
            "\n" + h2 + "\n"
            + f"**{heading}** is a critical part of succeeding with **{keyword}**. "
            + "Start by defining goals, selecting measurable criteria, and documenting assumptions before execution. "
            + "Then iterate based on outcomes and feedback to improve reliability and impact.\n\n"
            + "- Define the target outcome and constraints\n"
            + "- Test with small experiments before scaling\n"
            + "- Track quality, risk, and business value\n"
            + "- Refine the process using real-world results\n"
        )

    blocks.append(
        "\n## Conclusion\n"
        + f"To get better results with **{keyword}**, combine strategy, experimentation, and quality controls. "
        + "Apply the checklist from this guide and adapt it to your context for consistent progress."
    )

    return "\n".join(blocks)


def _fallback_seo(keyword: str, draft_blog: str) -> str:
    """Apply minimal SEO polish when the SEO agent is unavailable."""
    meta = (
        f"<!-- META: Learn {keyword} with practical steps, key criteria, and proven tactics to improve outcomes while keeping quality high. -->"
    )
    if draft_blog.lstrip().startswith("<!-- META:"):
        return draft_blog
    return f"{meta}\n{draft_blog}"


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "Blog Engine API is running."}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


# ─── SERP Scraping Endpoint ───────────────────────────────────────────────────

@app.post("/api/scrape", response_model=SerpResponse, tags=["Scraping"])
async def scrape_endpoint(req: GenerateRequest):
    """
    Phase 1: Scrape top 3 SERP results for the given keyword.
    Returns combined text and identified headings.
    """
    try:
        result = await asyncio.wait_for(
            scrape_serp(req.keyword),
            timeout=SCRAPE_TIMEOUT_SECONDS,
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="SERP scraping timed out after 30s.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


# ─── Full Blog Generation Pipeline ───────────────────────────────────────────

@app.post("/api/generate", response_model=BlogGenerationResponse, tags=["Generation"])
async def generate_blog(req: GenerateRequest):
    """
    Full pipeline:
      1. Scrape SERP  →  2. Research Agent  →  3. Writer Agent
      →  4. SEO Editor Agent  →  5. Validation metrics
    Returns the final blog markdown + SEO/readability metrics.
    """
    keyword = req.keyword.strip()
    if not keyword:
        raise HTTPException(status_code=400, detail="'keyword' must not be empty.")
    tone = req.tone or "informative"
    pipeline_start = time.perf_counter()
    stage_timings_ms: dict[str, int] = {}
    stage_status: dict[str, str] = {}

    scrape_start = time.perf_counter()
    try:
        # Phase 1 — SERP
        serp_data = await asyncio.wait_for(scrape_serp(keyword), timeout=SCRAPE_TIMEOUT_SECONDS)
        stage_status["scrape"] = "ok"
    except asyncio.TimeoutError:
        stage_timings_ms["scrape"] = _elapsed_ms(scrape_start)
        stage_status["scrape"] = "timeout"
        raise HTTPException(status_code=504, detail="SERP scraping timed out.")
    except Exception as e:
        stage_timings_ms["scrape"] = _elapsed_ms(scrape_start)
        stage_status["scrape"] = "error"
        raise HTTPException(status_code=500, detail=f"SERP scraping error: {str(e)}")
    stage_timings_ms["scrape"] = _elapsed_ms(scrape_start)

    pipeline_warnings: list[str] = []

    research_start = time.perf_counter()
    try:
        # Phase 2 — Research Agent (outline)
        outline = await asyncio.wait_for(
            asyncio.to_thread(run_research, serp_data, keyword),
            timeout=RESEARCH_TIMEOUT_SECONDS,
        )
        if not str(outline).strip():
            raise ValueError("Research agent returned empty outline.")
        stage_status["research"] = "ok"
    except asyncio.TimeoutError:
        outline = _fallback_outline(keyword, serp_data)
        pipeline_warnings.append("research_timeout_fallback")
        stage_status["research"] = "fallback_timeout"
    except Exception:
        outline = _fallback_outline(keyword, serp_data)
        pipeline_warnings.append("research_error_fallback")
        stage_status["research"] = "fallback_error"
    stage_timings_ms["research"] = _elapsed_ms(research_start)

    writer_start = time.perf_counter()
    try:
        # Phase 2 — Writer Agent (draft)
        draft_blog = await asyncio.wait_for(
            asyncio.to_thread(run_writer, outline, keyword, tone),
            timeout=WRITER_TIMEOUT_SECONDS,
        )
        if not str(draft_blog).strip():
            raise ValueError("Writer agent returned empty draft.")
        stage_status["writer"] = "ok"
    except asyncio.TimeoutError:
        draft_blog = _fallback_draft(keyword, tone, outline)
        pipeline_warnings.append("writer_timeout_fallback")
        stage_status["writer"] = "fallback_timeout"
    except Exception:
        draft_blog = _fallback_draft(keyword, tone, outline)
        pipeline_warnings.append("writer_error_fallback")
        stage_status["writer"] = "fallback_error"
    stage_timings_ms["writer"] = _elapsed_ms(writer_start)

    seo_start = time.perf_counter()
    try:
        # Phase 2 — SEO Editor Agent (final polish)
        final_blog = await asyncio.wait_for(
            asyncio.to_thread(run_seo_editor, draft_blog, keyword),
            timeout=SEO_TIMEOUT_SECONDS,
        )
        if not str(final_blog).strip():
            raise ValueError("SEO agent returned empty final blog.")
        stage_status["seo"] = "ok"
    except asyncio.TimeoutError:
        final_blog = _fallback_seo(keyword, draft_blog)
        pipeline_warnings.append("seo_timeout_fallback")
        stage_status["seo"] = "fallback_timeout"
    except Exception:
        final_blog = _fallback_seo(keyword, draft_blog)
        pipeline_warnings.append("seo_error_fallback")
        stage_status["seo"] = "fallback_error"
    stage_timings_ms["seo"] = _elapsed_ms(seo_start)

    # Phase 3 — Validation
    readability_start = time.perf_counter()
    try:
        readability = await asyncio.wait_for(
            asyncio.to_thread(get_readability_scores, final_blog),
            timeout=READABILITY_TIMEOUT_SECONDS,
        )
        stage_status["readability"] = "ok"
    except Exception:
        readability = {
            "readability_score": 0,
            "flesch_reading_ease": 0.0,
            "flesch_kincaid_grade": 0.0,
            "gunning_fog": 0.0,
            "smog_index": 0.0,
            "automated_readability_index": 0.0,
            "coleman_liau_index": 0.0,
            "dale_chall_readability_score": 0.0,
        }
        pipeline_warnings.append("readability_error_defaulted")
        stage_status["readability"] = "fallback_error"
    stage_timings_ms["readability"] = _elapsed_ms(readability_start)

    ai_start = time.perf_counter()
    try:
        ai_scores = await asyncio.wait_for(
            asyncio.to_thread(get_ai_detection_score, final_blog),
            timeout=AI_DETECTION_TIMEOUT_SECONDS,
        )
        stage_status["ai_detection"] = "ok"
    except Exception:
        ai_scores = {
            "ai_detection_percentage": 50.0,
            "naturalness_score": 50.0,
            "detection_method": "fallback",
            "detection_confidence": "low",
        }
        pipeline_warnings.append("ai_detection_error_defaulted")
        stage_status["ai_detection"] = "fallback_error"
    stage_timings_ms["ai_detection"] = _elapsed_ms(ai_start)

    metrics = {
        **readability,
        **ai_scores,
        "word_count": len(final_blog.split()),
        "heading_count": final_blog.count("\n#"),
        "pipeline_warnings": pipeline_warnings,
        "stage_timings_ms": stage_timings_ms,
        "stage_status": stage_status,
        "total_time_ms": _elapsed_ms(pipeline_start),
    }

    return BlogGenerationResponse(
        keyword=keyword,
        tone=tone,
        outline=outline,
        draft_blog=draft_blog,
        final_blog=final_blog,
        metrics=metrics,
    )


# ─── Metrics-only Endpoint (for testing) ─────────────────────────────────────

@app.post("/api/validate", tags=["Validation"])
async def validate_text(body: dict):
    """
    Accepts { "text": "..." } and returns readability + AI detection scores.
    Useful for testing the validation layer independently.
    """
    text = body.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="'text' field is required.")
    readability = await asyncio.wait_for(
        asyncio.to_thread(get_readability_scores, text),
        timeout=READABILITY_TIMEOUT_SECONDS,
    )
    ai_scores = await asyncio.wait_for(
        asyncio.to_thread(get_ai_detection_score, text),
        timeout=AI_DETECTION_TIMEOUT_SECONDS,
    )
    return {**readability, **ai_scores}


@app.post("/api/generate/debug", tags=["Generation"])
async def generate_blog_debug(req: GenerateRequest):
    """
    Diagnostics endpoint:
    runs the same generation pipeline but returns only timing/status metadata.
    """
    result = await generate_blog(req)
    return {
        "keyword": result.keyword,
        "tone": result.tone,
        "pipeline_warnings": result.metrics.get("pipeline_warnings", []),
        "stage_status": result.metrics.get("stage_status", {}),
        "stage_timings_ms": result.metrics.get("stage_timings_ms", {}),
        "total_time_ms": result.metrics.get("total_time_ms", 0),
        "word_count": result.metrics.get("word_count", 0),
    }
