# Versioning Policy

The `psychchart` project follows **Semantic Versioning (SemVer)**:

```

MAJOR.MINOR.PATCH

```

## Version meaning

- **MAJOR** version increments (X.0.0)
  - Breaking changes in the public API
  - Changes that invalidate existing scripts, YAML files, or workflows

- **MINOR** version increments (0.X.0)
  - New features
  - Extensions of the YAML schema
  - New plot capabilities
  - Backward-compatible changes

- **PATCH** version increments (0.0.X)
  - Bug fixes
  - Numerical stability improvements
  - Internal refactoring without API changes

## Current development stage

- Versions **0.x.y** indicate an evolving but functional API
- Backward compatibility is preserved within the same MINOR version
- Version **1.0.0** will indicate a stable, frozen public API

## Reproducibility

All scientific results produced with `psychchart` **must report the exact version** used, for example:

```

psychchart v0.1.0

```

Git tags are used to mark all released versions.

