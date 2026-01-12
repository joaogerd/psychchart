# Changelog

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

