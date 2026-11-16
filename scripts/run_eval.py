#!/usr/bin/env python3
"""Run the FlipRate protocol (see --help). Logic lives in src/fliprate/protocol.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fliprate.protocol import main  # noqa: E402

if __name__ == "__main__":
    main()
