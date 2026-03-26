# BlogForge — AI-Powered Blog Generation Engine

A full-stack, open-source blog generation engine that converts keyword intent into GEO-optimized, high-ranking content using **CrewAI**, **Ollama (llama3)**, **BeautifulSoup4**, and a **Next.js 14** dashboard.

---

## Architecture Overview

```
Keyword Input
     │
     ▼
┌──────────────────────────────────────────────────────┐
│  FastAPI  (port 8000)                                │
│                                                      │
│  POST /api/generate                                  │
│       │                                              │
│       ├─ 1. scraper.py  ──── SearXNG / DDG fallback  │
│       │       └─ BeautifulSoup4 → SERP JSON          │
│       │                                              │
│       ├─ 2. research_agent.py ─ CrewAI + llama3      │
│       │       └─ Gap analysis → Markdown outline     │
│       │                                              │
│       ├─ 3. writer_agent.py ── CrewAI + llama3       │
│       │       └─ Outline → 1500-2000 word draft      │
│       │                                              │
│       ├─ 4. seo_agent.py ───── CrewAI + llama3       │
│       │       └─ Draft → Keyword-compliant final     │
│       │                                              │
│       └─ 5. validation/                              │
│               ├─ readability.py  (textstat)          │
│               └─ ai_detector.py  (HuggingFace)       │
└──────────────────────────────────────────────────────┘
     │
     ▼
Next.js Dashboard (port 3000)
  ├─ Input form (keyword + tone)
  ├─ ProgressFlow (live pipeline steps)
  ├─ BlogDisplay  (Markdown preview)
  └─ MetricsPanel (SEO / readability / AI detection)
```

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.11+ | |
| Node.js | 18+ | |
| Ollama | latest | https://ollama.com |
| llama3 model | — | `ollama pull llama3` |
| SearXNG (optional) | — | Docker recommended; DDG fallback built-in |

---

## 1. Backend Setup

```bash
cd blog_engine_project/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify Ollama is running with llama3
ollama serve          # in a separate terminal
ollama pull llama3    # first time only

# Start FastAPI
uvicorn main:app --reload --port 8000
```

FastAPI Swagger UI → http://localhost:8000/docs

---

## 2. Frontend Setup

```bash
cd blog_engine_project/frontend

# Copy env file
cp .env.local.example .env.local

# Install dependencies
npm install

# Start Next.js dev server
npm run dev
```

Dashboard → http://localhost:3000

---

## 3. Test the Backend First (Postman / curl)

**Always validate the backend before touching the UI.**

### Health check
```bash
curl http://localhost:8000/health
# → {"status":"healthy"}
```

### SERP scrape only
```bash
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"keyword": "best productivity apps for developers"}'
```

Expected response:
```json
{
  "keyword": "best productivity apps for developers",
  "combined_text": "...",
  "headings": ["...", "..."],
  "source_urls": ["https://..."]
}
```

### Validation only (no LLM needed)
```bash
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a sample blog post about productivity. Developers often struggle..."}'
```

### Full generation pipeline (requires Ollama + llama3)
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"keyword": "best productivity apps for developers", "tone": "informative"}' \
  --max-time 600
```

> ⚠️ This will take **2–10 minutes** depending on your hardware. Set `--max-time 600`.

---

## 4. SearXNG Setup (Optional but Recommended)

The scraper prefers a local SearXNG instance for reliable SERP data.

```bash
# Quick Docker setup
docker run -d \
  -p 8888:8080 \
  -e BASE_URL="http://localhost:8888/" \
  searxng/searxng
```

If SearXNG is unavailable, the scraper **automatically falls back** to DuckDuckGo HTML search.

---

## 5. API Reference

### `POST /api/scrape`
| Field | Type | Description |
|-------|------|-------------|
| keyword | string | Target search keyword |
| tone | string? | Ignored in scrape-only mode |

### `POST /api/generate`
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| keyword | string | required | Target keyword |
| tone | string | "informative" | informative \| persuasive \| casual \| professional |

**Response:**
```json
{
  "keyword": "...",
  "tone": "...",
  "outline": "## Markdown outline...",
  "draft_blog": "## Raw draft...",
  "final_blog": "<!-- META: ... -->\n# Final blog...",
  "metrics": {
    "readability_score": 68,
    "flesch_reading_ease": 68.2,
    "flesch_kincaid_grade": 8.1,
    "gunning_fog": 10.4,
    "ai_detection_percentage": 42.5,
    "naturalness_score": 57.5,
    "detection_method": "heuristic",
    "detection_confidence": "medium",
    "word_count": 1723,
    "heading_count": 7
  }
}
```

### `POST /api/validate`
| Field | Type | Description |
|-------|------|-------------|
| text | string | Any text to analyze |

---

## 6. Timeouts

| Stage | Backend timeout | Frontend axios timeout |
|-------|----------------|----------------------|
| SERP scrape | 30s | — |
| Research agent | 120s | — |
| Writer agent | 180s | — |
| SEO agent | 120s | — |
| Total pipeline | ~7.5 min max | 10 min (600,000ms) |

If a stage times out, FastAPI returns `504 Gateway Timeout` with a descriptive message.

---

## 7. Project Structure

```
blog_engine_project/
├── backend/
│   ├── main.py                  # FastAPI app + CORS
│   ├── scraper.py               # Async SERP scraper (SearXNG + BS4)
│   ├── requirements.txt
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── research_agent.py    # CrewAI gap analysis → outline
│   │   ├── writer_agent.py      # CrewAI blog drafter
│   │   └── seo_agent.py         # CrewAI SEO editor + density check
│   └── validation/
│       ├── __init__.py
│       ├── readability.py       # textstat scores
│       └── ai_detector.py       # HuggingFace RoBERTa + heuristic fallback
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── postcss.config.js
│   ├── .env.local.example
│   ├── app/
│   │   ├── layout.tsx           # Root layout + fonts
│   │   ├── page.tsx             # Main dashboard
│   │   └── globals.css          # Tailwind + custom styles
│   ├── components/
│   │   ├── BlogDisplay.tsx      # Markdown renderer
│   │   ├── MetricsPanel.tsx     # SEO/readability/AI gauges
│   │   └── ProgressFlow.tsx     # Pipeline step indicator
│   └── lib/
│       └── api.ts               # Axios client + typed API calls
│
└── README.md
```

---

## 8. Troubleshooting

**`Connection refused` on `/api/generate`**
→ Ensure `uvicorn main:app --reload --port 8000` is running.

**`Ollama connection error`**
→ Run `ollama serve` in a separate terminal. Verify with `curl http://localhost:11434`.

**`ModuleNotFoundError: crewai`**
→ Activate the venv: `source .venv/bin/activate`, then `pip install -r requirements.txt`.

**CORS error in browser**
→ The `CORSMiddleware` in `main.py` allows `http://localhost:3000`. Ensure Next.js runs on port 3000.

**Generation takes >10 minutes**
→ llama3 on CPU is slow. Consider using `llama3:8b` (smaller) or running with GPU via CUDA.

**HuggingFace model download fails**
→ The AI detector gracefully falls back to a heuristic scorer. No action needed.

---

## License

MIT — build freely, deploy responsibly.