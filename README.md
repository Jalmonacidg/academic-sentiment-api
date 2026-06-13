# Academic Sentiment API

Sentiment and topic classifier for academic teaching evaluation comments, powered by **Google Gemini 2.5 Flash**.

Given a free-text comment from a student teaching evaluation, the API returns:
- **Sentiment** — `positive | negative | neutral | mixed`
- **Score** — confidence float from 0.0 (very negative) to 1.0 (very positive)
- **Topics** — detected pedagogical topics (methodology, communication, assessment, etc.)
- **Topic polarity** — sentiment per topic
- **Suggested action** — one concrete improvement recommendation

---

## Requirements

| Tool | Version |
|------|---------|
| Docker | ≥ 24 |
| Google Gemini API Key | free tier works |

Get a free key at <https://aistudio.google.com/apikey>.

---

## Build the image

```bash
docker build -t academic-sentiment-api .
```

Or pull from GHCR:

```bash
docker pull ghcr.io/jalmonacidg/academic-sentiment-api:latest
docker tag  ghcr.io/jalmonacidg/academic-sentiment-api:latest academic-sentiment-api
```

---

## Run

```bash
docker run --rm -p 8000:8000 -e GEMINI_API_KEY=your_key_here academic-sentiment-api
```

The service starts at `http://localhost:8000`.

Optional env vars:

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | — | **Required.** Google Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Model to use |

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Service info |
| `GET` | `/health` | Health check |
| `POST` | `/analyze` | Analyze a single comment |
| `POST` | `/analyze/batch` | Analyze up to 50 comments |
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/docs` | Interactive Swagger UI |

---

## Example: single comment

**Request:**

```bash
curl -s -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The professor explains the topics very clearly and always arrives on time, but the exams feel disconnected from what was taught in class.",
    "question_code": "TEACHER_COMMENT"
  }' | python3 -m json.tool
```

**Response:**

```json
{
  "text": "The professor explains the topics very clearly and always arrives on time, but the exams feel disconnected from what was taught in class.",
  "sentiment": "mixed",
  "score": 0.55,
  "topics": ["methodology", "punctuality", "assessment"],
  "topic_polarity": [
    { "topic": "methodology",  "polarity": "positive" },
    { "topic": "punctuality",  "polarity": "positive" },
    { "topic": "assessment",   "polarity": "negative" }
  ],
  "suggested_action": "Review assessment alignment with course content; ensure exams reflect topics covered during lectures.",
  "context": "feedback about the teacher"
}
```

---

## Example: batch analysis

```bash
curl -s -X POST http://localhost:8000/analyze/batch \
  -H "Content-Type: application/json" \
  -d '{
    "comments": [
      { "text": "Excellent professor, very dedicated and clear in explanations." },
      { "text": "The course materials are outdated and the grading criteria are never explained." },
      { "text": "Good teacher overall, but office hours are hard to attend." }
    ]
  }' | python3 -m json.tool
```

The batch response includes per-comment results plus an aggregated **summary** (sentiment distribution, average score), the **top 5 topics** by frequency, and a list of the most **critical comments** (score < 0.35).

---

## Health check

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0","uptime_s":12.3,"model":"gemini"}
```

---

## Development

```bash
# Install dependencies (requires uv)
uv pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .
ruff format --check .

# Start locally (requires .env with GEMINI_API_KEY)
cp .env.example .env
uvicorn app.main:app --reload
```

---

## Project structure

```
academic-sentiment-api/
├── app/
│   ├── main.py        # FastAPI app, endpoints
│   ├── analyzer.py    # Gemini integration, prompt
│   ├── models.py      # Pydantic request/response models
│   └── config.py      # Env-var configuration
├── tests/
│   └── test_api.py    # pytest tests (mocked, no real API calls)
├── scripts/
│   └── generate_dummy_data.py  # Dev helper for anonymized test data
├── Dockerfile
├── pyproject.toml     # Dependencies + ruff + pytest config
├── .env.example
├── .gitignore
└── .dockerignore
```

---

## Extra points checklist

- [x] `.gitignore` + `.dockerignore` — no secrets committed
- [x] Dockerfile: `python:3.12-slim` base + `uv` con lockfile (`uv.lock`) + orden óptimo de capas
- [x] Imagen publicada en GHCR — `ghcr.io/jalmonacidg/academic-sentiment-api:latest`
- [x] CI con GitHub Actions — lint + test + build/push, tag por SHA (`sha-<commit>`) y `latest`
- [x] `pytest` tests — corren sin API key real (mocked)
- [x] `ruff` lint configurado (reglas `E`, `F`, `I`)
- [x] `/metrics` — endpoint Prometheus via `prometheus-fastapi-instrumentator`
- [x] API key inyectada en runtime via `-e GEMINI_API_KEY=...`, nunca en la imagen

---

## Valid topic codes

| Code | Description |
|------|-------------|
| `methodology` | Teaching methods and class dynamics |
| `punctuality` | Attendance and time management |
| `subject_mastery` | Domain knowledge and depth |
| `communication` | Clarity and interaction with students |
| `assessment` | Exams, grading, and feedback |
| `resources` | Materials, slides, bibliography |
| `attitude` | Disposition, empathy, approachability |
| `other` | Anything not covered above |

## Valid question codes (`question_code`)

| Code | Context |
|------|---------|
| `TEACHER_COMMENT` | Feedback about the teacher |
| `COURSE_COMMENT` | Feedback about the course |
| `LEARNING` | Learning outcomes |
| `FEEDBACK` | Feedback and improvement |
| `RECOMMENDATION` | General recommendation |
