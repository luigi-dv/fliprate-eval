"""Shared settings for the FlipRate harness.

API keys and the four model IDs come from `.env` (see `.env.example`):
    ANTHROPIC_API_KEY, GROQ_API_KEY
    ANTHROPIC_CLAUDE_MODEL_SM, ANTHROPIC_CLAUDE_MODEL_LG   (Anthropic)
    OPEN_AI_MODEL, META_MODEL                              (both served by Groq)
"""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
CACHE_DIR = ROOT / "cache"
QUESTIONS_PATH = DATA_DIR / "questions.json"

SEED = 42
LETTERS = "ABCD"

# Questions per MMLU subject (100 in total). Weighted towards subjects where
# strong models still make mistakes, so the "initially wrong" (correction)
# subgroup is not tiny. high_school_mathematics is kept small: it is easy.
SUBJECT_COUNTS = {
    "formal_logic": 14,
    "professional_law": 14,
    "college_physics": 12,
    "college_mathematics": 12,
    "abstract_algebra": 10,
    "econometrics": 10,
    "moral_scenarios": 8,
    "professional_accounting": 8,
    "global_facts": 6,
    "high_school_mathematics": 6,
}

GROQ_MAX_TOKENS = 150  # free tier: 200K tokens per day per model


def _anthropic_spec(model_id):
    """Request settings that turn extended thinking off for a Claude model.

    Current Claude models reject `temperature`, so it is never sent.
    """
    model_id = model_id or ""
    if model_id.startswith(("claude-opus-5-5", "claude-fable", "claude-mythos")):
        # These models cannot run without thinking (the API returns a 400 for
        # thinking=disabled). Lowest effort is the closest available setting;
        # thinking tokens count against max_tokens, hence the larger limit.
        extra, max_tokens = {"output_config": {"effort": "low"}}, 2000
    elif model_id.startswith("claude-sonnet-5-5"):
        extra, max_tokens = {"thinking": {"type": "between_tools"}}, 300
    else:
        extra, max_tokens = {"thinking": {"type": "disabled"}}, 300
    return {"provider": "anthropic", "id": model_id, "temperature": None,
            "max_tokens": max_tokens, "extra": extra}


# Order here is the order used in tables and figures.
MODELS = {
    "claude-sm": _anthropic_spec(os.environ.get("ANTHROPIC_CLAUDE_MODEL_SM")),
    "claude-lg": _anthropic_spec(os.environ.get("ANTHROPIC_CLAUDE_MODEL_LG")),
    "gpt-oss": {
        "provider": "groq",
        "id": os.environ.get("OPEN_AI_MODEL"),
        "temperature": 0,
        "max_tokens": GROQ_MAX_TOKENS,
        "extra": {"reasoning_effort": "low"},
    },
    "llama": {
        "provider": "groq",
        "id": os.environ.get("META_MODEL"),
        "temperature": 0,
        "max_tokens": GROQ_MAX_TOKENS,
        "extra": {},
    },
}

# Concurrent requests per provider. Groq's free tier is tightly rate limited.
CONCURRENCY = {"anthropic": 6, "groq": 2}
MAX_TRIES = 6
# A retry-after longer than this means a daily quota, not a burst limit: stop
# and let the user resume later (the cache keeps everything already done).
MAX_RETRY_AFTER_S = 300
