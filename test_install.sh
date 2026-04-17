#!/bin/bash
command -v uv >/dev/null 2>&1 || { curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1; }
export PATH="$HOME/.local/bin:$PATH"
test -d "$HOME/.venv" || uv venv --system-site-packages --seed "$HOME/.venv"
. "$HOME/.venv/bin/activate"
export PYTHONUNBUFFERED=1
uv pip install -r requirements_v2.txt
