"""
Sentiment analysis engine using Gemini.
Processes plain text only — no personal data.
"""
from __future__ import annotations

import json
from google import genai

from app.config import GEMINI_API_KEY, GEMINI_MODEL, VALID_TOPICS
from app.models import AnalyzeResponse, TopicAnalysis

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not configured")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


PROMPT_TEMPLATE = """Analyze the following teaching evaluation comment.

COMMENT: "{text}"
CONTEXT: {context}

Respond ONLY with a valid JSON object with this exact structure:
{{
  "sentiment": "positive|negative|neutral|mixed",
  "score": 0.0-1.0,
  "topics": ["topic1", "topic2"],
  "topic_polarity": [{{"topic": "...", "polarity": "positive|negative|neutral"}}],
  "suggested_action": "one concrete improvement action"
}}

Valid topics: {topics}
- score: sentiment confidence (0=very negative, 0.5=neutral, 1=very positive)
- topics: detected topics (can be empty list)
- suggested_action: if positive reinforce it; if negative suggest concrete improvement
- Respond ONLY the JSON, no markdown, no explanation"""


async def analyze_comment(
    text: str,
    context: str | None = None,
) -> AnalyzeResponse:
    """
    Analyzes a comment and returns sentiment, topics and suggested action.
    SECURITY: Receives plain text only — no IDs or personal data.
    """
    ctx     = context or "teaching evaluation comment"
    prompt  = PROMPT_TEMPLATE.format(
        text    = text[:1000],
        context = ctx,
        topics  = ", ".join(VALID_TOPICS),
    )

    client   = get_client()
    response = client.models.generate_content(
        model    = GEMINI_MODEL,
        contents = prompt,
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except Exception:
        raise ValueError(f"Invalid JSON from Gemini: {raw}")

    topic_polarity = [
        TopicAnalysis(topic=t["topic"], polarity=t["polarity"])
        for t in data.get("topic_polarity", [])
    ]

    return AnalyzeResponse(
        text             = text,
        sentiment        = data.get("sentiment", "neutral"),
        score            = float(data.get("score", 0.5)),
        topics           = [
                                t
                                for t in data.get("topics", [])
                                if t in VALID_TOPICS
                            ],
        topic_polarity   = topic_polarity,
        suggested_action = data.get("suggested_action", "No action suggested"),
        context          = context,
    )
