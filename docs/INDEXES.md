# Thermal and Bioclimatic Indexes

This document describes the thermal and bioclimatic indexes
implemented in the `psychchart` package.

These indexes are empirical or semi-empirical formulations
used to assess thermal comfort or heat stress conditions,
and are conceptually distinct from the psychrometric
relationships implemented in `psychrometrics.py`.

---

## Design principles

- Indexes are implemented independently of the plotting engine
- Psychrometric physics and comfort interpretation are separated
- Each index has a clearly defined scope and limitations
- All indexes are reproducible and testable

---

## Implemented indexes

### ITU — Temperature-Humidity Index

The Temperature-Humidity Index (ITU), also referred to as THI,
is widely used in animal and human thermal comfort studies.

Typical formulation:

```

ITU = T - (0.55 - 0.0055 * RH) * (T - 14.5)

```

Where:
- T is the dry-bulb temperature (°C)
- RH is the relative humidity (0–100%)

#### Scope of use
- Heat stress screening
- Comparative comfort analysis
- Livestock and environmental studies

#### Limitations
- Does not account for wind speed or solar radiation
- Not intended for extreme climatic conditions

---

## Future extensions

Planned indexes include:
- Heat Load Index (HLI)
- Givoni bioclimatic comfort zones
- UTCI (Universal Thermal Climate Index)

---

## References

- Thom, E. C. (1959). The discomfort index.
- Hahn, G. L. (1999). Dynamic responses of cattle to thermal heat loads.
- Gaughan et al. (2008). Heat Load Index for feedlot cattle.


