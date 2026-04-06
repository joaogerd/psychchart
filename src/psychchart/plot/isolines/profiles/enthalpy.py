"""
Semantic profile for specific-enthalpy isolines (h = const).

This module defines the canonical semantic profile for rendering
specific-enthalpy isolines on a psychrometric chart.

Specific enthalpy is a core thermodynamic quantity in HVAC, drying,
cooling, and air-treatment analyses because it expresses the total energy
content of moist air per unit mass of dry air. In psychrometric diagrams,
enthalpy isolines are typically represented as:

oblique lines with slope similar to wet-bulb lines,

visually differentiated from wet-bulb curves,

labeled in kJ/kg,

clipped at the saturation boundary.

This profile centralizes the semantic defaults associated with enthalpy
curves in a single declarative object, improving consistency and reducing
the need for repeated styling rules across plotting backends.

Notes
-----
In many psychrometric formulations, enthalpy and wet-bulb temperature
isolines may appear nearly parallel over parts of the domain.
For that reason, keeping clearly distinct color and linestyle choices is
important for readability.
Examples
--------
>>> from psychchart.profiles.enthalpy import ENTHALPY_PROFILE
>>> ENTHALPY_PROFILE.name
'enthalpy'
>>> ENTHALPY_PROFILE.values[-1]
120
>>> ENTHALPY_PROFILE.label_fmt
'%.0f kJ/kg'

"""

from .base import IsolineProfile

# =============================================================================
# Specific Enthalpy (h) semantic profile
# =============================================================================
ENTHALPY_PROFILE = IsolineProfile(
    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------
    # Canonical semantic key for the enthalpy isoline family.
    # This identifier must remain stable across the chart architecture.
    name="enthalpy",
    
    # -------------------------------------------------------------------------
    # Default numerical levels
    # -------------------------------------------------------------------------
    # Representative enthalpy levels used in many practical psychrometric
    # applications.
    #
    # Units:
    #     kiloJoules per kilogram of dry air (kJ/kg)
    #
    # The 20 kJ/kg increment is a useful engineering default that offers
    # enough thermodynamic resolution while limiting line density.
    values=[0, 20, 40, 60, 80, 100, 120],
    
    # -------------------------------------------------------------------------
    # Visual style defaults
    # -------------------------------------------------------------------------
    # Orange semantically suggests heat/energy and therefore fits enthalpy
    # better than neutral or moisture-associated tones.
    #
    # A dash-dot pattern helps distinguish enthalpy from wet-bulb lines,
    # which may have a similar visual slope in the chart.
    color="#202020",  # Deep Orange for energy semantics
    linewidth=0.6,
    linestyle="-.",
    alpha=0.6,
    
    # -------------------------------------------------------------------------
    # Labeling behavior
    # -------------------------------------------------------------------------
    # Enthalpy is not directly readable from the main axes, so labels are
    # important for practical use.
    labels=True,
    label_fontsize=6,

    # Label formatting string.
    # The renderer is expected to supply the enthalpy value in kJ/kg.
    label_fmt="%.0f kJ/kg",
    
    # -------------------------------------------------------------------------
    # Rendering hints
    # -------------------------------------------------------------------------
    # Slightly below wet-bulb in emphasis, but still above the background grid.
    zorder=18,
    
    # Enthalpy isolines should not extend into the supersaturated region in
    # a conventional psychrometric chart, hence saturation clipping is kept.
    clip_to_saturation=True,
)
