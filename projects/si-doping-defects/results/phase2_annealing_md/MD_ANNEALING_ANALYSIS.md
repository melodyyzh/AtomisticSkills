# Phase 2: Implant-Damage Annealing MD

**Model:** MACE-MH-1 (`matpes_r2scan`)  
**Timestep:** 1.5 fs  
**Protocol:** 300 K equilibration → 1000 K anneal → quench to 300 K

Compare to Phase 1 formation energies in `ANALYSIS.md`.

## Cases

| Case | Role | N (init→final) | E/atom after quench (eV) | Max T (K) |
|------|------|----------------|--------------------------|-----------|
| `pristine` | reference | 54→54 | -8.7138 | 1506 |
| `vac_Si_0` | damage/dopant | 53→53 | -8.6356 | 1359 |
| `int_Si_0` | damage/dopant | 55→55 | -8.6408 | 1310 |
| `sub_P_0` | damage/dopant | 54→54 | -8.7156 | 1366 |

## Interpretation

- **pristine:** baseline; should stay 54 atoms, stable T during anneal.
- **vac_Si_0 / int_Si_0:** implant damage; watch whether `n_atoms` and energy move toward pristine after quench (partial Frenkel healing in a small cell).
- **sub_P_0:** substitutional dopant; compare stability vs native defects during anneal.

Open **`*/stage.extxyz`** or combined stage files in **OVITO** (see `docs/trajectory_output.md`).

## Per-case outputs

- `pristine/` — logs, `.traj`, `.extxyz`, `case_summary.json`
- `vac_Si_0/` — logs, `.traj`, `.extxyz`, `case_summary.json`
- `int_Si_0/` — logs, `.traj`, `.extxyz`, `case_summary.json`
- `sub_P_0/` — logs, `.traj`, `.extxyz`, `case_summary.json`
