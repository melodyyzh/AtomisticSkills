#!/usr/bin/env python3
"""
Si band structure / DOS from Materials Project DFT (mp-149).

Uses pre-computed VASP/PBE band data from MP — same Si entry as Phase 1 fetch.
For a *new* DFT run on your structure, see README Phase 3 notes (VASP + atomate2).

Env: base-agent
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_DIR.parents[1]
OUT_DIR = PROJECT_DIR / "results" / "band_structure"
SKILL_SCRIPT = (
    REPO_ROOT
    / ".agents/skills/mat-electronic-structure/scripts/get_mp_electronic_structure.py"
)

DEFAULT_MP_ID = "mp-149"


def _base_python() -> str:
    for root in (
        Path.home() / "miniconda",
        Path.home() / "miniconda3",
        Path.home() / "miniforge3",
    ):
        py = root / "envs" / "base-agent" / "bin" / "python"
        if py.is_file():
            return str(py)
    return sys.executable


def main() -> None:
    parser = argparse.ArgumentParser(description="Si band diagram from MP DFT data")
    parser.add_argument(
        "--material_id",
        default=DEFAULT_MP_ID,
        help=f"Materials Project ID (default: {DEFAULT_MP_ID})",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skip PNG generation",
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUT_DIR / "si_mp_electronic.json"

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{REPO_ROOT}:{env.get('PYTHONPATH', '')}"
    sys.path.insert(0, str(REPO_ROOT))
    from src.utils.config_utils import inject_config_into_env

    inject_config_into_env()

    cmd = [
        _base_python(),
        str(SKILL_SCRIPT),
        "--material_id",
        args.material_id,
        "--output",
        str(out_json),
    ]
    if not args.no_plot:
        cmd.append("--plot")

    print("=== Si band structure (Materials Project DFT) ===")
    subprocess.run(cmd, check=True, cwd=str(REPO_ROOT), env=env)

    print(f"\nOutputs in {OUT_DIR}:")
    for name in ("band_structure.png", "dos.png", "si_mp_electronic.json"):
        p = OUT_DIR / name
        if p.exists():
            print(f"  {p}")


if __name__ == "__main__":
    main()
