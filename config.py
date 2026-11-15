"""Shared settings for the FlipRate harness."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
CACHE_DIR = ROOT / "cache"
QUESTIONS_PATH = DATA_DIR / "questions.json"

SEED = 42
LETTERS = "ABCD"

# 4 required subjects + 6 mixed (medicine, security, statistics-heavy social science,
# history, philosophy, moral reasoning).
SUBJECTS = [
    "college_physics",
    "formal_logic",
    "professional_law",
    "high_school_mathematics",
    "college_medicine",
    "computer_security",
    "econometrics",
    "high_school_us_history",
    "philosophy",
    "moral_scenarios",
]
N_PER_SUBJECT = 10

# Model IDs checked against the provider model lists on 2026-11-15.
#   temperature: None means "do not send it" (current Claude models reject the
#                parameter; see README).
#   max_tokens:  300 for plain chat models. Reasoning models spend hidden
#                reasoning tokens out of the same budget, so they get more room.
#   extra:       provider-specific keyword arguments passed through as-is.
MODELS = {
    "claude": {
        "provider": "anthropic",
        "id": "claude-opus-5-5",
        "temperature": None,
        "max_tokens": 2000,
        "extra": {"output_config": {"effort": "low"}},
    },
    "llama": {
        "provider": "groq",
        "id": "llama-3.3-70b-versatile",
        "temperature": 0,
        "max_tokens": 300,
        "extra": {},
    },
    "gpt-oss": {
        "provider": "groq",
        "id": "openai/gpt-oss-120b",
        "temperature": 0,
        "max_tokens": 1500,
        "extra": {"reasoning_effort": "low"},
    },
}

# Concurrent requests per provider. Groq's free tier is tightly rate limited.
CONCURRENCY = {"anthropic": 6, "groq": 2}
MAX_TRIES = 6
# A retry-after longer than this means a daily quota, not a burst limit: stop
# and let the user resume later (the cache keeps everything already done).
MAX_RETRY_AFTER_S = 300
