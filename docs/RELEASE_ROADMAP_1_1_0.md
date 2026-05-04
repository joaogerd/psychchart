# psychChart Release Roadmap — Version 1.1.0

This document defines the release-closing roadmap for `psychchart` version `1.1.0`.

It is intended to be used as a practical checklist for issues, branches, Pull Requests and release validation.

The goal is not to expand the scope of the project. The goal is to stabilize what already exists, align code with documentation, validate examples, and prepare a functional, reliable and publishable release.

---

## 1. Executive summary

`psychchart` is close to a stable functional release.

The main technical components already exist:

- YAML-driven psychrometric chart generation;
- Pydantic configuration validation;
- CLI rendering;
- configurable psychrometric isolines;
- geometric zones;
- points;
- domain indexes such as ITU;
- index fields and index isolines;
- in-field semantic labels;
- labeled index-derived zones;
- data layers;
- temporal trajectories;
- classified thermal classes;
- operational overlays;
- explicit intervention zones;
- robust legend infrastructure;
- FastAPI rendering service;
- frontend development base;
- reproducible frontend lockfile;
- documented Git branching workflow.

The project should not receive large new features before the next release.

The next work cycle should focus on:

1. version consistency;
2. official example validation;
3. documentation alignment;
4. API documentation cleanup;
5. release packaging validation;
6. final release tagging.

Recommended next release:

```text
1.1.0
```

Rationale: the repository already declares `1.0.1`, and the recent work adds backward-compatible functionality rather than only patch-level fixes.

---

## 2. Current state

### 2.1 Completed or functionally available

The following items are considered implemented enough to be part of the release, provided they pass final validation:

```text
CLI psychchart
YAML loader
AppConfig/Pydantic validation
ChartConfig
classical psychrometric isolines
geometric zones
points
index configuration
index fields
index isolines
index field labels
labeled index_zones
data_layers
points/scatter/density/scalar_field/path/annotate renderers
classified_points renderer
temporal trajectories
semantic classification profiles
operational_overlays
intervention_zones
legend system
FastAPI /health, /render, /render/file, /readout
frontend base layout
frontend package-lock
branching workflow documentation
```

### 2.2 Partially complete

These items exist but need final alignment before release:

```text
README coverage of newly added features
CHANGELOG coverage of recent PRs
examples/README.txt coverage of new examples
API documentation for /readout
intervention_zones documentation
version consistency across pyproject and package __version__
clear frontend status: official feature or development preview
smoke tests covering all official examples
installation validation outside editable mode
```

### 2.3 Not part of the immediate release scope

These should not block version `1.1.0`:

```text
PyPI publication
notebooks
visual regression tests
frontend served by FastAPI under /app/
advanced YAML editor UX
JSON schema export
plugin system for external indexes
full UTCI physical implementation
large refactors of plot/core.py
large redesign of documentation site
```

---

## 3. Release priorities

### P0 — release blockers

These must be resolved before tagging `v1.1.0`.

#### P0.1 Version consistency

Problem:

- `pyproject.toml` must declare the intended release version.
- `src/psychchart/__init__.py` must expose the same version through `psychchart.__version__`.
- `CHANGELOG.md` must include the same version.

Required outcome:

```text
pyproject.toml              -> version = "1.1.0"
src/psychchart/__init__.py  -> __version__ = "1.1.0"
CHANGELOG.md                -> ## [1.1.0] - YYYY-MM-DD
```

Recommended PR:

```text
release: prepare version 1.1.0
```

---

#### P0.2 Official examples must render

All examples listed as official must run from the repository root without errors.

Minimum command set:

```bash
psychchart examples/minimal.yaml
psychchart examples/example_points.yaml
psychchart examples/example_scatter.yaml
psychchart examples/example_density.yaml
psychchart examples/example_path.yaml
psychchart examples/example_annotate.yaml
psychchart examples/example_path_scatter_annotate.yaml
psychchart examples/example_mixed.yaml
psychchart examples/itu_field_labels.yaml
psychchart examples/index_zone_itu_labeled.yaml
psychchart examples/operational_overlay_minimal.yaml
psychchart examples/intervention_zones_minimal.yaml
psychchart examples/thermal_trajectory_classified.yaml
psychchart examples/bovine_bioclimatic_final_azevedo.yaml
```

Required outcome:

- every official YAML example renders successfully;
- all required data files are tracked;
- historical examples remain outside the validated set.

Recommended PR:

```text
test: validate official YAML examples
```

---

#### P0.3 Test suite must pass

Required command:

```bash
pytest
```

Required outcome:

```text
all tests pass
```

The test suite must include at least:

```text
configuration validation
index field labels
index zone labels
operational overlays
intervention zones
API basic tests
service-layer tests
example smoke tests
```

---

#### P0.4 Package installation must be validated

Required commands in a clean environment:

```bash
python -m pip install .
psychchart --help
```

Development install:

```bash
python -m pip install -e ".[dev]"
pytest
```

API install:

```bash
python -m pip install -e ".[api]"
uvicorn psychchart.api.fastapi_app:app --reload
```

Parquet support:

```bash
python -m pip install -e ".[parquet]"
```

Required outcome:

- package installs cleanly;
- CLI entry point works;
- optional extras install their expected dependencies.

---

### P1 — should be completed for 1.1.0

#### P1.1 README update

The README must mention the features that are part of the release.

Required updates:

```text
index_zones with internal labels
intervention_zones
/readout endpoint
frontend status
branching workflow link
official example list alignment
```

Recommended PR:

```text
docs: update README for 1.1.0 features
```

---

#### P1.2 CHANGELOG update

Add a `1.1.0` section covering recent changes.

Must include:

```text
readout endpoint
frontend workspace base
frontend package-lock
labeled index_zones
intervention_zones standalone layer
intervention_zones YAML pipeline integration
branching workflow documentation
release roadmap documentation
```

Recommended PR:

```text
docs: update changelog for 1.1.0
```

---

#### P1.3 examples/README.txt update

Add newly supported examples:

```text
psychchart examples/index_zone_itu_labeled.yaml
psychchart examples/intervention_zones_minimal.yaml
```

Make clear that `examples_old/` is historical and not part of the validated release set.

Recommended PR:

```text
docs: align official example list
```

---

#### P1.4 API documentation update

`docs/api_usage.md` should document:

```text
GET /health
POST /render
POST /render/file
POST /readout
```

The `/readout` example should include input and output fields:

```json
{
  "T": 31.0,
  "RH_pct": 65.0,
  "pressure": 101325.0
}
```

Expected output fields:

```text
T
RH_pct
RH
W
h
Tdp
ITU
```

Recommended PR:

```text
docs: document readout API endpoint
```

---

#### P1.5 Intervention zone documentation

Create:

```text
docs/INTERVENTION_ZONES.md
```

The document must explain:

```text
what intervention_zones are
how they differ from operational_overlays
when to use recommended rules
when to use inappropriate_rules
how vector works
how hatch works
how label_style works
how to run the minimal example
```

Recommended PR:

```text
docs: add intervention zones guide
```

---

### P2 — desirable but can wait

These are useful but should not block `1.1.0`:

```text
notebooks
PyPI publication
visual image regression tests
frontend served from FastAPI
full documentation website
advanced web UI workflow
schema export
external plugin registry
more bioclimatic indexes
```

---

## 4. Technical inconsistencies to resolve

### 4.1 Version mismatch risk

Likely files:

```text
pyproject.toml
src/psychchart/__init__.py
CHANGELOG.md
```

Impact:

- wrong release metadata;
- confusing tags;
- user cannot determine installed version reliably.

Resolution:

- set all version references to `1.1.0`;
- add a version consistency test.

Suggested test:

```python
import importlib.metadata as metadata
import psychchart


def test_package_version_matches_public_version():
    assert psychchart.__version__ == metadata.version("psychchart")
```

---

### 4.2 Official examples not centralized

Likely files:

```text
examples/README.txt
tests/test_bioclimatic_examples.py
possibly tests/test_examples_smoke.py
```

Impact:

- README may list examples that are not tested;
- tests may cover examples not documented;
- release validation becomes manual and error-prone.

Resolution:

- create one canonical list of official examples inside tests;
- keep `examples/README.txt` aligned with that list.

---

### 4.3 intervention_zones not fully documented

Likely files:

```text
docs/INTERVENTION_ZONES.md
README.md
examples/intervention_zones_minimal.yaml
```

Impact:

- users may confuse `intervention_zones` with `operational_overlays`;
- the chart decision layer may be misused.

Resolution:

- document the conceptual distinction;
- provide minimal and practical YAML examples.

---

### 4.4 Frontend release status unclear

Likely files:

```text
README.md
frontend/README.md
frontend/package.json
frontend/package-lock.json
```

Impact:

- users may expect a finished product UI;
- release scope becomes too broad.

Resolution:

For `1.1.0`, mark the frontend as:

```text
development preview
```

not as the primary stable interface.

Stable interfaces for `1.1.0` should be:

```text
Python API
CLI
YAML examples
FastAPI basic endpoints
```

---

### 4.5 CLI error messages need minimum quality

Likely files:

```text
src/psychchart/cli.py
src/psychchart/loader.py
```

Impact:

- users may struggle with invalid YAML, missing files or bad data columns.

Resolution for `1.1.0`:

- keep traceback in debug/dev mode if desired;
- ensure the first error line clearly reports the failed file and main reason.

Minimum cases:

```text
missing YAML file
invalid YAML key
missing data file
unknown index
missing data column
```

---

## 5. Minimum scope for version 1.1.0

### In scope

```text
CLI chart rendering
YAML configuration
psychrometric isolines
geometric zones
points
ITU field/isoline rendering
index field semantic labels
labeled index_zones
data_layers
trajectory/path rendering
classified thermal points
operational_overlays
intervention_zones
legend support
FastAPI basic rendering and readout
frontend development preview
validated examples
release documentation
```

### Out of scope

```text
full web application product
notebooks
PyPI release automation
visual regression testing
full plugin API
full UTCI implementation
large core refactor
serving frontend under FastAPI /app/
```

---

## 6. Release-closing checklist

### Code

```text
[ ] Align pyproject.toml version.
[ ] Align psychchart.__version__.
[ ] Add version consistency test.
[ ] Ensure intervention_zones savefig works.
[ ] Ensure operational_overlays still render.
[ ] Ensure index field labels still render.
[ ] Ensure index_zone labels still render.
[ ] Ensure data_layers examples still render.
```

### Tests

```text
[ ] pytest passes.
[ ] Official example smoke tests pass.
[ ] API tests pass.
[ ] CLI basic error tests pass.
[ ] Frontend build passes if frontend is part of release validation.
```

### Documentation

```text
[ ] README updated.
[ ] CHANGELOG updated.
[ ] examples/README.txt updated.
[ ] docs/api_usage.md updated.
[ ] docs/INTERVENTION_ZONES.md added.
[ ] docs/BRANCHING_WORKFLOW.md linked from README.
[ ] docs/RELEASE_ROADMAP_1_1_0.md added.
```

### Packaging

```text
[ ] python -m pip install . works.
[ ] python -m pip install -e ".[dev]" works.
[ ] python -m pip install -e ".[api]" works.
[ ] python -m pip install -e ".[parquet]" works.
[ ] psychchart --help works.
```

### Manual validation

```text
[ ] psychchart examples/minimal.yaml
[ ] psychchart examples/example_points.yaml
[ ] psychchart examples/example_scatter.yaml
[ ] psychchart examples/example_density.yaml
[ ] psychchart examples/example_path.yaml
[ ] psychchart examples/itu_field_labels.yaml
[ ] psychchart examples/index_zone_itu_labeled.yaml
[ ] psychchart examples/operational_overlay_minimal.yaml
[ ] psychchart examples/intervention_zones_minimal.yaml
[ ] psychchart examples/thermal_trajectory_classified.yaml
[ ] psychchart examples/bovine_bioclimatic_final_azevedo.yaml
```

API validation:

```text
[ ] uvicorn psychchart.api.fastapi_app:app --reload
[ ] curl /health
[ ] curl /readout
[ ] curl /render
```

Frontend validation:

```text
[ ] cd frontend
[ ] npm ci
[ ] npm run build
```

---

## 7. Revised roadmap

### Phase 1 — Release preparation

Objective:

Prepare metadata, versioning and changelog for `1.1.0`.

Tasks:

```text
update pyproject.toml
update src/psychchart/__init__.py
add version consistency test
update CHANGELOG.md
```

Deliverable:

```text
PR: release: prepare version 1.1.0
```

Acceptance criteria:

```text
pytest passes
python -c "import psychchart; print(psychchart.__version__)" prints 1.1.0
importlib.metadata.version("psychchart") returns 1.1.0
CHANGELOG contains 1.1.0
```

Branch required:

```text
release/prepare-1.1.0
```

---

### Phase 2 — Official example validation

Objective:

Guarantee that documented examples actually work.

Tasks:

```text
update examples/README.txt
create/update smoke tests for all official examples
remove unstable examples from official list
ensure required data files are tracked
```

Deliverable:

```text
PR: test: validate official examples
```

Acceptance criteria:

```text
pytest passes
all official examples render without error
no official example depends on untracked data
```

Branch required:

```text
test/official-example-smoke
```

---

### Phase 3 — Documentation alignment

Objective:

Make user-facing documentation consistent with release functionality.

Tasks:

```text
update README.md
add docs/INTERVENTION_ZONES.md
update docs/api_usage.md
link docs/BRANCHING_WORKFLOW.md
explain frontend as development preview
```

Deliverable:

```text
PR: docs: align documentation for 1.1.0
```

Acceptance criteria:

```text
README mentions all stable release features
/readout is documented
intervention_zones is documented
frontend status is explicit
```

Branch required:

```text
docs/release-1.1.0-alignment
```

---

### Phase 4 — Package validation

Objective:

Ensure installation and optional extras work.

Tasks:

```text
test non-editable install
test dev install
test api extra
test parquet extra
test CLI entry point
```

Deliverable:

```text
PR if fixes are needed; otherwise validation note in release PR
```

Acceptance criteria:

```text
python -m pip install . works
psychchart --help works
pytest works after dev install
api extra installs uvicorn/fastapi/httpx
parquet extra installs pyarrow
```

Branch required:

```text
fix/package-validation
```

only if changes are needed.

---

### Phase 5 — Release tagging

Objective:

Tag and publish the release from `main`.

Tasks:

```text
merge develop/main as appropriate
pull latest main
run final validation
create annotated tag
push tag
create GitHub release
```

Commands:

```bash
git checkout main
git pull origin main
pytest
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0
```

Verify tag target:

```bash
git rev-parse v1.1.0^{}
git rev-parse origin/main
```

Acceptance criteria:

```text
tag points to origin/main
release notes match CHANGELOG
all release validation commands pass
```

Branch required:

```text
none
```

---

## 8. Objective release acceptance criteria

The version `1.1.0` is ready only when all items below are true.

### Tests

```bash
pytest
```

passes.

### CLI

```bash
psychchart --help
```

works.

### Official examples

```bash
psychchart examples/minimal.yaml
psychchart examples/itu_field_labels.yaml
psychchart examples/index_zone_itu_labeled.yaml
psychchart examples/operational_overlay_minimal.yaml
psychchart examples/intervention_zones_minimal.yaml
psychchart examples/thermal_trajectory_classified.yaml
psychchart examples/bovine_bioclimatic_final_azevedo.yaml
```

all render without error.

### API

```bash
uvicorn psychchart.api.fastapi_app:app --reload
```

starts successfully.

```bash
curl http://127.0.0.1:8000/health
```

returns a healthy response.

```bash
curl -X POST http://127.0.0.1:8000/readout \
  -H 'Content-Type: application/json' \
  -d '{"T": 31.0, "RH_pct": 65.0, "pressure": 101325.0}'
```

returns psychrometric readout fields.

### Frontend preview

```bash
cd frontend
npm ci
npm run build
```

passes if the frontend is included in release validation.

### Version

```bash
python -c "import psychchart; print(psychchart.__version__)"
python -c "import importlib.metadata as m; print(m.version('psychchart'))"
```

both return:

```text
1.1.0
```

---

## 9. Final action plan

Execute in this order:

```text
1. Create or update develop from main.
2. Merge this roadmap documentation.
3. Create release/prepare-1.1.0.
4. Fix version consistency.
5. Update CHANGELOG.md.
6. Update README.md and examples/README.txt.
7. Add docs/INTERVENTION_ZONES.md.
8. Update docs/api_usage.md with /readout.
9. Add or update official example smoke tests.
10. Run pytest.
11. Run official examples manually once.
12. Validate pip installation.
13. Validate API.
14. Validate frontend build as preview.
15. Merge release preparation into main.
16. Tag v1.1.0 from main.
17. Publish GitHub release.
18. Delete release branches.
```

---

## 10. Scope control rule

No new major features should be added before `1.1.0`.

Allowed before release:

```text
bug fixes
documentation alignment
example validation
version correction
packaging correction
small test additions
```

Not allowed before release:

```text
large architecture refactors
new index families
new frontend workflows
new API products
major rendering redesigns
new scientific models
```

The release should prioritize stability, clarity, reproducibility and ease of use.
