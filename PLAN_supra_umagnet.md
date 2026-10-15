# Plan: fix the Supra branch of `magnet_setup`

**Status:** proposed 2026-10-15, not yet approved.

## Goal

`magnet_setup()` (`python_magnetsetup/ana.py`) builds a correct magnettools
`UnifMagnet` (SI units) for a `Supras` magnet whose `Supra` parts have
`detail=DetailLevel.NONE`, so assemblies with a superconducting magnet (in
magnetdb-duckdb-demo: `M8_A211225_00` and `M8_A230919_00`, magnet `Hybrid` /
part `HybridSupra`) can be loaded. Detail levels that need an HTS structure
file fail with an explicit error instead of an unrelated `TypeError`.

## Context: why the Supra branch fails today

Code (`ana.py`, `magnet_setup`, Supras branch):

```python
UMagnets = mt.VectorOfUnifs()            # local variable, hides the module function UMagnets()
...
elif isinstance(cad, Supras):
    for smagnet in cad.magnets:
        if smagnet.detail is None:          # (1)
            tmp = UMagnet(smagnet, debug)   # (2)
            UMagnets.append(tmp)
        else:
            sstruct = smagnet.get_magnet_struct()               # (3)
            tmp = UMagnets(sstruct, smagnet.detail, debug)      # (4)
        for item in tmp:                    # (5) runs for both branches
            UMagnets.append(item)
```

| # | Problem | Evidence |
|---|---|---|
| 1 | python_magnetgeo now stores `Supra.detail` as a `DetailLevel` enum defaulting to `DetailLevel.NONE` (`"NONE"`), never Python `None`, so the `else` branch always runs. | `python_magnetgeo/Supra.py` (`__init__`, `from_dict`); `python_magnetgeo/enums.py`: `NONE`, `DBLPANCAKE`, `PANCAKE`, `TAPE` |
| 3 | The `else` branch loads the HTS structure file `self.struct`; plain Supra parts have `struct=""`. | `Supra.get_magnet_struct()` |
| 4 | `UMagnets(...)` calls the local `VectorOfUnifs`, not the helper function. | reproduced: `TypeError: 'VectorOfUnifs' object is not callable` |
| — | The helper `UMagnets()` compares `detail` with `"dblepancake"`, `"pancake"`, `"tape"`, while the enum values are `"DBLPANCAKE"`, …; no branch matches, so it would return zero UMagnets. It also passes HTS radii without the ×1e-3 mm→m conversion. | `ana.py` `UMagnets()` vs `enums.py` |
| 2 | `UMagnet(Supra)` reads attributes a plain `Supra` does not have (`dblepancakes`, `getFillingFactor()` — commented out in `Supra.py`, `r0`, `r1`, `h`, `z0`) → `AttributeError`. | `ana.py` `UMagnet()`; `Supra.py` |
| — | `UMagnet()` also has unit errors: `j = n / getArea() * 1e-6` (per mm² should be ×1e6) and `z_offset = struct.z0` unscaled while radii are ×1e-3. | `ana.py` `UMagnet()` |
| 5 | After the NONE branch, `for item in tmp` iterates over a single `UnifMagnet`. | reproduced: `TypeError: 'UnifMagnet' object is not iterable` |

`UnifMagnet` signature (magnettools):
`UnifMagnet(external_radius, internal_radius, height, currentdensity, z_offset=0.0, lambda=1.0, rho=0.0)`
— the same as `BitterMagnet`. `BMagnet()` passes everything in SI: radii and
`z_offset` in m, **full** height, `j` in A/m² for 1 A.

Reference data (the only Supra part in magnetdb, dimensions in mm):
`{"__classname__": "Supra", "name": "Hybrid", "r": [550, 913], "z": [-700, 700], "n": 1924, "struct": "", "detail": "NONE"}`

## Files affected

| File | Action |
|---|---|
| `python_magnetsetup/ana.py` | **edit** `UMagnet()` and the Supras branch of `magnet_setup()` |
| `tests/test_ana_supra.py` | **create** |
| `debian/changelog` | **edit** — add one bullet to the existing `0.1.1-1 UNRELEASED` entry (see open question 2) |

Nothing changes in magnetdb-duckdb-demo itself; its submodule pointer moves
only when that repo commits it (out of scope).

## Design

- **`UMagnet(struct)`** rewritten for a plain `Supra` (dimensions in mm):
  - `r_int, r_ext = r[0]·1e-3, r[1]·1e-3`  [m]
  - `height = (z[1] − z[0])·1e-3`  [m]
  - `z_offset = (z[0] + z[1]) / 2 · 1e-3`  [m]
  - `j = n / ((r_ext − r_int) · height)`  [A/m² for 1 A]
  - `lambda = 1`, `rho = 0` (superconductor)
- **Supras branch of `magnet_setup`:**
  - `detail == DetailLevel.NONE` → append **one** `UMagnet(smagnet)` (no `is None`
    test, no iteration over a single magnet);
  - any other level → `NotImplementedError(f"Supra '{name}': detail={detail} needs an HTS struct; not supported by magnet_setup")`.
  - The detailed `UMagnets()` helper becomes unreachable from `magnet_setup`;
    it is reported as dead code, not deleted. The shadowed local `UMagnets`
    name can no longer cause a call error and is left as is.
- Docstrings of the two modified functions rewritten in NumPy style with units
  (`sphinx.ext.napoleon` is already enabled in `docs/conf.py`).

## Steps

0. Create a branch: `git switch -c fix/supra-umagnet` (from `eb617d3`, tip of
   `origin/msite_to_assembly`). Baseline: `pytest`.
   → verify: the branch exists; existing tests pass.
1. **Tests first** — create `tests/test_ana_supra.py`:
   - `UMagnet(Supra(name="S", r=[550, 913], z=[-700, 700], n=1924))`:
     `get_R_int() == 0.550`, `get_R_ext() == 0.913`, `get_HalfHeight() == 0.7`,
     `get_Z_offset() == 0.0`, `get_CurrentDensity()` at 1 A `== 1924 / (0.363 · 1.4)`;
   - analytic check: at 1 A, `MagneticField` at (0, 0) equals the thick-solenoid
     centre field
     `B0 = μ0 · j · a1 · β · ln[(α + √(α² + β²)) / (1 + √(1 + β²))]`,
     `α = a2/a1`, `β = (h/2)/a1`, within 1e-6 relative;
   - off-centre Supra (`z = [0, 1400]`) → `z_offset == 0.7`;
   - `magnet_setup` on a `Supras` YAML written to `tmp_path` (with an `appenv`
     pointing there) returns exactly 1 UMagnet; with `detail=DBLPANCAKE` it
     raises `NotImplementedError`.

   → verify: the new tests fail against the current code.
2. Implement the `ana.py` changes.
   → verify: `pytest` all passes; `ruff check python_magnetsetup/ana.py`
   reports no new warnings compared with the baseline.
3. **Integration check from magnetdb-duckdb-demo** — on a scratch copy of
   `to_duckdb/magnetdb-2026-10-08.duckdb`, run `load_assembly_config_from_duckdb`
   → `prepare_geometry_directory` → `load_magnettools` (`to_duckdb/stress_map.py`)
   for `M8_A230919_00` (Insert + Bitters + Hybrid).
   → verify: loading succeeds; 1 UMagnet; centre field at `IS = 1 A` equals the
   analytic value; total field at nominal currents reported for plausibility.
4. **Data check (read-only)** — load one pupitre file of each M8 assembly with
   `prepareData` and check whether an `IS` column exists and is non-zero.
   → verify: report the result. Without `IS`, the hybrid's field contribution
   to hoop stress is zero regardless of this fix.
5. Add the `debian/changelog` bullet, if confirmed (open question 2).

## Assumptions and open questions

1. **Scope of detail levels** — recommended: fix `NONE` only and raise for
   `DBLPANCAKE` / `PANCAKE` / `TAPE`. No HTS struct file exists in the data, so
   a fix of the detailed path could not be verified; that helper also has its
   own unit issues (no ×1e-3) and mismatched enum strings. Extend the scope?
2. **Packaging** — add a bullet to the UNRELEASED `0.1.1-1` changelog entry, or
   leave packaging alone?
3. **Branch** — `fix/supra-umagnet` off `msite_to_assembly`, or commit directly
   on `msite_to_assembly`? Nothing is committed or pushed without explicit
   instruction.
4. **Uniform current density** — uniform `j` over the rectangular winding
   section, filling factor 1 for the field: standard for a `UnifMagnet` and
   consistent with the analytic check.

## Related

- magnetdb-duckdb-demo: part-name refactor of the hoop-stress pipeline
  (`to_duckdb/compute_hoop_stats.py`, `to_duckdb/stress_map.py`). Its count
  check over all assemblies covers the M8 assemblies once this fix lands, so
  this plan is best executed first.
