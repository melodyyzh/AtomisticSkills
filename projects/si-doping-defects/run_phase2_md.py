#!/usr/bin/env python3
"""
Phase 2: implant-damage annealing MD on Si defect supercells.

Protocol per structure (from Phase 1 relaxed CIFs):
  1. Equilibrate at 300 K (NVT)
  2. Anneal at 1000 K (NVT) — RTA-like hold
  3. Quench 1000 → 300 K (NVT + linear ramp)

Env: mace-agent
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT))

RESULTS = PROJECT_DIR / "results"
PHASE2 = RESULTS / "phase2_annealing_md"
PRISTINE_RELAX = RESULTS / "pristine_relaxation"
DEFECT_RELAX = RESULTS / "defect_relaxations"

MODEL_NAME = "MACE-MH-1"
TASK_NAME = "matpes_r2scan"
DT_FS = 1.5
LOG_INTERVAL = 10

# (stage_name, temperature_K, steps, ensemble, extra monitor)
STAGES = [
    ("01_equilibrate_300K", 300.0, 800, "nvt", ["explosion"]),
    ("02_anneal_1000K", 1000.0, 1500, "nvt", ["explosion"]),
    ("03_quench_1000_to_300K", 1000.0, 1500, "nvt", ["explosion", "quenching"]),
]

CASES = {
    "pristine": PRISTINE_RELAX / "relaxed_structure.cif",
    "vac_Si_0": DEFECT_RELAX / "vac_Si_0" / "relaxed_structure.cif",
    "int_Si_0": DEFECT_RELAX / "int_Si_0" / "relaxed_structure.cif",
    "sub_P_0": DEFECT_RELAX / "sub_P_0" / "relaxed_structure.cif",
}


def _parse_log_stats(log_path: Path) -> dict:
    """Extract last energy/temperature from ASE MD log."""
    if not log_path.exists():
        return {}
    temps, epots = [], []
    with open(log_path) as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            if "Time" in line and "Etot" in line:
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            try:
                epots.append(float(parts[2]))  # Epot column
                if len(parts) >= 5:
                    temps.append(float(parts[4]))  # T[K]
            except ValueError:
                continue
    out = {"n_log_frames": len(epots)}
    if epots:
        out["final_epot_eV"] = epots[-1]
        out["initial_epot_eV"] = epots[0]
    if temps:
        out["final_temperature_K"] = temps[-1]
        out["max_temperature_K"] = max(temps)
    return out


class _MdRunnerParams:
    """Minimal stub for mat-md-monitors (timestep / log interval)."""

    timestep = DT_FS
    loginterval = LOG_INTERVAL


def _run_stage(
    atoms,
    calc,
    out_dir: Path,
    stage_name: str,
    temperature: float,
    steps: int,
    monitor_types: list,
    quench_end: float | None = None,
    init_velocities: bool = True,
) -> None:
    """ASE NVT MD without matgl-dependent md_runner (mace-agent safe)."""
    from ase import units
    from ase.md.nose_hoover_chain import NoseHooverChainNVT
    from ase.md.velocitydistribution import (
        MaxwellBoltzmannDistribution,
        Stationary,
        ZeroRotation,
    )
    from src.utils.mlips.md_utils import MDStopIteration, get_md_callback
    from src.utils.structure_utils import export_trajectory_for_ovito, save_structure

    out_dir.mkdir(parents=True, exist_ok=True)
    traj = out_dir / f"{stage_name}.traj"
    logf = out_dir / f"{stage_name}.log"

    atoms.calc = calc
    if init_velocities:
        MaxwellBoltzmannDistribution(atoms, temperature_K=temperature)
        Stationary(atoms)
        ZeroRotation(atoms)

    dt_fs = DT_FS * units.fs
    taut = 100 * DT_FS * units.fs
    dyn = NoseHooverChainNVT(
        atoms,
        dt_fs,
        tdamp=taut,
        temperature_K=temperature,
        trajectory=str(traj),
        logfile=str(logf),
        loginterval=LOG_INTERVAL,
    )

    runner = _MdRunnerParams()
    for mtype in monitor_types:
        kw = {"temperature": temperature, "output_dir": str(out_dir)}
        if mtype == "quenching" and quench_end is not None:
            kw["temperature_end"] = quench_end
            kw["steps"] = steps
        result = get_md_callback(mtype, atoms, **kw)
        if result is None:
            continue
        if isinstance(result, tuple):
            cb, interval = result
        else:
            cb, interval = result, LOG_INTERVAL
        dyn.attach(cb, interval=interval, dyn=dyn, md_runner=runner)

    try:
        dyn.run(steps)
    except MDStopIteration as e:
        (out_dir / "early_stop.txt").write_text(str(e))

    export_trajectory_for_ovito(traj)
    save_structure(atoms, out_dir / f"{stage_name}_final.cif")


def run_case(case_name: str, cif_path: Path, device: str = "cpu") -> dict:
    from ase.io import read
    from src.utils.mlips.mace.mace_wrapper import MACEWrapper

    if not cif_path.exists():
        raise FileNotFoundError(f"Missing relaxed structure: {cif_path}")

    print(f"\n=== MD case: {case_name} ===")
    case_dir = PHASE2 / case_name
    case_dir.mkdir(parents=True, exist_ok=True)

    atoms = read(str(cif_path))
    n0 = len(atoms)
    wrapper = MACEWrapper(model_name=MODEL_NAME, device=device, head=TASK_NAME)
    wrapper.load()

    def calc_factory():
        c = wrapper.create_calculator()
        return c

    calc = calc_factory()
    stage_stats = []
    for i, (stage_name, temp, steps, _ens, monitors) in enumerate(STAGES):
        print(f"  Stage {stage_name}: {temp} K, {steps} steps")
        quench_end = 300.0 if "quenching" in monitors else None
        _run_stage(
            atoms,
            calc,
            case_dir,
            stage_name,
            temp,
            steps,
            monitors,
            quench_end=quench_end,
            init_velocities=(i == 0),
        )
        log_path = case_dir / f"{stage_name}.log"
        st = _parse_log_stats(log_path)
        st["stage"] = stage_name
        st["target_T_K"] = temp
        stage_stats.append(st)

    # Post-anneal single-point energy (same calculator)
    atoms.calc = calc_factory()
    e_final = float(atoms.get_potential_energy())
    from src.utils.structure_utils import save_structure

    final_cif = case_dir / "final_after_quench.cif"
    save_structure(atoms, final_cif)

    summary = {
        "case": case_name,
        "input_cif": str(cif_path),
        "n_atoms_initial": n0,
        "n_atoms_final": len(atoms),
        "final_energy_eV": e_final,
        "final_energy_per_atom_eV": e_final / len(atoms),
        "stages": stage_stats,
        "output_dir": str(case_dir),
    }
    with open(case_dir / "case_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    return summary


def write_report(summaries: list) -> None:
    lines = [
        "# Phase 2: Implant-Damage Annealing MD",
        "",
        f"**Model:** {MODEL_NAME} (`{TASK_NAME}`)  ",
        f"**Timestep:** {DT_FS} fs  ",
        "**Protocol:** 300 K equilibration → 1000 K anneal → quench to 300 K",
        "",
        "Compare to Phase 1 formation energies in `ANALYSIS.md`.",
        "",
        "## Cases",
        "",
        "| Case | Role | N (init→final) | E/atom after quench (eV) | Max T (K) |",
        "|------|------|----------------|--------------------------|-----------|",
    ]
    for s in summaries:
        max_t = max(
            (st.get("max_temperature_K", 0) for st in s["stages"]),
            default=0,
        )
        lines.append(
            f"| `{s['case']}` | "
            f"{'reference' if s['case'] == 'pristine' else 'damage/dopant'} | "
            f"{s['n_atoms_initial']}→{s['n_atoms_final']} | "
            f"{s['final_energy_per_atom_eV']:.4f} | {max_t:.0f} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- **pristine:** baseline; should stay 54 atoms, stable T during anneal.",
            "- **vac_Si_0 / int_Si_0:** implant damage; watch whether `n_atoms` and "
            "energy move toward pristine after quench (partial Frenkel healing in a small cell).",
            "- **sub_P_0:** substitutional dopant; compare stability vs native defects during anneal.",
            "",
            "Open **`*/stage.extxyz`** or combined stage files in **OVITO** "
            "(see `docs/trajectory_output.md`).",
            "",
            "## Per-case outputs",
            "",
        ]
    )
    for s in summaries:
        lines.append(f"- `{s['case']}/` — logs, `.traj`, `.extxyz`, `case_summary.json`")
    lines.append("")

    report = PHASE2 / "MD_ANNEALING_ANALYSIS.md"
    report.write_text("\n".join(lines))

    combined = {"cases": summaries}
    with open(PHASE2 / "phase2_summary.json", "w") as f:
        json.dump(combined, f, indent=2)
    print(f"\nWrote {report}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case",
        default="all",
        choices=["all", *CASES.keys()],
    )
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    os.chdir(PROJECT_DIR)
    PHASE2.mkdir(parents=True, exist_ok=True)

    names = list(CASES.keys()) if args.case == "all" else [args.case]
    summaries = []
    for name in names:
        summaries.append(run_case(name, CASES[name], device=args.device))
    write_report(summaries)
    print("Phase 2 MD complete.")


if __name__ == "__main__":
    main()
