# Changelog

## [Unreleased]
### Added
- Bovine bioclimatic chart concept documentation.
- Final Azevedo et al. (2005) bovine bioclimatic chart example combining psychrometrics, ITU field, ITU isolines, experimental T x RH envelopes, CTA-classified trajectory, and accumulated-load legend.
- Operational overlay layer for management-action fields over psychrometric space.
- Built-in `dairy_cooling_default` operational profile for routine dairy-cattle cooling examples.
- Operational overlay documentation and smoke tests.
- Smoke tests for bovine bioclimatic examples.

### Changed
- Operational overlays are rendered as clean classified contour regions instead of raster-like quadrilateral meshes.
- `thermal_trajectory_classified.yaml` now uses the built-in dairy operational profile by default.
- Runtime payload now carries operational profiles and overlays to the plotting layer.
- Zone labels support fractional Matplotlib font sizes.
- Runtime dependencies now explicitly include `pandas` and `pydantic>=2`; `pyarrow` is declared as an optional parquet extra.

### Fixed
- Optional operational modifiers with explicit `None` values are now safely ignored.
- Operational overlays now use the registered ITU implementation instead of the obsolete experimental domain engine.
- Operational overlays now resolve humidity ratio through the current psychrometric API.
- Example data paths were normalized to tracked files under `examples/data/`.

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

