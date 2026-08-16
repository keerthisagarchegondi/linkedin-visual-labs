#!/usr/bin/env bash

set -euo pipefail

REPOSITORY_ROOT="$(git rev-parse --show-toplevel)"
cd "${REPOSITORY_ROOT}"

echo "Repository root: ${REPOSITORY_ROOT}"
echo "System Python: $(python --version)"

if [[ ! -x ".venv/bin/python" ]]; then
    echo "Creating project virtual environment..."
    python -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install --editable ".[dev]"

echo
echo "Running environment doctor..."
python -m linkedin_visual_labs doctor

echo
echo "Codespace setup completed successfully."