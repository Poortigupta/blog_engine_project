"""
research_agent.py — CrewAI Research Agent
Ingests SERP data and produces a structured outline covering gaps.
Uses Ollama (llama3) as the local LLM backend.
"""

from crewai import Agent, Task, Crew
from langchain_community.llms import Ollama

OLLAMA_BASE_URL = "http://localhost:11434"


def _build_llm():
    return Ollama(model="llama3", base_url=OLLAMA_BASE_URL, request_timeout=120.0)


def run_research(serp_data: dict, keyword: str) -> str:
    """
    Takes SERP scrape output and keyword, returns a structured markdown outline
    that identifies content gaps vs. existing SERP results.

    Args:
        serp_data: dict with keys: combined_text, headings, source_urls
        keyword:   target keyword string

    Returns:
        Markdown outline string
    """
    llm = _build_llm()

    existing_headings = "\n".join(f"- {h}" for h in serp_data.get("headings", []))
    serp_excerpt = serp_data.get("combined_text", "")[:3000]

    researcher = Agent(
        role="Senior SEO Content Strategist",
        goal=(
            f"Analyze the top-ranking content for '{keyword}' and identify "
            "subtopics, angles, and questions that are underserved or missing."
        ),
        backstory=(
            "You are a veteran SEO strategist who has helped hundreds of sites "
            "reach page 1. You excel at spotting content gaps by reading SERP data "
            "and crafting outlines that outperform existing results."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    task = Task(
        description=f"""
You have scraped the top 3 Google results for the keyword: **{keyword}**

Existing headings from SERP:
{existing_headings}

SERP content excerpt:
\"\"\"
{serp_excerpt}
\"\"\"

Your job:
1. Identify 3-5 subtopics or angles that are MISSING or underexplored in the current SERP.
2. Create a comprehensive blog outline in markdown that covers:
   - A compelling H1 title (include the keyword naturally)
   - An introduction section
   - At least 5 H2 sections (include the gaps you identified)
   - At least 2 H3 subsections per H2
   - A conclusion / CTA section
3. For each H2, add a brief (1-sentence) description of what that section covers.

Return ONLY the markdown outline. No preamble, no explanation.
        """,
        expected_output="A detailed markdown blog outline with H1, H2s, H3s, and brief section descriptions.",
        agent=researcher,
    )

    crew = Crew(agents=[researcher], tasks=[task], verbose=False)
    result = crew.kickoff()
    return str(result)