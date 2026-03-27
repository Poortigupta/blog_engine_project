"""
main.py — FastAPI application entry point
Run with: uvicorn main:app --reload --port 8000
"""

import asyncio
import traceback
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
            timeout=30.0,
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
    try:
        # Phase 1 — SERP
        serp_data = await asyncio.wait_for(scrape_serp(req.keyword), timeout=30.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="SERP scraping timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SERP scraping error: {str(e)}")

    try:
        # Phase 2 — Research Agent (outline)
        outline = await asyncio.wait_for(
            asyncio.to_thread(run_research, serp_data, req.keyword),
            timeout=120.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Research agent timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research agent error: {str(e)}")

    try:
        # Phase 2 — Writer Agent (draft)
        draft_blog = await asyncio.wait_for(
            asyncio.to_thread(run_writer, outline, req.keyword, req.tone),
            timeout=180.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Writer agent timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Writer agent error: {str(e)}")

    try:
        # Phase 2 — SEO Editor Agent (final polish)
        final_blog = await asyncio.wait_for(
            asyncio.to_thread(run_seo_editor, draft_blog, req.keyword),
            timeout=120.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="SEO agent timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SEO agent error: {str(e)}")

    # Phase 3 — Validation
    readability = get_readability_scores(final_blog)
    ai_scores = get_ai_detection_score(final_blog)

    metrics = {
        **readability,
        **ai_scores,
        "word_count": len(final_blog.split()),
        "heading_count": final_blog.count("\n#"),
    }

    return BlogGenerationResponse(
        keyword=req.keyword,
        tone=req.tone,
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
    readability = get_readability_scores(text)
    ai_scores = get_ai_detection_score(text)
    return {**readability, **ai_scores}
