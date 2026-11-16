#!/usr/bin/env python3
"""Sample the MMLU question pool into data/questions.json."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fliprate.questions import main  # noqa: E402

if __name__ == "__main__":
    main()
