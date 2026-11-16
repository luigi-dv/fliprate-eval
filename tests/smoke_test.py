"""Offline smoke test: the whole pipeline with a fake model (no API keys, no network).

    python tests/smoke_test.py

Replaces `providers.call` with a deterministic fake, runs the protocol for every
model and system prompt on the first 20 questions, then the analysis (both
views) and the transcript sampler. Everything is written to a temporary
directory; results/ and cache/ are never touched.
"""
import asyncio
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
for _var in ("ANTHROPIC_MODEL_XS_GEN_4", "ANTHROPIC_MODEL_LG_GEN_4",
             "ANTHROPIC_MODEL_XS_GEN_5", "ANTHROPIC_MODEL_LG_GEN_5",
             "GROQ_OPEN_AI_MODEL_XS", "GROQ_OPEN_AI_MODEL_LG"):
    os.environ.setdefault(_var, "dummy-" + _var.lower().replace("_", "-"))

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from fliprate import analysis, prompts, protocol, providers, transcripts
from fliprate.config import MODELS, QUESTIONS_PATH

N_QUESTIONS = 20


def _h(*parts):
    """Deterministic pseudo-random number in [0, 1)."""
    digest = hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
    return int(digest, 16) % 1000 / 1000


def make_fake(questions):
    gold = {prompts.turn0(q): q["answer_letter"] for q in questions}

    async def fake(model_key, messages):
        users = [m["content"] for m in messages if m["role"] == "user"]
        g = gold[users[0]]
        guard = messages[0]["content"] != prompts.SYSTEM
        right = _h(model_key, users[0], "correct") < 0.6
        first = g if right else "ABCD"[("ABCD".index(g) + 1) % 4]
        conf = int(60 + 40 * _h(model_key, users[0], "conf"))
        answer = first
        if len(users) > 1:
            pushed = re.search(r"(?:might be|answer is|definitely) ([A-D])", users[-1])
            p = {2: .15, 3: .3, 4: .5}.get(len(users), 0) * (0.4 if guard else 1) * (1.5 - conf / 100)
            if pushed and _h(model_key, users[0], len(users)) < p:
                answer = pushed.group(1)
            if not pushed and _h(model_key, users[0], "base") < 0.05:
                answer = "ABCD"[("ABCD".index(first) + 2) % 4]
        r = _h(model_key, users[0], len(users), "format")
        if r < 0.03:
            return "I cannot answer that.", False
        if r < 0.08:
            return f"Sure! answer: {answer}, confidence: {conf}", True
        return (f'Let S = {{1, 2}}.\n```json\n{{"reason": "Because {{x}} holds.", '
                f'"confidence": {conf}, "answer": "{answer}"}}\n```'), False

    return fake


def check_parse_reply():
    parse = protocol.parse_reply
    assert parse('{"reason": "r", "confidence": 80, "answer": "B"}') == ("B", 80.0, True)
    assert parse('```json\n{"reason": "r", "confidence": 55, "answer": "c"}\n```') == ("C", 55.0, True)
    assert parse('Working {x}. Final: {"confidence": 70, "answer": "D"}') == ("D", 70.0, True)
    assert parse("My answer: A, confidence: 90") == ("A", 90.0, True)
    assert parse("Answer: B") == ("B", None, False)
    assert parse("I cannot answer that.") == (None, None, False)
    assert parse('{"answer": "Z", "confidence": 150}') == (None, None, False)


def main():
    check_parse_reply()

    questions = json.loads(QUESTIONS_PATH.read_text())[:N_QUESTIONS]
    providers.call = make_fake(questions)

    with tempfile.TemporaryDirectory(prefix="fliprate-smoke-") as tmp:
        tmp = Path(tmp)
        csv = tmp / "results.csv"
        for system in ("default", "guard_neg", "guard_pos"):
            keys = [k for k in MODELS if system == "default" or MODELS[k]["provider"] == "anthropic"]
            rows, errors = asyncio.run(protocol.run_all(keys, questions, system))
            assert not errors, f"{len(errors)} errors, first: {errors[0]!r}"
            assert rows, f"no rows for system={system}"
            protocol.save(rows, csv, keys, system)

        df = pd.read_csv(csv, dtype={"level": str})
        assert list(df.columns) == protocol.COLUMNS, list(df.columns)
        assert set(df["model"]) == set(MODELS), set(df["model"])
        assert set(df["system"]) == {"default", "guard_neg", "guard_pos"}
        assert set(df["condition"]) >= {"capitulation", "correction"}, set(df["condition"])
        turn0 = df[(df["branch"] == "turn0") & df["answer"].notna()]
        assert turn0["correct"].astype(bool).any() and not turn0["correct"].astype(bool).all(), \
            "need both initially-correct and initially-wrong questions"

        outdir = tmp / "out"
        for view in ("all", "common"):
            sys.argv = ["analyze", "--results", str(csv), "--outdir", str(outdir), "--view", view]
            analysis.main()
        manual = tmp / "manual_check.md"
        sys.argv = ["sample_transcripts", "--results", str(csv), "--out", str(manual)]
        transcripts.main()

        expected = ["metrics.csv", "summary.md", "fig1_eds.png", "fig2_conf_resistance.png",
                    "fig3_survival.png", "fig4_guard.png"]
        for name in expected:
            path = outdir / name
            assert path.is_file() and path.stat().st_size > 0, f"missing or empty: {name}"
        assert manual.is_file() and manual.stat().st_size > 0, "missing manual_check.md"

    print(f"OK: smoke test passed ({len(df)} rows, {len(MODELS)} models, 3 system prompts)")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
