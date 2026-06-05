# Trajectory Output Convention (OVITO & Visualization)

AtomisticSkills uses **ASE** for relaxations and MD. ASE’s default trajectory sink is the native **`.traj`** format. That format is correct for Python/ASE workflows but is **not** a portable visualization format.

This document is the project-wide convention for **all** trajectory-producing code (MCP tools, `src/utils/mlips/`, skill scripts, and new projects).

## Format reference

| Extension | Format | Primary consumers | OVITO (standard) |
|-----------|--------|-------------------|------------------|
| `.traj` | ASE UlmASE-Trajectory (binary) | ASE, `ase.io.read`, analysis scripts | **No** |
| `.extxyz` / `.xyz` | Extended XYZ (text, multi-frame) | OVITO, VMD, ASE, many parsers | **Yes** |
| `.cif` | Single structure | OVITO (static), Matterviz | Yes (one frame) |

**OVITO Pro** can read `.traj` via an ASE plugin; do not rely on that for shared workflows or documentation.

## Required convention

Whenever code **writes an ASE `.traj` file**, it **must also**:

1. Export an **extended XYZ** file with the same basename (e.g. `relax.traj` → `relax.extxyz`).
2. Use `src.utils.structure_utils.export_trajectory_for_ovito()` (do not duplicate conversion logic).
3. Document **both** paths in return values / SKILL outputs:
   - `trajectory_path` — ASE `.traj` (analysis, continuation MD)
   - `trajectory_path_ovito` — `.extxyz` (visualization)

### Implementation (Python)

```python
from src.utils.structure_utils import export_trajectory_for_ovito

traj_path = output_dir / "relax.traj"
# ... run ASE optimizer/MD with trajectory=str(traj_path) ...

extxyz_path = export_trajectory_for_ovito(traj_path)
```

### Already covered (do not reimplement)

- `MLIPModel._single_relax()` — `src/utils/mlips/base.py`
- `MLIPModel._run_md_single()` — same module

New relax/MD code should go through these wrappers or call `export_trajectory_for_ovito` after writing `.traj`.

## Skill & documentation rules

- **SKILL.md**: In output file lists, name `*.extxyz` as the **OVITO / visualization** trajectory and `*.traj` as the **ASE analysis** trajectory.
- **Examples / README**: Prefer linking `[trajectory.extxyz](trajectory.extxyz)` for 3D viewers; mention `.traj` only for ASE post-processing.
- **Do not** tell users to open `.traj` in OVITO without conversion or OVITO Pro + ASE.

## MCP tool return JSON

Relax and MD tools may return:

```json
{
  "trajectory_path": "/path/to/relax.traj",
  "trajectory_path_ovito": "/path/to/relax.extxyz",
  "cif_path": "/path/to/relaxed_structure.cif"
}
```

Agents should suggest **`trajectory_path_ovito`** (or `relaxed_structure.cif` for a single frame) when the user’s visualization tool is OVITO.

## Single-frame trajectories

If an optimization converges in zero or one step, `.traj` may contain only one frame. Extended XYZ is still written; **`relaxed_structure.cif`** is equally valid for static viewing.

## Exceptions

| Case | Convention |
|------|------------|
| Non-ASE trajectories (LAMMPS dump, GROMACS XTC, HDF5 MC) | Use native format; document OVITO import in the skill |
| Deliberately ASE-only internal temp files | No extxyz if file is under `.agents/test` and not user-facing |
| Large production MD | May additionally offer subsampled extxyz in the skill; full `.traj` + extxyz still required for default MCP outputs |

## Related docs

- [visualize_structure.md](visualize_structure.md) — Matterviz / in-editor viewing
- [coding-standards.md](../.agents/rules/coding-standards.md) — agent coding rules
- [skill-standards.md](../.agents/rules/skill-standards.md) — skill authoring
