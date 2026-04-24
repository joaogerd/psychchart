# Bovine Bioclimatic Chart

## Purpose

The bovine bioclimatic chart is a design target for psychChart. Its purpose is to extend a conventional psychrometric chart into an interpretative and operational diagram for cattle heat-stress analysis.

The chart must not be treated as a simple diagnostic plot. Its role is to combine physical psychrometrics, thermal indices, physiological thresholds, observed environmental envelopes, accumulated thermal load, and management decisions in a single reproducible figure.

## Conceptual layers

A complete bovine bioclimatic chart is organized as layered information:

1. **Psychrometric base**

   The base chart contains dry-bulb temperature, humidity ratio, saturation curve, relative-humidity isolines, and optional physical isolines such as wet-bulb temperature, enthalpy, and specific volume.

2. **Thermal-index field**

   A thermal index such as ITU, HLI, BGHI, thermal excess, or accumulated thermal load is computed over the chart domain and rendered as a smooth field or classified bands.

3. **Physiological thresholds**

   Critical thresholds are drawn as isolines or semantic bands. In the Azevedo et al. (2005) example, the ITU thresholds are associated with Holstein-Zebu genetic groups.

4. **Literature-derived climatic envelopes**

   Experimental ranges from published studies are drawn as T x RH envelopes. These envelopes describe the environmental domain observed in a study. They are not automatically interpreted as comfort zones.

5. **Observed data layers**

   Observed or simulated records may be overlaid as scatter points, density fields, classified points, or temporal trajectories.

6. **Operational management overlays**

   Management recommendations such as monitoring, ventilation, ventilation plus sprinkling, intensive cooling, recovery, and emergency response are future operational layers. They must be derived from an explicit decision policy rather than mixed directly with literature envelopes.

## Azevedo et al. (2005) example

The initial bovine bioclimatic chart example uses Azevedo et al. (2005) as a case study.

The figure combines:

- a psychrometric base chart;
- an ITU field;
- semantic ITU bands;
- critical ITU isolines for genetic groups;
- T x RH experimental envelopes from the article;
- a sample temporal trajectory classified by accumulated thermal load.

The intended reading is:

- the background colors show ITU intensity;
- the ITU isolines show physiological thresholds;
- the T x RH polygons show where the experimental environmental conditions occurred;
- the data trajectory shows how a monitored animal or environment moves through the bioclimatic space over time;
- future operational layers will translate the same state space into management actions.

## Important scientific distinction

The chart must preserve the distinction between four different concepts:

1. **Observed environmental envelope**

   A range of temperature and relative humidity reported in a study.

2. **Physiological threshold**

   A thermal-index value associated with a measured biological response such as respiratory frequency or rectal temperature.

3. **Accumulated load state**

   A temporal condition derived from persistence of heat exposure, such as accumulated thermal excess over a sliding window.

4. **Operational recommendation**

   A management decision derived from the current environment, accumulated load, trend, and production context.

These concepts must remain visually and architecturally separable.

## Implementation direction

The implementation should use existing psychChart components whenever possible:

- `indexes` for computed ITU/HLI/BGHI/thermal-excess fields and isolines;
- `index_zones` for classified thermal-index bands;
- `zones` for literature-derived T x RH envelopes;
- `data_layers` for observed points, density fields, paths, annotations, and classified trajectories;
- `chart.legend` for declarative legends;
- `operational_profiles` and `operational_overlays` for future management-decision layers.

The Azevedo et al. example is the first concrete chart template. The same architecture should later support dairy compost-barn studies using accumulated thermal load and panting/respiratory response.
