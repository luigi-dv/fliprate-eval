"""Run the FlipRate protocol and write one CSV row per turn.

    python run.py --pilot                      # 5 questions, 1 model -> results/pilot.csv
    python run.py --models all --n 100         # full run -> results/results.csv
    python run.py --models all --n 100 --system guard   # stretch condition
"""
import argparse
import asyncio
import json
import random
import re
from pathlib import Path

import pandas as pd
from tqdm.asyncio import tqdm

import prompts
import providers
from config import LETTERS, MODELS, QUESTIONS_PATH, RESULTS_DIR, SEED

COLUMNS = [
    "model", "system", "qid", "subject", "gold", "branch", "condition", "level",
    "pushed", "answer", "confidence", "correct", "switched_from_t0", "parse_ok", "raw",
]


def _clean_answer(value):
    value = str(value).strip().upper()
    return value if len(value) == 1 and value in LETTERS else None


def _clean_confidence(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if 0 <= value <= 100 else None


def parse_reply(raw: str):
    """Return (answer, confidence, parse_ok).

    parse_ok is True only when the reply contained valid JSON with a valid
    answer letter. If the regex fallback had to be used, answer/confidence may
    still be filled in but parse_ok is False.
    """
    # First {...} block: try the shortest match, then the longest (in case the
    # reason text itself contains a closing brace).
    for pattern in (r"\{.*?\}", r"\{.*\}"):
        match = re.search(pattern, raw, re.S)
        if not match:
            continue
        try:
            obj = json.loads(match.group(0))
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and _clean_answer(obj.get("answer")):
            return _clean_answer(obj["answer"]), _clean_confidence(obj.get("confidence")), True

    answer = re.search(r'"?answer"?\s*[:=]\s*"?\(?([A-D])\b', raw, re.I)
    confidence = re.search(r'"?confidence"?\s*[:=]\s*"?(\d{1,3})', raw, re.I)
    return (
        answer.group(1).upper() if answer else None,
        _clean_confidence(confidence.group(1)) if confidence else None,
        False,
    )


def pushed_letter(question: dict, turn0_correct: bool) -> str:
    """Correct at turn 0 -> push a random wrong letter; wrong -> push the gold letter."""
    gold = question["answer_letter"]
    if not turn0_correct:
        return gold
    rng = random.Random(f"{SEED}-{question['id']}")  # same letter for every model
    return rng.choice([l for l in LETTERS if l != gold])


async def run_question(model_key: str, question: dict, system_name: str) -> list[dict]:
    gold = question["answer_letter"]
    base = {"model": model_key, "system": system_name, "qid": question["id"],
            "subject": question["subject"], "gold": gold}

    def row(branch, condition, level, pushed, raw, turn0_answer=None):
        answer, confidence, parse_ok = parse_reply(raw)
        switched = None
        if turn0_answer is not None and answer is not None:
            switched = answer != turn0_answer
        return {**base, "branch": branch, "condition": condition, "level": level,
                "pushed": pushed, "answer": answer, "confidence": confidence,
                "correct": None if answer is None else answer == gold,
                "switched_from_t0": switched, "parse_ok": parse_ok, "raw": raw}

    # Turn 0
    history = [
        {"role": "system", "content": prompts.SYSTEMS[system_name]},
        {"role": "user", "content": prompts.turn0(question)},
    ]
    raw0 = await providers.call(model_key, history)
    turn0 = row("turn0", "none", "0", None, raw0)
    if turn0["answer"] is None:
        turn0["condition"] = "parse_fail"
        return [turn0]
    rows = [turn0]
    history.append({"role": "assistant", "content": raw0})

    # Baseline branch: neutral re-ask on top of the turn-0 history.
    raw = await providers.call(
        model_key, history + [{"role": "user", "content": prompts.BASELINE}]
    )
    rows.append(row("baseline", "none", "B", None, raw, turn0["answer"]))

    # Pressure branch: escalate L1 -> L3 in one conversation, stop at first switch.
    condition = "capitulation" if turn0["correct"] else "correction"
    pushed = pushed_letter(question, turn0["correct"])
    for level, template in prompts.LADDER.items():
        history.append({"role": "user", "content": template.format(X=pushed)})
        raw = await providers.call(model_key, history)
        history.append({"role": "assistant", "content": raw})
        turn = row("pressure", condition, str(level), pushed, raw, turn0["answer"])
        rows.append(turn)
        if turn["switched_from_t0"]:
            break
    return rows


async def run_all(model_keys, questions, system_name):
    async def safe(model_key, question):
        try:
            return await run_question(model_key, question, system_name)
        except Exception as error:  # keep going; the cache makes a re-run cheap
            return error

    jobs = [safe(m, q) for m in model_keys for q in questions]
    results = await tqdm.gather(*jobs, desc=f"system={system_name}")
    errors = [r for r in results if isinstance(r, Exception)]
    rows = [turn for r in results if not isinstance(r, Exception) for turn in r]
    return rows, errors


def save(rows, path, model_keys, system_name):
    """Write rows to `path`, replacing earlier rows for the same (model, system)."""
    new = pd.DataFrame(rows, columns=COLUMNS)
    if path.exists():
        old = pd.read_csv(path, dtype={"level": str})
        keep = ~(old["model"].isin(model_keys) & (old["system"] == system_name))
        new = pd.concat([old[keep], new], ignore_index=True)
    path.parent.mkdir(exist_ok=True)
    new.to_csv(path, index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", default="all", help="'all' or comma-separated keys from config.MODELS")
    parser.add_argument("--n", type=int, default=100, help="number of questions")
    parser.add_argument("--system", choices=list(prompts.SYSTEMS), default="default")
    parser.add_argument("--pilot", action="store_true", help="5 questions, 1 model")
    parser.add_argument("--out", default=None, help="output CSV (default results/results.csv)")
    args = parser.parse_args()

    model_keys = list(MODELS) if args.models == "all" else args.models.split(",")
    for key in model_keys:
        if key not in MODELS:
            parser.error(f"unknown model {key!r}; choose from {list(MODELS)}")

    questions = json.loads(QUESTIONS_PATH.read_text())
    n = args.n
    out = RESULTS_DIR / "results.csv"
    if args.pilot:
        model_keys, n, out = model_keys[:1], 5, RESULTS_DIR / "pilot.csv"
    if args.out:
        out = Path(args.out)
    if n < len(questions):
        questions = random.Random(SEED).sample(questions, n)

    rows, errors = asyncio.run(run_all(model_keys, questions, args.system))
    save(rows, out, model_keys, args.system)

    print(f"Wrote {len(rows)} turn rows for {model_keys} (system={args.system}) to {out}")
    if errors:
        print(f"{len(errors)} question(s) failed and are missing from the CSV. "
              f"Re-run the same command to resume. First error: {errors[0]!r}")


if __name__ == "__main__":
    main()
