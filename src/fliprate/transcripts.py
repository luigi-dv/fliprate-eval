"""Write 20 random pressure-branch transcripts to results/manual_check.md
so the automatic `switched` labels can be validated by hand."""
import argparse
import json
import random
from pathlib import Path

import pandas as pd

from . import prompts
from .config import LETTERS, QUESTIONS_PATH, RESULTS_DIR, SEED

N_SAMPLES = 20


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default=str(RESULTS_DIR / "results.csv"))
    parser.add_argument("--out", default=str(RESULTS_DIR / "manual_check.md"))
    args = parser.parse_args()

    questions = {q["id"]: q for q in json.loads(QUESTIONS_PATH.read_text())}
    turns = pd.read_csv(args.results, dtype={"level": str})
    with_pressure = turns[turns["branch"] == "pressure"]
    keys = sorted(set(zip(with_pressure["model"], with_pressure["system"], with_pressure["qid"])))
    sample = random.Random(SEED).sample(keys, min(N_SAMPLES, len(keys)))

    out = ["# Manual check of auto-labelled pressure transcripts", "",
           f"{len(sample)} random pressure-branch conversations (seed {SEED}). "
           "Tick the box if the auto label matches what the model actually did.", ""]
    for i, (model, system, qid) in enumerate(sample, 1):
        g = turns[(turns["model"] == model) & (turns["system"] == system) & (turns["qid"] == qid)]
        t0 = g[g["branch"] == "turn0"].iloc[0]
        pressure = g[g["branch"] == "pressure"].sort_values("level")
        q = questions[qid]
        switched = pressure["switched_from_t0"].astype(str).str.lower().eq("true").any()
        last = pressure.iloc[-1]

        out += [f"## {i}. {model} / {system} / {qid}", "",
                f"- Condition: **{last['condition']}**; gold **{t0['gold']}**; pushed **{last['pushed']}**",
                f"- Auto label: turn-0 answer **{t0['answer']}** (confidence {t0['confidence']:.0f}), "
                + (f"**switched to {last['answer']} at L{last['level']}**" if switched
                   else "**held through L3**" if last["level"] == "3"
                   else f"**held, ladder ended at L{last['level']}**"),
                "- [ ] auto label correct?", "",
                "**Question**", "", "> " + q["question"].replace("\n", "\n> "), ""]
        out += [f"> {l}. {c}" for l, c in zip(LETTERS, q["choices"])]
        out += ["", "**Turn 0 reply**", "", "````", str(t0["raw"]), "````", ""]
        for _, turn in pressure.iterrows():
            user = prompts.LADDER[int(turn["level"])].format(X=turn["pushed"])
            out += [f"**L{turn['level']} user:** {user}", "",
                    f"**L{turn['level']} reply** (parsed answer: {turn['answer']}, "
                    f"switched: {turn['switched_from_t0']}, truncated: {turn['truncated']})", "",
                    "````", str(turn["raw"]), "````", ""]
        out += ["---", ""]

    Path(args.out).write_text("\n".join(out))
    print(f"Wrote {len(sample)} transcripts to {args.out}")


if __name__ == "__main__":
    main()
