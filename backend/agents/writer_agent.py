"""
writer_agent.py — CrewAI Writer Agent
Takes the research outline and drafts a comprehensive, GEO-optimized blog.
Enforces Snippet Readiness Probability through structured formatting.
"""

from crewai import Agent, Task, Crew
from langchain_community.llms import Ollama

OLLAMA_BASE_URL = "http://localhost:11434"

TONE_INSTRUCTIONS = {
    "informative": "Write in a clear, authoritative, third-person educational tone.",
    "persuasive": "Write in a persuasive tone that builds urgency and drives the reader toward action.",
    "casual": "Write in a friendly, conversational first-person tone as if talking to a friend.",
    "professional": "Write in a formal, corporate-appropriate tone suitable for B2B audiences.",
}


def _build_llm():
    return Ollama(model="llama3", base_url=OLLAMA_BASE_URL, request_timeout=180.0)


def run_writer(outline: str, keyword: str, tone: str = "informative") -> str:
    """
    Drafts a full markdown blog from the provided outline.

    Args:
        outline:  Markdown outline from the Research Agent
        keyword:  Target keyword for density enforcement
        tone:     Writing tone (informative | persuasive | casual | professional)

    Returns:
        Full markdown blog draft
    """
    llm = _build_llm()
    tone_instruction = TONE_INSTRUCTIONS.get(tone, TONE_INSTRUCTIONS["informative"])

    writer = Agent(
        role="Expert Blog Content Writer",
        goal=(
            f"Write a comprehensive, engaging 1500-2000 word blog post about '{keyword}' "
            "that ranks on Google and maximizes featured snippet chances."
        ),
        backstory=(
            "You are an expert content writer who specializes in creating SEO-optimized "
            "long-form articles. You know how to write for both search engines and humans. "
            "Your articles consistently win featured snippets due to your formatting discipline."
        ),
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )

    task = Task(
        description=f"""
Using this outline, write a full blog post about **{keyword}**.

OUTLINE:
\"\"\"
{outline}
\"\"\"

TONE INSTRUCTION: {tone_instruction}

STRICT FORMATTING RULES (Snippet Readiness Protocol):
1. Use the exact H1, H2, H3 headings from the outline.
2. Start every H2 section with a 2-3 sentence **definition paragraph** — bold the key term being defined.
3. Use **bullet point lists** (3-5 items) for any process, list of tips, or comparison.
4. Include at least one "Quick Answer" box per article using this format:
   > **Quick Answer:** [1-2 sentence direct answer to the implied question of the heading]
5. Bold all key terms on first use in each section.
6. Write 150-200 words per H2 section minimum.
7. End with a conclusion + clear CTA paragraph.
8. Total article length: 1500-2000 words.
9. Do NOT include any meta commentary — return ONLY the final markdown blog content.
10. Keyword "{keyword}" must appear naturally at least once in the introduction, once in at least 3 H2 sections, and once in the conclusion.

Return ONLY the markdown blog. No preamble.
        """,
        expected_output="A complete 1500-2000 word markdown blog post with all formatting rules applied.",
        agent=writer,
    )

    crew = Crew(agents=[writer], tasks=[task], verbose=False)
    result = crew.kickoff()
    return str(result)