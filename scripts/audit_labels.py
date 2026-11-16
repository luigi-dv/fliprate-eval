"""Independent audit of results/results.csv.

    python scripts/audit_labels.py [results/results.csv]

Re-parses every raw reply with a separate, simpler parser and checks that:
  1. the recorded answer letter matches the last "answer" field in the reply;
  2. the `correct` flag matches answer == gold;
  3. the pushed option follows the protocol (a wrong option after a right
     first answer, the keyed option after a wrong one);
  4. each pressure conversation stops at the first changed answer, or runs
     all three steps when the answer never changes.
"""
import re
import sys

import pandas as pd

path = sys.argv[1] if len(sys.argv) > 1 else "results/results.csv"
df = pd.read_csv(path, dtype=str, keep_default_na=False)

mismatch = 0
for _, r in df.iterrows():
    letters = re.findall(r'"answer"\s*:\s*"([ABCD])"', r["raw"])
    parsed = letters[-1] if letters else ""
    if parsed != r["answer"]:
        mismatch += 1
        print("ANSWER MISMATCH", r["model"], r["system"], r["qid"], r["branch"], r["level"])

bad_flag = int(((df["answer"] != "") & ((df["answer"] == df["gold"]).map(str) != df["correct"])).sum())

protocol = 0
turn0 = df[df["branch"] == "turn0"].set_index(["model", "system", "qid"])
groups = df[df["branch"] == "pressure"].groupby(["model", "system", "qid"])
for key, g in groups:
    first = turn0.loc[key]
    condition, pushed = g["condition"].iloc[0], g["pushed"].iloc[0]
    if first["correct"] == "True":
        ok = condition == "capitulation" and pushed != first["gold"]
    else:
        ok = condition == "correction" and pushed == first["gold"]
    switched = list(g.sort_values("level")["switched_from_t0"])
    if "True" in switched:
        ok = ok and switched.index("True") == len(switched) - 1
    else:
        ok = ok and len(switched) == 3
    protocol += 0 if ok else 1

print(f"rows: {len(df)}")
print(f"answer mismatches: {mismatch}")
print(f"correct-flag inconsistencies: {bad_flag}")
print(f"pressure conversations: {groups.ngroups}, protocol errors: {protocol}")
print(f"parse_ok false: {int((df['parse_ok'] != 'True').sum())}, truncated: {int((df['truncated'] == 'True').sum())}")
