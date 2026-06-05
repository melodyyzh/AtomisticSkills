# Si Point-Defect Analysis (MLIP)

**Model:** MACE-MH-1 (`matpes_r2scan`)  
**Supercell:** 3×3×3  
**Chemical potentials:** elemental reservoir (`MACE-MH-1_matpes_r2scan_energies.json`)

## Formation energies (neutral)

| Rank | Defect | E_f (eV) | Δn (species change) |
|------|--------|----------|---------------------|
| 1 | `sub_P_0` | 0.083 | Si:1, P:-1 |
| 2 | `sub_B_0` | 0.662 | Si:1, B:-1 |
| 3 | `vac_Si_0` | 3.681 | Si:1 |
| 4 | `int_Si_0` | 4.491 | Si:-1 |

## Interpretation

**Lowest formation energy:** `sub_P_0` (0.083 eV) under the elemental chemical-potential reference used here.

### Doping (substitutional)
- **P@Si** — n-type donor (extra electron in band-gap engineering picture).
- **B@Si** — p-type acceptor.

Compare their E_f to decide which substitutional dopant is more favorable to incorporate at neutral charge state in this MLIP model.

### Implant damage (native defects)
- **Si vacancy (V_Si)** — common displacement damage product.
- **Si self-interstitial (Si_i)** — Frenkel partner to vacancies.

After implantation, the crystal often contains both V and Si_i. If E_f(V) + E_f(Si_i) is large compared to pristine Si, annealing provides thermodynamic driving force for **Frenkel recombination** (V + Si_i → bulk Si), reducing defect density.

Substitutional dopants that remain after anneal are those with **low E_f** relative to competing native defects, and sufficient kinetic access during RTA.

### Caveats
- Neutral defects only; real dopants are charged (use DFT for transition levels).
- MLIP E_f are **trends**, not experimental formation enthalpies.
- No implant cascade — this is equilibrium defect thermodynamics on a fixed supercell.

## Raw data

See `results/defect_energies.json`.
