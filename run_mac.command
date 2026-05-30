#!/bin/zsh
cd "$(dirname "$0")"
echo "Starting DubDeck AI..."
if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD=python3
else
  PYTHON_CMD=python
fi
if [ ! -d ".venv" ]; then
  $PYTHON_CMD -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
export TORCH_HOME="$PWD/temp/cache/torch"
export XDG_CACHE_HOME="$PWD/temp/cache"
export PYTHONPYCACHEPREFIX="$PWD/temp/cache/pycache"
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false .venv/bin/python -m streamlit run app.py
echo "DubDeck AI closed. Press Enter to exit."
read
