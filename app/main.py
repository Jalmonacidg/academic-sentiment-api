"""
Academic Sentiment API
----------------------
Sentiment and topic classifier for academic teaching evaluation comments.

Security: Processes plain text only — no personal data or identifiers.

Usage:
    docker run --rm -p 8000:8000 -e GEMINI_API_KEY=... academic-sentiment-api
"""

from __future__ import annotations

import time
from collections import Counter

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.analyzer import analyze_comment
from app.config import APP_NAME, APP_VERSION, QUESTION_CONTEXT_MAP
from app.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    BatchRequest,
    BatchResponse,
    TopicSummary,
)

app = FastAPI(
    title=APP_NAME,
    description="Sentiment and topic analysis for academic teaching evaluations",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

_start_time = time.time()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/")
async def root():
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "uptime_s": round(time.time() - _start_time, 1),
        "model": "gemini",
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(body: AnalyzeRequest):
    """
    Analyze a single teaching evaluation comment.

    - **text**: comment to analyze (5-2000 chars)
    - **question_code**: source question code (optional)

    Returns sentiment, score, detected topics and suggested action.
    """
    context = None
    if body.question_code and body.question_code in QUESTION_CONTEXT_MAP:
        context = QUESTION_CONTEXT_MAP[body.question_code]

    try:
        result = await analyze_comment(body.text, context)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Parse error: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Model error: {e}")

    return result


@app.post("/analyze/batch", response_model=BatchResponse)
async def analyze_batch(body: BatchRequest):
    """
    Analyze a batch of comments (max 50).

    Returns individual analysis + aggregated summary with:
    - sentiment distribution
    - most frequent topics
    - critical comments highlighted
    """
    results = []
    errors = 0

    for item in body.comments:
        try:
            context = None
            if item.question_code and item.question_code in QUESTION_CONTEXT_MAP:
                context = QUESTION_CONTEXT_MAP[item.question_code]
            r = await analyze_comment(item.text, context)
            results.append(r)
        except Exception:
            errors += 1

    if not results:
        raise HTTPException(status_code=502, detail="Could not analyze any comment")

    sentiments = Counter(r.sentiment for r in results)
    total = len(results)

    summary = {
        "total": total,
        "errors": errors,
        "positive_pct": round(sentiments.get("positive", 0) / total * 100, 1),
        "negative_pct": round(sentiments.get("negative", 0) / total * 100, 1),
        "neutral_pct": round(sentiments.get("neutral", 0) / total * 100, 1),
        "mixed_pct": round(sentiments.get("mixed", 0) / total * 100, 1),
        "avg_score": round(sum(r.score for r in results) / total, 2),
    }

    all_topics = [t for r in results for t in r.topics]
    freq_topics = Counter(all_topics).most_common(5)
    top_topics = [
        TopicSummary(topic=t, frequency=f, pct=round(f / total * 100, 1))
        for t, f in freq_topics
    ]

    critical = [r.text[:120] for r in results if r.score < 0.35][:5]

    return BatchResponse(
        total=total,
        results=results,
        summary=summary,
        top_topics=top_topics,
        critical_comments=critical,
    )
