"""Basic API tests."""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

from app.main import app
from app.models import AnalyzeResponse, TopicAnalysis

MOCK_RESPONSE = AnalyzeResponse(
    text             = "The professor explains very clearly",
    sentiment        = "positive",
    score            = 0.85,
    topics           = ["methodology"],
    topic_polarity   = [TopicAnalysis(topic="methodology", polarity="positive")],
    suggested_action = "Keep current teaching methodology",
)


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_analyze_ok():
    with patch("app.main.analyze_comment", return_value=MOCK_RESPONSE):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            r = await client.post("/analyze", json={
                "text": "The professor explains very clearly"
            })
    assert r.status_code == 200
    data = r.json()
    assert data["sentiment"] == "positive"
    assert "methodology" in data["topics"]


@pytest.mark.asyncio
async def test_analyze_text_too_short():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.post("/analyze", json={"text": "ok"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_batch_ok():
    with patch("app.main.analyze_comment", return_value=MOCK_RESPONSE):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            r = await client.post("/analyze/batch", json={
                "comments": [
                    {"text": "The professor explains very clearly"},
                    {"text": "Assessments are too difficult and unclear"},
                ]
            })
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert "avg_score" in data["summary"]

@pytest.mark.asyncio
async def test_analyze_model_error():

    with patch(
        "app.main.analyze_comment",
        side_effect=Exception("Gemini unavailable")
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:

            r = await client.post(
                "/analyze",
                json={
                    "text": "The professor explains very clearly"
                }
            )

    assert r.status_code == 502
    assert "Model error" in r.json()["detail"]


@pytest.mark.asyncio
async def test_batch_all_fail():

    with patch(
        "app.main.analyze_comment",
        side_effect=Exception("Gemini unavailable")
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:

            r = await client.post(
                "/analyze/batch",
                json={
                    "comments": [
                        {"text": "Comment number one"},
                        {"text": "Comment number two"}
                    ]
                }
            )

    assert r.status_code == 502
    assert r.json()["detail"] == "Could not analyze any comment"
