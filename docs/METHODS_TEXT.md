# Methods — Psychrometric Validation

The psychrometric relationships implemented in the `psychchart`
package are based on classical formulations consistent with
ASHRAE Fundamentals.

Saturation vapor pressure is computed using the
Magnus–Tetens approximation, which provides adequate accuracy
for psychrometric diagram construction.

Validation was performed through:
1. Internal consistency checks,
2. Pointwise comparison with reference values from the literature,
3. Graphical comparison against standard psychrometric charts.

An acceptable relative error threshold of 3% was adopted for
humidity ratio validation, which is appropriate for
diagrammatic psychrometric analysis and thermal comfort studies.

# ICF

We define a Functional Comfort Index (ICF) to quantify instantaneous behavioral functionality by contrasting productive and compensatory behaviors. Productive behaviors are represented by feeding and rumination, while panting is used as the primary compensatory thermoregulatory response. For each observation, the index is computed as (ICF=(F+R)/(F+R+P)), yielding a bounded scalar in ([0,1]) under non-negative inputs and a positive denominator. Higher values represent greater relative allocation to productive behaviors, whereas lower values indicate dominance of compensatory behavior. Importantly, the ICF reflects relative functionality rather than absolute thermal comfort; absolute comfort is defined by physiological optimality criteria and is addressed in the zoning/inference stage.
