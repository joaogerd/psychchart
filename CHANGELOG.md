# Changelog

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

