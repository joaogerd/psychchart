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
## ICF — Functional Comfort Index

 The Functional Comfort Index (ICF) quantifies the *instantaneous behavioral functionality* of an animal by contrasting productive behaviors (feeding and rumination) against compensatory thermoregulatory responses (panting). The ICF is defined as:

 [
 ICF = \frac{F + R}{F + R + P}
 ]

where (F) is feeding, (R) is rumination, and (P) is panting, measured on a common scale (e.g., minutes per hour, percentages, or consistent behavioral scores).

 The ICF is bounded within ([0,1]) for non-negative inputs and a positive denominator. Values closer to 1 indicate higher relative behavioral functionality (i.e., the animal is allocating a larger fraction of its behavioral budget to feeding and rumination rather than panting). Values closer to 0 indicate dominance of compensatory behavior.

**Interpretation note:** ICF does **not** define absolute thermal comfort. A high ICF indicates high *relative functionality* within the observed context; the animal’s typical baseline may still correspond to suboptimal thermal conditions. Absolute comfort requires explicit physiological criteria (e.g., near-zero panting and maximal allocation to productive behaviors), which are handled at the inference/zoning layer.

---

 ### ICFP — Standardized Functional Comfort Index

 The standardized Functional Comfort Index (ICFP) is obtained through post-processing of the instantaneous ICF values relative to a reference distribution. The standardization is performed using a z-score transformation:

 [
 ICFP = \frac{ICF - \mu_{ref}}{\sigma_{ref}}
 ]

where (\mu_{ref}) and (\sigma_{ref}) are the mean and standard deviation of the ICF within the chosen reference (e.g., individual animal, group, or time window). The ICFP quantifies relative deviations from the typical functional state and enables comparison across animals, environments, and periods. Importantly, the ICFP does not represent absolute thermal comfort.

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






