# Plan: support Supra detail levels DBLPANCAKE / PANCAKE / TAPE in `magnet_setup`

**Status:** follow-up, proposed 2026-10-16, not yet approved.

**Depends on:** [`PLAN_supra_umagnet.md`](PLAN_supra_umagnet.md) — fixes the
`DetailLevel.NONE` path and makes the detailed levels raise
`NotImplementedError`. This plan starts from that state, on top of branch
`fix/supra-umagnet` (or its merge).

## Goal

`magnet_setup()` builds correct magnettools `UnifMagnet` stacks (SI units) for
`Supra` parts with `detail` = `DBLPANCAKE`, `PANCAKE` or `TAPE`, from the HTS
structure file the part references, replacing the `NotImplementedError` left
by `PLAN_supra_umagnet.md`. Verified with the example structure files shipped
by python_magnetgeo.

Out of scope (separate plans, see "Follow-ups"): python_magnetgeo bugs, and
everything magnetdb-duckdb-demo needs to actually use detailed supras.

## Context

### Model

With `detail ≠ NONE`, `Supra.struct` names an HTS structure JSON, read by
`python_magnetgeo.SupraStructure.HTSInsert.fromcfg` as a stack of double
pancakes (`hts/dblpancake.py`); a double pancake is 2 pancakes plus an
isolation; a pancake is `ntapes` turns of tape of radial thickness `w + e`
(superconductor `w`, insulation `e`) and height `h` (`hts/pancake.py`,
`hts/tape.py`). All dimensions in mm.

The existing helper `UMagnets(struct, detail)` (`ana.py`) creates one
`UnifMagnet` per:

| Level | Elements per Supra part | Current density for 1 A |
|---|---|---|
| `DBLPANCAKE` | n_dp | `2·n_p / (W_dp · H_dp)`, `H_dp` = 2·pancake height + inner isolation |
| `PANCAKE` | 2·n_dp | `n_p / (W_p · h_p)` |
| `TAPE` | 2·Σ ntapes (one ring per turn) | `1 / (w · h)` over the superconductor section |

Its geometry (pancake centres at `z_dp ∓ (H_dp/2 − h_p/2)`, tape rings
`r_l … r_l + w`) is correct; the problems are around it.

### Problems in python_magnetsetup (`ana.py`) — fixed by this plan

1. **Dispatch** — the local variable `UMagnets = mt.VectorOfUnifs()` in
   `magnet_setup` shadows the function `UMagnets()`; the helper compares
   `detail` with `"dblepancake"`, `"pancake"`, `"tape"` while the enum values
   are `"DBLPANCAKE"`, `"PANCAKE"`, `"TAPE"` → no branch matches.
2. **Units** — HTS dimensions (mm) are passed unconverted: radii, heights and
   z need ×1e-3; `j` (turns/mm²) needs ×1e6.
3. **Radii** — `DBLPANCAKE` and `PANCAKE` use the insert-wide
   `struct.r0` / `struct.r1` instead of each double pancake's
   `dp.getR0()` / `dp.getR1()`; wrong when double pancakes differ (allowed by
   the "different dblpancakes" format).
4. **Struct file lookup** — `Supra.get_magnet_struct()` opens `struct`
   relative to `Supra._basedir` (`os.getcwd()` when the `Supra` was built),
   not through the geometry search paths used for the magnet YAML.
5. **Axial position** — `HTSInsert.fromcfg` never reads a `z0` (insert always
   centred on 0) and `Supra.check_dimensions()` overwrites `Supra.z` with that
   centred range, so an off-centre Supra loses its position (python_magnetgeo
   bug (a) below).

### Problems in python_magnetgeo — NOT fixed here (upstream)

- (a) `HTSInsert.fromcfg` never sets `z0`; `check_dimensions()` then
  overwrites `Supra.z` (`SupraStructure.py` `fromcfg`, `Supra.py`
  `check_dimensions`).
- (b) "Different dblpancakes" format: `r0` starts at 0 and is updated with
  `min(r0, …)`, so it always stays 0; `check_dimensions()` then sets
  `Supra.r[0] = 0`.
- (c) A top-level `"tape"` entry is parsed and discarded
  (`tape.from_data(...)` without assignment); harmless when each pancake
  defines its tape.

This plan works around (a) and avoids depending on (b) (per-pancake radii);
the bugs themselves stay for an upstream fix.

### Test data

`python_magnetgeo/tests.cfg/HTS.json` (also `LTS.json`, `BSCCO.json`,
currently identical): 2 double pancakes, pancake `r0 = 25`, `ntapes = 2`, tape
`w = 0.07616…`, `e = 0.03`, `h = 6`, isolation layers `h = [0.2125, 0.3, 0.2125]`
(mm). Expected element counts: 2 / 4 / 8; total turns `Supra.n = 8`.

## Files affected (python_magnetsetup)

| File | Action |
|---|---|
| `python_magnetsetup/ana.py` | **edit** — Supras branch of `magnet_setup()` (dispatch, struct lookup, z offset) and helper `UMagnets()` (units, per-pancake radii, enum levels) |
| `tests/test_ana_supra_detail.py` | **create** |
| `tests/data/HTS.json` | **create** — copy of `python_magnetgeo/tests.cfg/HTS.json`, so the tests do not depend on the python_magnetgeo source tree (the .deb build only has the installed package) |
| `debian/changelog` | **edit** — one bullet in the current UNRELEASED entry |

## Design

- **`magnet_setup`, Supras branch:**
  - rename the local `UMagnets` variable (e.g. `umagnets`) in `magnet_setup`
    so the helper is callable; the module-level function name is kept;
  - `DetailLevel.NONE` → unchanged (from `PLAN_supra_umagnet.md`);
  - other levels:
    1. `z_c = (smagnet.z[0] + smagnet.z[1]) / 2` [mm], captured **before**
       loading the struct (python_magnetgeo bug (a) overwrites `Supra.z`);
    2. resolve `smagnet.struct` with `findfile(smagnet.struct, search_paths(MyEnv, "geom"))`;
       `HTSInsert.fromcfg(<resolved path>)`, then `smagnet.check_dimensions(hts)`
       (same as `get_magnet_struct()`, minus the `_basedir` lookup);
    3. `UMagnets(hts, smagnet.detail, z_offset=z_c)` and append every element.
- **`UMagnets(struct, detail, z_offset=0.0)`:**
  - branch on `DetailLevel.DBLPANCAKE` / `PANCAKE` / `TAPE`; any other value →
    `ValueError`;
  - per double pancake `dp`: radii `dp.getR0()`, `dp.getR1()`; all lengths
    ×1e-3; `z = (dp.getZ0() + z_offset)·1e-3`; `j` ×1e6;
  - formulas as in the table above (unchanged physics).
- Docstrings of the modified functions in NumPy style, with units.

## Steps

0. Start from `fix/supra-umagnet` after `PLAN_supra_umagnet.md` is done
   (same branch, or a new `feat/supra-detail-levels` off it — open question 1).
   Baseline: `pytest`.
   → verify: all pass, including the `PLAN_supra_umagnet.md` tests.
1. **Tests first** — `tests/test_ana_supra_detail.py`, using
   `tests/data/HTS.json`:
   - element count per level: `DBLPANCAKE` 2, `PANCAKE` 4, `TAPE` 8;
   - **ampere-turn conservation**: Σ `j · (r_ext − r_int) · height` = 8 at every
     level;
   - units: every element's `get_R_int()` ≈ 0.025 m order of magnitude (not 25);
   - per-pancake radii: a struct written to `tmp_path` in the "different
     dblpancakes" format with two pancake radii → elements carry each
     pancake's own radii;
   - z offset: a `Supra` with `z = [100, 100 + H]` (mm) → element centres
     shifted by `z_c`, not centred on 0;
   - field: at 1 A, `MagneticField` at (0, 0) of each level equals the sum of
     the analytic thick-solenoid centre fields of its elements (1e-6 relative),
     and the `DBLPANCAKE` / `PANCAKE` fields are within a few % of the `NONE`
     model of the same envelope;
   - `magnet_setup` on a `Supras` YAML in `tmp_path` with `struct: HTS.json`
     and each detail level → expected element count (struct found through the
     search paths, not the cwd).

   → verify: the new tests fail against the `PLAN_supra_umagnet.md` state
   (which raises `NotImplementedError`).
2. Implement the `ana.py` changes.
   → verify: `pytest` all passes; `ruff check python_magnetsetup/ana.py`
   reports no new warnings.
3. Changelog bullet: `magnet_setup: support Supra detail levels DBLPANCAKE, PANCAKE, TAPE`.
4. Package build with tests (same procedure as `PLAN_supra_umagnet.md` step 6).
   → verify: `tests/test_ana_supra_detail.py` runs and passes in `dh_auto_test`.

## Assumptions and open questions

1. **Branch** — continue on `fix/supra-umagnet`, or a new
   `feat/supra-detail-levels` off it?
2. **Field tolerance vs `NONE`** — the detailed models include insulation gaps,
   so their field differs from the uniform envelope; "a few %" is a sanity
   bound to fix once the toy numbers are computed, not a physics requirement.
3. **TAPE cost** — one element per turn and pancake; a real insert can reach
   tens of thousands of elements, slowing every field evaluation. No mitigation
   planned here.
4. **Test data duplication** — `tests/data/HTS.json` copies the python_magnetgeo
   example; alternative: depend on a python_magnetgeo test-data path (not
   available in the installed .deb).

## Follow-ups (separate plans)

- **python_magnetgeo** (upstream): fix (a) `HTSInsert` `z0`, (b) `r0` in the
  "different dblpancakes" format, (c) discarded top-level `tape`. Once (a) is
  fixed, drop the `z_c` workaround in `ana.py`.
- **magnetdb-duckdb-demo:**
  - store the HTS struct JSON (in `parts.geometry_data` or a new column) and
    write it next to the YAML in `prepare_geometry_directory`; today only the
    struct file name is stored, and the only supra has `detail: "NONE"`,
    `struct: ""`;
  - hoop stress per part with several elements per part: group elements per
    Supra part (as Bstacks for Bitters; `check_coil_counts` of
    `to_duckdb/PLAN_hoop_stress_part_names.md` fails otherwise), choose the
    representative element (at z0; for `TAPE`, which ring?), and give supras a
    real z0 (hard-coded 0 in `validate_fast_from_pupitre`).
