"""Sample the MMLU questions used by the harness -> data/questions.json.

The file is an ordered list. It is built in blocks of 100 questions; every
block has the subject mix in config.SUBJECT_COUNTS and is shuffled with a fixed
seed. The runner always takes the first `--n` questions, so `--n 200` is the
`--n 100` set plus 100 new questions, and an interrupted run has covered a
random mix of subjects rather than whole subjects in turn.
"""
import json
import random

from datasets import load_dataset

from .config import DATA_DIR, LETTERS, N_BLOCKS, QUESTIONS_PATH, SEED, SUBJECT_COUNTS


def main():
    df = load_dataset("cais/mmlu", "all", split="test").to_pandas()
    random.seed(SEED)
    by_subject = {s: df[df["subject"] == s].reset_index(drop=True) for s in SUBJECT_COUNTS}
    unused = {s: list(range(len(rows))) for s, rows in by_subject.items()}

    questions = []
    for block in range(N_BLOCKS):
        block_questions = []
        for subject, n in SUBJECT_COUNTS.items():
            if len(unused[subject]) < n:
                raise ValueError(f"{subject}: not enough questions for block {block + 1}")
            # Sample positions among the still-unused questions of this subject.
            picked = sorted(random.sample(range(len(unused[subject])), n))
            indices = [unused[subject][p] for p in picked]
            unused[subject] = [i for i in unused[subject] if i not in indices]
            for i in indices:
                row = by_subject[subject].iloc[i]
                choices = [str(c) for c in row["choices"]]
                assert len(choices) == 4, (subject, i)
                block_questions.append(
                    {
                        "id": f"{subject}-{i:04d}",
                        "subject": subject,
                        "question": row["question"].strip(),
                        "choices": choices,
                        "answer_letter": LETTERS[int(row["answer"])],
                    }
                )
        random.Random(f"{SEED}-order-{block}").shuffle(block_questions)
        questions += block_questions

    assert len({q["id"] for q in questions}) == len(questions)
    DATA_DIR.mkdir(exist_ok=True)
    QUESTIONS_PATH.write_text(json.dumps(questions, indent=2, ensure_ascii=False))
    print(f"Wrote {len(questions)} questions to {QUESTIONS_PATH}")
    counts = {l: sum(q["answer_letter"] == l for q in questions[:100]) for l in LETTERS}
    print("Gold letter counts, first 100:", counts)


if __name__ == "__main__":
    main()
