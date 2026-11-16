#!/usr/bin/env bash
# FlipRate: single entry point. Run `./fliprate.sh help` for the commands.
set -euo pipefail
cd "$(dirname "$0")"

PY=.venv/bin/python

usage() {
  cat <<'EOF'
Usage: ./fliprate.sh <command> [options]

  setup                  Create .venv and install requirements.txt
  questions              Sample the MMLU question pool -> data/questions.json
  pilot [model ...]      5 questions per model (default: every model in turn)
                         -> results/pilot.csv and results/pilot_check.md
  run [options]          Full run -> results/results.csv
                         (default options: --models all --n 100)
  guards                 Stretch condition: guard_neg and guard_pos, Claude models only
  analyze [options]      metrics.csv, summary.md and figures -> results/
  transcripts            20 random transcripts -> results/manual_check.md
  all                    questions (if missing) + run + analyze + transcripts
  models                 List the model keys and IDs read from .env

Options after `run` and `analyze` are passed to scripts/run_eval.py and
scripts/analyze.py (see their --help). Examples:

  ./fliprate.sh pilot claude-xs-5
  ./fliprate.sh run --models claude-xs-5,claude-lg-5 --n 100
  ./fliprate.sh run --n 200
  ./fliprate.sh analyze --view common

Every API reply is cached in cache/, so re-running a command resumes for free.
EOF
}

setup() {
  if [ ! -x "$PY" ]; then
    echo "Creating .venv ..."
    if command -v uv >/dev/null 2>&1; then
      uv venv --python 3.11 .venv
    else
      local python
      python=$(command -v python3.11 || command -v python3) \
        || { echo "Python 3.11+ is required." >&2; exit 1; }
      "$python" -m venv .venv
    fi
  fi
  echo "Installing requirements ..."
  if command -v uv >/dev/null 2>&1; then
    uv pip install -q --python "$PY" -r requirements.txt
  else
    "$PY" -m pip install -q -r requirements.txt
  fi
}

ensure_ready() {
  if [ ! -x "$PY" ] || ! "$PY" -c "import anthropic, groq, dotenv, datasets, statsmodels" 2>/dev/null; then
    setup
  fi
}

ensure_env() {
  if [ ! -f .env ]; then
    echo "No .env file. Run: cp .env.example .env   and fill in the two API keys." >&2
    exit 1
  fi
}

ensure_questions() {
  [ -f data/questions.json ] || "$PY" scripts/build_questions.py
}

command=${1:-help}
[ $# -gt 0 ] && shift

case "$command" in
  help|-h|--help)
    usage ;;
  setup)
    setup ;;
  questions)
    ensure_ready
    "$PY" scripts/build_questions.py ;;
  models)
    ensure_ready
    "$PY" -c "import sys; sys.path.insert(0, 'src')
from fliprate.config import MODELS, thinking_setting
for key, spec in MODELS.items(): print(f'{key:12} {spec[\"id\"] or \"(not set in .env)\":28} thinking {thinking_setting(key)}')" ;;
  pilot)
    ensure_ready; ensure_env; ensure_questions
    if [ $# -eq 0 ]; then
      set -- $("$PY" -c "import sys; sys.path.insert(0, 'src'); from fliprate.config import MODELS; print(' '.join(MODELS))")
    fi
    for model in "$@"; do
      "$PY" scripts/run_eval.py --pilot --models "$model"
    done
    "$PY" scripts/sample_transcripts.py --results results/pilot.csv --out results/pilot_check.md ;;
  run)
    ensure_ready; ensure_env; ensure_questions
    if [ $# -eq 0 ]; then set -- --models all --n 100; fi
    "$PY" scripts/run_eval.py "$@" ;;
  guards)
    ensure_ready; ensure_env; ensure_questions
    "$PY" scripts/run_eval.py --models all --n 100 --system guard_neg "$@"
    "$PY" scripts/run_eval.py --models all --n 100 --system guard_pos "$@" ;;
  analyze)
    ensure_ready
    "$PY" scripts/analyze.py "$@" ;;
  transcripts)
    ensure_ready
    "$PY" scripts/sample_transcripts.py "$@" ;;
  all)
    ensure_ready; ensure_env; ensure_questions
    "$PY" scripts/run_eval.py --models all --n 100
    "$PY" scripts/analyze.py
    "$PY" scripts/sample_transcripts.py ;;
  *)
    echo "Unknown command: $command" >&2
    usage >&2
    exit 1 ;;
esac
