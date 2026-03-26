"""
validation/ai_detector.py — AI detection & naturalness scoring.

Uses a local HuggingFace RoBERTa-based classifier to estimate
the probability that the text was written by an AI.

Model: roberta-base-openai-detector (Hello-SimpleAI/chatgpt-detector-roberta)
Falls back to a heuristic mock if the model is unavailable (no internet / GPU).
"""

import re
import math
import warnings
from functools import lru_cache

# Suppress transformers noise
warnings.filterwarnings("ignore")

_pipeline_cache = None


def _get_pipeline():
    """Lazy-load the HuggingFace pipeline; cache after first load."""
    global _pipeline_cache
    if _pipeline_cache is not None:
        return _pipeline_cache
    try:
        from transformers import pipeline
        _pipeline_cache = pipeline(
            "text-classification",
            model="Hello-SimpleAI/chatgpt-detector-roberta",
            truncation=True,
            max_length=512,
        )
        return _pipeline_cache
    except Exception:
        return None


def _heuristic_ai_score(text: str) -> float:
    """
    Heuristic fallback when the HuggingFace model is unavailable.
    Returns estimated AI probability (0.0–1.0).

    Heuristics used:
      - Sentence length variance (AI tends to be uniform)
      - Passive voice frequency
      - Transition word density (AI overuses transitions)
      - Lexical diversity (type-token ratio)
    """
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    if not sentences:
        return 0.5

    # Sentence length variance (lower variance → more AI-like)
    lengths = [len(s.split()) for s in sentences]
    avg_len = sum(lengths) / len(lengths)
    variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
    variance_score = max(0, 1 - (variance / 200))  # 0=human, 1=AI

    # Passive voice proxy
    passive_pattern = re.compile(r"\b(is|are|was|were|be|been|being)\s+\w+ed\b", re.I)
    passive_ratio = len(passive_pattern.findall(text)) / max(len(sentences), 1)
    passive_score = min(passive_ratio / 0.3, 1.0)

    # Transition words (AI loves these)
    transitions = [
        "furthermore", "moreover", "additionally", "consequently",
        "therefore", "in conclusion", "in summary", "it is worth noting",
        "it should be noted", "on the other hand", "as a result",
    ]
    words_lower = text.lower()
    transition_count = sum(words_lower.count(t) for t in transitions)
    transition_score = min(transition_count / 10, 1.0)

    # Lexical diversity (TTR) — low TTR = more AI
    words = re.findall(r"\w+", text.lower())
    ttr = len(set(words)) / max(len(words), 1)
    diversity_score = max(0, 1 - (ttr / 0.6))

    ai_probability = (
        variance_score * 0.30
        + passive_score * 0.20
        + transition_score * 0.25
        + diversity_score * 0.25
    )

    return round(min(max(ai_probability, 0.0), 1.0), 3)


def get_ai_detection_score(text: str) -> dict:
    """
    Returns AI detection metrics for the provided text.

    Returns:
      - ai_detection_percentage:  0-100 (higher = more AI-like)
      - naturalness_score:        0-100 (higher = more human-like)
      - detection_method:         "model" | "heuristic"
      - confidence:               "high" | "medium" | "low"
    """
    # Chunk text for model (max 512 tokens ≈ ~380 words)
    words = text.split()
    chunk_size = 380
    chunks = [" ".join(words[i : i + chunk_size]) for i in range(0, min(len(words), chunk_size * 3), chunk_size)]

    pipe = _get_pipeline()

    if pipe is not None:
        try:
            scores = []
            for chunk in chunks[:3]:  # max 3 chunks
                result = pipe(chunk)[0]
                # Label is either "LABEL_0" (human) or "LABEL_1" (AI)
                label = result["label"]
                score = result["score"]
                ai_prob = score if "1" in label or "ai" in label.lower() else (1 - score)
                scores.append(ai_prob)

            avg_ai_prob = sum(scores) / len(scores)
            method = "model"
            confidence = "high" if len(scores) >= 2 else "medium"
        except Exception:
            avg_ai_prob = _heuristic_ai_score(text)
            method = "heuristic"
            confidence = "low"
    else:
        avg_ai_prob = _heuristic_ai_score(text)
        method = "heuristic"
        confidence = "medium"

    ai_pct = round(avg_ai_prob * 100, 1)
    naturalness = round(100 - ai_pct, 1)

    return {
        "ai_detection_percentage": ai_pct,
        "naturalness_score": naturalness,
        "detection_method": method,
        "detection_confidence": confidence,
    }