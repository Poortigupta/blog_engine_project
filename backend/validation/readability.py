"""
validation/readability.py — Readability scoring via textstat.
Strips markdown syntax before scoring so the LLM's formatting
doesn't inflate/deflate sentence complexity metrics.
"""

import re
import textstat


def _strip_markdown(text: str) -> str:
    """Remove common markdown syntax for cleaner readability scoring."""
    # Remove code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Remove inline code
    text = re.sub(r"`[^`]+`", "", text)
    # Remove headings markers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italic
    text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
    # Remove blockquotes
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)
    # Remove bullets
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    # Remove HTML comments
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Remove links
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def get_readability_scores(text: str) -> dict:
    """
    Returns a dictionary of readability metrics using textstat.

    Scores:
      - flesch_reading_ease: 0-100 (higher = easier; aim for 50-70 for web content)
      - flesch_kincaid_grade: US grade level
      - gunning_fog:          Fog index (aim for ≤12)
      - smog_index:           SMOG grade level
      - automated_readability_index: ARI grade
      - coleman_liau_index:   Coleman-Liau grade
      - dale_chall_readability_score: Dale-Chall score
      - readability_score:    Normalized 0-100 score (derived from Flesch)
    """
    clean = _strip_markdown(text)

    flesch = textstat.flesch_reading_ease(clean)
    fk_grade = textstat.flesch_kincaid_grade(clean)
    fog = textstat.gunning_fog(clean)
    smog = textstat.smog_index(clean)
    ari = textstat.automated_readability_index(clean)
    coleman = textstat.coleman_liau_index(clean)
    dale_chall = textstat.dale_chall_readability_score(clean)

    # Normalized 0-100 readability score
    # Flesch 0-100: higher is better; we pass through directly, clamped
    readability_score = max(0, min(100, int(flesch)))

    return {
        "readability_score": readability_score,
        "flesch_reading_ease": round(flesch, 1),
        "flesch_kincaid_grade": round(fk_grade, 1),
        "gunning_fog": round(fog, 1),
        "smog_index": round(smog, 1),
        "automated_readability_index": round(ari, 1),
        "coleman_liau_index": round(coleman, 1),
        "dale_chall_readability_score": round(dale_chall, 1),
    }