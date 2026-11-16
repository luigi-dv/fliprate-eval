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

ROOT = Path(__file__).resolve().parents[2]  # repository root
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

# scripts/build_questions.py writes this many blocks of 100 questions (each with the subject mix
# above). `--n 100` uses the first block; `--n 200` extends it with the second.
N_BLOCKS = 2

# Output limits. They must be generous enough that no reply is cut off before
# its JSON ends. Every model spends hidden reasoning tokens out of the same limit.
CLAUDE_MIN_THINKING_BUDGET = 1024  # smallest budget the API accepts
CLAUDE_MAX_TOKENS = 2000           # thinking budget + room for the JSON answer
GROQ_MAX_TOKENS = 1500


def _anthropic_spec(model_id):
    """Request settings for a Claude model: thinking ON at its lowest setting.

    claude-opus-5-5 cannot run without thinking, so every Claude model thinks,
    each at the lowest setting its API accepts:
      - 5.x models: adaptive thinking at effort "low"
      - 4.5 models: extended thinking with the minimum budget (1024 tokens)
    Thinking tokens count against max_tokens, so the limit leaves room for the
    full budget plus the JSON answer.

    `temperature` is never sent: the API version used by the installed SDK
    (2026-10-21) rejects it for every Claude model, including the 4.5 ones.
    """
    model_id = model_id or ""
    if model_id.startswith(("claude-haiku-4-5", "claude-opus-4-5", "claude-sonnet-4-5")):
        extra = {"thinking": {"type": "enabled", "budget_tokens": CLAUDE_MIN_THINKING_BUDGET}}
    elif model_id.startswith(("claude-opus-5-5", "claude-fable", "claude-mythos")):
        extra = {"output_config": {"effort": "low"}}  # thinking is always on
    else:
        extra = {"thinking": {"type": "adaptive"}, "output_config": {"effort": "low"}}
    return {"provider": "anthropic", "id": model_id, "temperature": None,
            "max_tokens": CLAUDE_MAX_TOKENS, "extra": extra}


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

def thinking_setting(model_key):
    """Short description of how the model reasons before answering in our calls."""
    spec = MODELS[model_key]
    if spec["provider"] == "groq":
        return f"on, reasoning effort {spec['extra']['reasoning_effort']}"
    thinking = spec["extra"].get("thinking", {})
    if thinking.get("type") == "enabled":
        return f"on, extended thinking, budget {thinking['budget_tokens']} tokens (minimum)"
    if thinking.get("type") in ("disabled", "between_tools"):
        return "off"
    effort = spec["extra"].get("output_config", {}).get("effort", "default")
    return f"on, adaptive, effort {effort}"


# Concurrent requests per provider. Groq's free tier is tightly rate limited.
CONCURRENCY = {"anthropic": 6, "groq": 2}
MAX_TRIES = 6
# Rate-limit (429) waits do not use up the tries above: Groq's free tier allows
# only 8,000 tokens per minute per model, so waiting for the window is normal.
MAX_RATE_LIMIT_WAITS = 60
# A retry-after longer than this means a daily quota, not a burst limit: stop
# and let the user resume later (the cache keeps everything already done).
MAX_RETRY_AFTER_S = 300
