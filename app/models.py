"""Pydantic models for request/response."""
from enum import Enum
from pydantic import BaseModel, Field

class Sentiment(str, Enum):
    positive = "positive"
    negative = "negative"
    neutral  = "neutral"
    mixed    = "mixed"

class AnalyzeRequest(BaseModel):
    text:          str = Field(..., min_length=5, max_length=2000,
                               description="Comment to analyze")
    question_code: str | None = Field(None,
                               description="Source question code (optional)")


class TopicAnalysis(BaseModel):
    topic:    str
    polarity: str  # positive | negative | neutral


class AnalyzeResponse(BaseModel):
    text:            str
    sentiment:       str    # positive | negative | neutral | mixed
    score:           float  = Field(..., ge=0.0, le=1.0)
    topics:          list[str]
    topic_polarity:  list[TopicAnalysis]
    suggested_action: str
    context:         str | None = None


class BatchRequest(BaseModel):
    comments: list[AnalyzeRequest] = Field(..., min_length=1, max_length=50)


class TopicSummary(BaseModel):
    topic:     str
    frequency: int
    pct:       float


class BatchResponse(BaseModel):
    total:            int
    results:          list[AnalyzeResponse]
    summary:          dict
    top_topics:       list[TopicSummary]
    critical_comments: list[str]
