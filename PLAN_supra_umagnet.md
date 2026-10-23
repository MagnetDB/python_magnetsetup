# Plan: fix the Supra branch of `magnet_setup`

**Status:** proposed 2026-10-15, not yet approved.

## Goal

`magnet_setup()` (`python_magnetsetup/ana.py`) builds a correct magnettools
`UnifMagnet` (SI units) for a `Supras` magnet whose `Supra` parts have
`detail=DetailLevel.NONE`, so assemblies with a superconducting magnet (in
magnetdb-duckdb-demo: `M8_A211225_00` and `M8_A230919_00`, magnet `Hybrid` /
part `HybridSupra`) can be loaded. Detail levels that need an HTS structure
file fail with an explicit error instead of an unrelated `TypeError`. The
Debian package declares the runtime dependencies it needs to import,
`pyproject.toml` declares the python_magnetgeo range `__init__.py` enforces,
and **the test suite runs (and must pass) when the .deb is built**.

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

## Context: version and dependency consistency (checked 2026-10-16)

Versions are consistent: `pyproject.toml` `0.1.1`, `debian/changelog` top entry
`0.1.1-1` (UNRELEASED, "rebuild for trixie"), installed metadata `0.1.1`
(`__version__` and Sphinx `release` read it). Latest git tag is `v0.1.0`; no
`v0.1.1` tag exists, so 0.1.1 is unreleased and the fix can go into the
existing `0.1.1-1` entry without a version bump.

Dependency declarations are not consistent:

| Dependency | `pyproject.toml` | `debian/control` Depends | Code |
|---|---|---|---|
| python_magnetgeo | `python-magnetgeo`, no bound | **missing** | 27 imports; `__init__.py` raises at import unless `>=1.0.0,<2.0.0` |
| pint | `>=0.24,<0.25` | **missing** | `units.py` |
| PyYAML | `>=6.0,<7.0` | **missing** (Build-Depends only) | 6 imports |

A `python3-magnetsetup` .deb installed on a clean machine therefore fails at
`import python_magnetsetup`. Available in the configured apt sources:
`python3-magnetgeo` 1.0.1-8, `python3-pint` 0.24.4-2, `python3-yaml` 6.0.2-1+b2.

## Context: tests during the .deb build (checked 2026-10-16)

- `debian/rules` disables the test step:
  `override_dh_auto_test: echo "disable pytest (issue with trusted-host)"`.
- debhelper's pybuild build system passes `--test-pytest` only when
  **`python3-pytest`** is in Build-Depends
  (`/usr/share/perl5/Debian/Debhelper/Buildsystem/pybuild.pm`); otherwise pybuild
  falls back to `unittest discover`. Build-Depends currently lists only
  `python3-pytest-runner`.
- pybuild copies `pyproject.toml` and `tests/` into the build directory and runs
  `python3 -m pytest` there (`testpaths = ["tests"]` applies); the pyproject
  plugin sets `HOME` to a temporary directory. File logging only starts when
  `MAGNETSETUP_LOG_FILE` is set, so a read-only `HOME` is not a problem.
- Importing any `python_magnetsetup.*` module runs `__init__.py`, which calls
  `check_magnetgeo_compatibility()` → python_magnetgeo is needed by **every**
  test, including `test_logging.py`.

Packages the tests need at build time:

| Package | Needed by | Build-Depends today |
|---|---|---|
| `python3-pytest` | test runner (enables `--test-pytest`) | no (`python3-pytest-runner` only) |
| `python3-magnetgeo (>= 1.0.0)`, `(<< 2.0.0)` | `__init__.py` version check (every test); `Supra` / `Supras` in the new tests | no |
| `python3-yaml` | `ana.py`, `objects.py` | yes |
| `python3-decouple` | `config.py` (imported by `ana.py`) | no |
| `python3-magnettools` | `ana.py` (new Supra tests) | no |
| `python3-packaging` | `__init__.py` range check (optional: skipped without it) | no |

Not needed by the tests: pint, pandas, chevron, requests, fabric, gmsh, lxml,
paraview (none is imported by `ana.py`, `config.py`, `objects.py`,
`file_utils.py`, `logging_config.py` or the tests).

The "trusted-host" issue most likely came from `python3-pytest-runner`
(`setup.py test` trying pip during an offline build); the package now builds
with `pybuild-plugin-pyproject` and no longer uses pytest-runner. Not verified.

`python3-magnetgeo` and `python3-magnettools` are not in Debian: the build
chroot (local or CI) must have the LNCMI apt depot configured.

## Files affected

| File | Action |
|---|---|
| `python_magnetsetup/ana.py` | **edit** `UMagnet()` and the Supras branch of `magnet_setup()` |
| `tests/test_ana_supra.py` | **create** |
| `pyproject.toml` | **edit** — `python-magnetgeo` → `python-magnetgeo>=1.0.0,<2.0.0` |
| `debian/control` | **edit** — `python3-magnetsetup` Depends: add `python3-magnetgeo (>= 1.0.0)`, `python3-magnetgeo (<< 2.0.0)`, `python3-pint`, `python3-yaml`. Build-Depends: replace `python3-pytest-runner` with `python3-pytest`; add `python3-magnetgeo (>= 1.0.0)`, `python3-magnetgeo (<< 2.0.0)`, `python3-decouple`, `python3-magnettools`, `python3-packaging` |
| `debian/rules` | **edit** — delete the `override_dh_auto_test` target |
| `debian/watch` | **edit** — `https://github.com/trophime/python_magnetsetup/tags` → `https://github.com/MagnetDB/python_magnetsetup/tags` (matches `Homepage` in `debian/control`) |
| `debian/changelog` | **edit** — add bullets to the existing `0.1.1-1 UNRELEASED` entry (no version bump) |

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
- **Packaging (minimal):** declare only what is needed for the package to
  import — the python_magnetgeo range already enforced by `__init__.py`
  (`MIN_MAGNETGEO_VERSION` / `MAX_MAGNETGEO_VERSION`), pint and PyYAML. Version
  stays `0.1.1`; `debian/changelog` `0.1.1-1` gets four bullets:
  - `magnet_setup: fix Supra (detail=NONE) UnifMagnet; raise for HTS detail levels`
  - `d/control: add missing python3-magnetgeo, python3-pint, python3-yaml Depends`
  - `d/rules, d/control: run the test suite at build time (python3-pytest and test Build-Depends)`
  - `d/watch: track the MagnetDB GitHub organisation`
- **`debian/watch`:** only the URL changes (`trophime` → `MagnetDB`); the
  `filenamemangle` option and the tag regex `(?:.*?/)?v?(\d[\d.]*)\.tar\.gz`
  stay, they already match `…/archive/refs/tags/v0.1.0.tar.gz`. Tags on
  `MagnetDB/python_magnetsetup` today: `v0.0.1`, `v0.1.0`.
- **Tests at build time:** remove the `override_dh_auto_test` target so
  `dh_auto_test` runs; `python3-pytest` in Build-Depends makes pybuild use
  pytest; Build-Depends gain the packages listed in "Context: tests during the
  .deb build". No `PYBUILD_TEST_ARGS` needed (`testpaths` in `pyproject.toml`).
  A failing test fails the build.

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
5. **Packaging** — edit `pyproject.toml`, `debian/control`, `debian/rules`,
   `debian/watch` and `debian/changelog` as above.
   → verify:
   - `python3 -c "from debian.deb822 import Deb822; ..."` parses
     `debian/control`; the `python3-magnetsetup` Depends list contains the 4 new
     entries and Build-Depends contains the 6 test entries, without
     `python3-pytest-runner`;
   - `debian/rules` no longer contains `override_dh_auto_test`;
   - `uscan --no-download --report --verbose` (read-only network query) reads
     `https://github.com/MagnetDB/python_magnetsetup/tags` and finds upstream
     `0.1.0` (the newest tag; the local `0.1.1` is not tagged yet);
   - `dpkg-parsechangelog -S Version` → `0.1.1-1`; matches `pyproject.toml`
     `version = "0.1.1"`;
   - `pip install -e .` in the `.venv` (or `pip check`) reports no conflict with
     the installed `python-magnetgeo` 1.0.1;
   - each new Depends resolves: `apt-cache policy python3-magnetgeo python3-pint python3-yaml`
     shows a candidate.
6. **Build the .deb with tests** (see open question 5 for where).
   → verify:
   - the build log of `dh_auto_test` shows `python3 -m pytest` running in the
     pybuild build directory, collecting `tests/test_logging.py` and
     `tests/test_ana_supra.py`, all passing;
   - the build succeeds and `dpkg -I python3-magnetsetup_0.1.1-1_all.deb` shows
     the new Depends;
   - negative check: temporarily break one assertion in `tests/test_ana_supra.py`
     → the build fails at `dh_auto_test` (then revert).

## Assumptions and open questions

1. **Scope of detail levels** — *decided 2026-10-16:* fix `NONE` only and
   raise `NotImplementedError` for `DBLPANCAKE` / `PANCAKE` / `TAPE`. Support
   for the detailed levels is a follow-up:
   [`PLAN_supra_detail_levels.md`](PLAN_supra_detail_levels.md).
2. **Packaging** — *decided 2026-10-16:* keep `0.1.1`, add bullets to the
   UNRELEASED `0.1.1-1` entry, and include the minimal dependency correction
   above. Left out (separate packaging work if wanted): `fabric` and
   `requests` declared but never imported; `gmsh` / `lxml` in Build-Depends but
   never imported; `pandas` (lazy imports in `jsonmodel.py`, `flatten.py`) and
   `packaging` (optional, in `__init__.py`) undeclared; `debian/copyright`
   `Source:` still points to `github.com/Trophime/python_magnetsetup`.
   *Added 2026-10-16:* running the tests at build time and switching
   `debian/watch` to the MagnetDB organisation are **in scope** (see Design).
3. **Branch** — *decided 2026-10-16:* `fix/supra-umagnet` off
   `msite_to_assembly` (`eb617d3`). Nothing is committed or pushed without
   explicit instruction.
4. **Uniform current density** — *decided 2026-10-16:* uniform `j` over the
   rectangular winding section, filling factor 1 for the field (`lambda = 1`,
   `rho = 0`): standard for a `UnifMagnet` and consistent with the analytic
   check.
5. **Where to build the .deb (step 6)** — locally, missing build dependencies
   are `pybuild-plugin-pyproject`, `python3-decouple` and `python3-magnetgeo`
   (installing them is a system change needing `sudo`); `python3-pytest`,
   `python3-magnettools`, `python3-packaging`, `python3-yaml`, `debhelper` and
   `dh-python` are already installed. Options:
   - (a) local `dpkg-buildpackage -us -uc -b` after
     `sudo apt install pybuild-plugin-pyproject python3-decouple python3-magnetgeo`
     — fastest, but tests then use the system `python3-magnetgeo` (1.0.1-8);
   - (b) a clean chroot (`sbuild` / `pbuilder`) with the LNCMI apt depot —
     closest to a real build, catches missing Build-Depends;
   - (c) the Debian CI runner on MagnetDB/apt-depot (calcul22, see
     `PLAN_github_runner_setup.md` / `PLAN_apt_ci_upload.md` in
     magnetdb-duckdb-demo) — only once that runner exists.

   Recommended: (b) if a chroot is already set up, else (a).

## Related

- Follow-up: [`PLAN_supra_detail_levels.md`](PLAN_supra_detail_levels.md) —
  DBLPANCAKE / PANCAKE / TAPE support in `magnet_setup`.
- magnetdb-duckdb-demo: part-name refactor of the hoop-stress pipeline
  (`to_duckdb/compute_hoop_stats.py`, `to_duckdb/stress_map.py`). Its count
  check over all assemblies covers the M8 assemblies once this fix lands, so
  this plan is best executed first.
