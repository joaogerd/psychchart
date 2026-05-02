# Changelog

## [1.0.1] - 2026-05-01

### Added
- Bovine bioclimatic chart concept documentation.
- Final Azevedo et al. (2005) bovine bioclimatic chart example combining psychrometrics, ITU field, ITU isolines, experimental T x RH envelopes, CTA-classified trajectory, and accumulated-load legend.
- Semantic labels rendered directly inside continuous index fields.
- Configurable in-field index label styling and manual label positions using T/W or T/RH coordinates.
- Operational overlay layer for management-action fields over psychrometric space.
- Built-in `dairy_cooling_default` operational profile for routine dairy-cattle cooling examples.
- Minimal operational overlay example: `examples/operational_overlay_minimal.yaml`.
- Validated YAML example smoke-test set covering core, path, bioclimatic and operational examples.
- Small deterministic example dataset at `examples/data/observations.csv`.
- Operational overlay documentation and smoke tests.

### Changed
- Operational overlays now render from the declarative `OperationalProfile` and `psychchart.operations.engine.action` decision engine.
- Operational overlay colors, labels, legends and colorbars now come from profile-defined `action_styles`.
- Static overlay `trend` values are converted into representative `dca_dt` values so the same decision engine can support static overlays and future time-series diagnostics.
- Operational overlays are rendered as clean classified contour regions instead of raster-like quadrilateral meshes.
- `thermal_trajectory_classified.yaml` now uses the built-in dairy operational profile by default.
- Runtime payload now carries operational profiles and overlays to the plotting layer.
- Public YAML examples were normalized and documented for execution from the repository root.
- Zone labels support fractional Matplotlib font sizes.
- Runtime dependencies now explicitly include `pandas` and `pydantic>=2`; `pyarrow` is declared as an optional parquet extra.

### Fixed
- Optional operational modifiers with explicit `None` values are now safely ignored.
- Operational overlays now use the registered ITU implementation instead of the obsolete experimental domain engine.
- Operational overlays now resolve humidity ratio through the current psychrometric API.
- Index field labels now warn when the number of labels does not match the number of level intervals instead of failing silently.
- Example data paths were normalized to tracked files under `examples/data/`.
- YAML examples using `animal_day.csv` now use RH auto-detection when the CSV stores RH as percentages.
- Missing `examples/data/observations.csv` was added so data-layer examples render reproducibly.

## [1.0.0] - 2026-04-26

### Added
- Application service layer (`app/services.py`)
- FastAPI backend (`api/fastapi_app.py`)
- API endpoints:
  - `/health`
  - `/render`
  - `/render/file`
- Base64 and binary export support
- CSV data layer builder for interactive usage
- Point readout system (ITU, enthalpy, dew point, W)
- Automated tests for services and API
- API documentation (`docs/api_usage.md`)

### Changed
- Streamlit app refactored to use service layer
- Project architecture reorganized into:
  - core
  - services
  - interfaces (CLI, Streamlit, API)
- README updated for product-level usage

### Improved
- Code modularity and separation of concerns
- Reusability across CLI, app, API
- Type safety using Pydantic and dataclasses

### Fixed
- Reduced duplication between app and core logic

## [0.3.0] - 2026-02-15
### Added
- Separation of index architecture into `domain/` and `data/`
- New `DataIndex` base class for observational indexes
- Support for declarative observational datasets via `ObservationsConfig`
- YAML schema extension for observational data
- Initial integration path for data-driven scalar fields (e.g. ICF)

### Changed
- Refactored index engine to support domain-only evaluation
- Removed domain evaluation capability from data-based indexes
- Internal API cleanup for future extensibility

### Removed
- Legacy compatibility of observational indexes with domain engine

## [0.2.0] - 2026-01-11
### Added
- Modular plotting backend (`plot/` package)
- Support for index fields (e.g. ITU, ITI) over psychrometric domain
- Smoke tests for index field computation and rendering
- New illustrative examples (cartesian ITU, cattle breeds)

### Changed
- Refactored plotting engine for clearer separation of concerns
- Improved internal APIs for zones and index rendering

### Removed
- Deprecated monolithic `plot.py` module

## [0.1.0] - 2026-01-07
### Added
- Arquitetura modular (CLI, loader, plot, psychrometrics)
- Parser YAML centralizado
- Geração de cartas psicrométricas configuráveis
- Testes automatizados com pytest
- CLI `psychchart`

### Fixed
- Normalização consistente de umidade relativa
- Remoção de duplicações e acoplamentos indevidos

