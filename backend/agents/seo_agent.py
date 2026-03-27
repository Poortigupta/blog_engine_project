"""
seo_agent.py — CrewAI SEO Editor Agent
Reviews the draft blog for keyword density compliance, meta optimization,
and structural SEO rules. Returns the final polished markdown.
"""

import re
from crewai import Agent, Task, Crew
from langchain_community.llms import Ollama

OLLAMA_BASE_URL = "http://localhost:11434"
TARGET_DENSITY_MIN = 0.015   # 1.5%
TARGET_DENSITY_MAX = 0.030   # 3.0%


def _keyword_density(text: str, keyword: str) -> float:
    """Calculate keyword density as a ratio."""
    words = re.findall(r"\w+", text.lower())
    kw_words = re.findall(r"\w+", keyword.lower())
    count = sum(
        1 for i in range(len(words) - len(kw_words) + 1)
        if words[i : i + len(kw_words)] == kw_words
    )
    return count / max(len(words), 1)


def _build_llm():
    return Ollama(model="llama3", base_url=OLLAMA_BASE_URL)


def run_seo_editor(draft: str, keyword: str) -> str:
    """
    Reviews and edits the draft blog for SEO compliance.

    Args:
        draft:    Markdown draft from the Writer Agent
        keyword:  Target keyword

    Returns:
        Final, SEO-polished markdown blog
    """
    density = _keyword_density(draft, keyword)
    word_count = len(draft.split())

    density_note = ""
    if density < TARGET_DENSITY_MIN:
        current_count = int(density * word_count)
        target_count = int(TARGET_DENSITY_MIN * word_count)
        needed = target_count - current_count
        density_note = (
            f"⚠️  DENSITY TOO LOW: '{keyword}' appears ~{current_count} times "
            f"({density*100:.2f}%). You MUST naturally add it ~{needed} more times to reach 1.5%."
        )
    elif density > TARGET_DENSITY_MAX:
        density_note = (
            f"⚠️  DENSITY TOO HIGH: '{keyword}' appears too frequently ({density*100:.2f}%). "
            "Remove some occurrences to reduce to ≤3%."
        )
    else:
        density_note = f"✅ Keyword density is {density*100:.2f}% — within target range."

    llm = _build_llm()

    seo_editor = Agent(
        role="SEO Content Editor",
        goal=(
            f"Ensure the blog about '{keyword}' is fully optimized for search engines "
            "without sacrificing readability or sounding spammy."
        ),
        backstory=(
            "You are a meticulous SEO editor with 10+ years of on-page optimization experience. "
            "You know Google's guidelines inside out. You fix keyword density issues, "
            "improve internal structure, and ensure every heading and paragraph serves a purpose."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    task = Task(
        description=f"""
Review and improve the following blog post about **{keyword}**.

KEYWORD DENSITY ANALYSIS: {density_note}

DRAFT BLOG:
\"\"\"
{draft}
\"\"\"

YOUR TASKS:
1. {density_note} — Fix keyword density as instructed above.
2. Verify every H2 heading contains either the exact keyword or a close semantic variant.
3. Ensure the first 100 words of the introduction contain the exact keyword at least once.
4. Check that the conclusion contains the exact keyword.
5. Add or improve the meta-description as an HTML comment at the very top:
   <!-- META: [150-160 char description with keyword] -->
6. Do NOT change the overall structure, tone, or content — only optimize for SEO.
7. Ensure all markdown formatting (bold, bullets, blockquotes) is preserved.
8. Return ONLY the final optimized markdown blog with the meta comment at the top.
        """,
        expected_output="The SEO-optimized markdown blog with a meta description comment at the top.",
        agent=seo_editor,
    )

    crew = Crew(agents=[seo_editor], tasks=[task], verbose=False)
    result = crew.kickoff()
    return str(result)


def compute_seo_score(text: str, keyword: str) -> int:
    """
    Heuristic SEO score (0–100) based on:
      - Keyword density (30 pts)
      - Word count (20 pts)
      - H2 count (20 pts)
      - Bullet point usage (15 pts)
      - Bold term usage (15 pts)
    """
    score = 0
    density = _keyword_density(text, keyword)

    # Density (0-30)
    if TARGET_DENSITY_MIN <= density <= TARGET_DENSITY_MAX:
        score += 30
    elif density > 0:
        score += 15

    # Word count (0-20)
    wc = len(text.split())
    if wc >= 1500:
        score += 20
    elif wc >= 800:
        score += 10

    # H2 count (0-20)
    h2_count = len(re.findall(r"^## ", text, re.MULTILINE))
    if h2_count >= 5:
        score += 20
    elif h2_count >= 3:
        score += 10

    # Bullet points (0-15)
    bullet_count = len(re.findall(r"^\s*[-*] ", text, re.MULTILINE))
    if bullet_count >= 10:
        score += 15
    elif bullet_count >= 5:
        score += 8

    # Bold terms (0-15)
    bold_count = len(re.findall(r"\*\*.+?\*\*", text))
    if bold_count >= 8:
        score += 15
    elif bold_count >= 4:
        score += 8

    return min(score, 100)