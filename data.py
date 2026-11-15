"""Sample the MMLU questions used by the harness -> data/questions.json."""
import json
import random

from datasets import load_dataset

from config import DATA_DIR, LETTERS, QUESTIONS_PATH, SEED, SUBJECT_COUNTS


def main():
    df = load_dataset("cais/mmlu", "all", split="test").to_pandas()
    random.seed(SEED)

    questions = []
    for subject, n in SUBJECT_COUNTS.items():
        rows = df[df["subject"] == subject].reset_index(drop=True)
        if len(rows) < n:
            raise ValueError(f"{subject}: only {len(rows)} questions")
        for i in sorted(random.sample(range(len(rows)), n)):
            row = rows.iloc[i]
            choices = [str(c) for c in row["choices"]]
            assert len(choices) == 4, (subject, i)
            questions.append(
                {
                    "id": f"{subject}-{i:04d}",
                    "subject": subject,
                    "question": row["question"].strip(),
                    "choices": choices,
                    "answer_letter": LETTERS[int(row["answer"])],
                }
            )

    DATA_DIR.mkdir(exist_ok=True)
    QUESTIONS_PATH.write_text(json.dumps(questions, indent=2, ensure_ascii=False))
    print(f"Wrote {len(questions)} questions to {QUESTIONS_PATH}")
    counts = {l: sum(q["answer_letter"] == l for q in questions) for l in LETTERS}
    print("Gold letter counts:", counts)


if __name__ == "__main__":
    main()
