---
description: MD annealing of Si point-defect supercells after implant damage (equilibrate, high-T hold, quench) using MACE.
---

# Si Doping — Phase 2 Annealing MD

**Scientific problem:** Phase 1 gives **0 K formation energies**; implant processing is **finite-T**. This workflow heats defect-bearing supercells to mimic rapid thermal anneal (RTA) and observes whether native defects (V, Si_i) evolve toward a lower-energy state relative to substitutional dopants.

## Prerequisites

- Completed `projects/si-doping-defects/` Phase 1 (`pristine_relaxation/`, `defect_relaxations/`)
- `mace-agent` conda env

## Run

```bash
cd projects/si-doping-defects
conda run -n mace-agent python run_phase2_md.py --device cpu
```

## Outputs

`results/phase2_annealing_md/<case>/` — per-stage `.traj`, `.extxyz`, `.log`, `MD_ANNEALING_ANALYSIS.md`

## Skills

- `mat-md-monitors` — explosion, quenching
- `ml-foundation-potentials` — MACE-MH-1 matpes_r2scan
- Phase 1: `mat-defect-energy`
