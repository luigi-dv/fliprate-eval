#!/usr/bin/env python3
"""Compute metrics, figures and summary.md (see --help). Logic lives in src/fliprate/analysis.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fliprate.analysis import main  # noqa: E402

if __name__ == "__main__":
    main()
