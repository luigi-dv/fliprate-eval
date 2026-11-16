"""Shared settings for the FlipRate harness.

API keys and the six model IDs come from `.env` (see `.env.example`):
    ANTHROPIC_API_KEY, GROQ_API_KEY
    ANTHROPIC_MODEL_XS_GEN_4, ANTHROPIC_MODEL_LG_GEN_4   (Claude 4.5 generation)
    ANTHROPIC_MODEL_XS_GEN_5, ANTHROPIC_MODEL_LG_GEN_5   (Claude 5.5 generation)
    GROQ_OPEN_AI_MODEL_XS, GROQ_OPEN_AI_MODEL_LG         (GPT-OSS, served by Groq)
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

# Output limits. They must be generous enough that no reply is cut off before
# its JSON ends. GPT-OSS and claude-opus-5-5 spend hidden reasoning tokens out
# of the same limit, so they get more room.
CLAUDE_MAX_TOKENS = 800
CLAUDE_THINKING_MAX_TOKENS = 2000
GROQ_MAX_TOKENS = 1500


def _anthropic_spec(model_id):
    """Request settings that turn extended thinking off for a Claude model.

    `temperature` is never sent: the API version used by the installed SDK
    (2026-10-21) rejects it for every Claude model, including the 4.5 ones.
    """
    model_id = model_id or ""
    if model_id.startswith(("claude-opus-5-5", "claude-fable", "claude-mythos")):
        # These models cannot run without thinking (the API returns a 400 for
        # thinking=disabled). Lowest effort is the closest available setting;
        # thinking tokens count against max_tokens, hence the larger limit.
        extra, max_tokens = {"output_config": {"effort": "low"}}, CLAUDE_THINKING_MAX_TOKENS
    elif model_id.startswith("claude-sonnet-5-5"):
        extra, max_tokens = {"thinking": {"type": "between_tools"}}, CLAUDE_MAX_TOKENS
    else:
        extra, max_tokens = {"thinking": {"type": "disabled"}}, CLAUDE_MAX_TOKENS
    return {"provider": "anthropic", "id": model_id, "temperature": None,
            "max_tokens": max_tokens, "extra": extra}


def _groq_spec(model_id):
    # Both Groq models are GPT-OSS reasoning models: lowest reasoning effort.
    return {"provider": "groq", "id": model_id, "temperature": 0,
            "max_tokens": GROQ_MAX_TOKENS, "extra": {"reasoning_effort": "low"}}


# Order here is the order used in tables and figures.
MODELS = {
    "claude-xs-4": _anthropic_spec(os.environ.get("ANTHROPIC_MODEL_XS_GEN_4")),
    "claude-lg-4": _anthropic_spec(os.environ.get("ANTHROPIC_MODEL_LG_GEN_4")),
    "claude-xs-5": _anthropic_spec(os.environ.get("ANTHROPIC_MODEL_XS_GEN_5")),
    "claude-lg-5": _anthropic_spec(os.environ.get("ANTHROPIC_MODEL_LG_GEN_5")),
    "gpt-oss-xs": _groq_spec(os.environ.get("GROQ_OPEN_AI_MODEL_XS")),
    "gpt-oss-lg": _groq_spec(os.environ.get("GROQ_OPEN_AI_MODEL_LG")),
}

# Concurrent requests per provider. Groq's free tier is tightly rate limited.
CONCURRENCY = {"anthropic": 6, "groq": 2}
MAX_TRIES = 6
# A retry-after longer than this means a daily quota, not a burst limit: stop
# and let the user resume later (the cache keeps everything already done).
MAX_RETRY_AFTER_S = 300
