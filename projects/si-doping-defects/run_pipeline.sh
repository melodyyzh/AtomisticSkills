#!/bin/bash
# Run the full Si doping / point-defect test project.
set -e
cd "$(dirname "$0")"
REPO_ROOT="$(cd ../.. && pwd)"
export PYTHONPATH="${REPO_ROOT}:${PYTHONPATH:-}"

MACE_PY="${MACE_PY:-$(conda info --base 2>/dev/null)/envs/mace-agent/bin/python}"
if [[ ! -x "$MACE_PY" ]]; then
  echo "mace-agent not found."
  if [[ "$(uname -s)" == "Darwin" ]]; then
    echo "Install from repo root: bash conda-envs/mace-agent/install_macos.sh"
  else
    echo "Install from repo root: bash conda-envs/mace-agent/install.sh"
  fi
  echo "Also required: bash conda-envs/base-agent/install.sh"
  exit 1
fi

echo "Using: $MACE_PY"
"$MACE_PY" run_pipeline.py --step all --device cpu
