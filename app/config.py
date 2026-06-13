"""Centralized configuration via environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL:   str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
APP_VERSION:    str = "0.1.0"
APP_NAME:       str = "Academic Sentiment API"

VALID_TOPICS = [
    "methodology",
    "punctuality",
    "subject_mastery",
    "communication",
    "assessment",
    "resources",
    "attitude",
    "other",
]

QUESTION_CONTEXT_MAP = {
    "TEACHER_COMMENT": "feedback about the teacher",
    "COURSE_COMMENT":  "feedback about the course",
    "LEARNING":        "learning outcomes",
    "FEEDBACK":        "feedback and improvement",
    "RECOMMENDATION":  "general recommendation",
}
