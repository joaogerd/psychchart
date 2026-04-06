"""
Base configuration foundations for psychchart.

This module defines the strict base model used throughout the ``psychchart``
configuration system.

It centralizes the shared validation policy adopted by all typed configuration
models in the project, ensuring that nested configuration sections behave in a
consistent, predictable, and safe way. By concentrating the common Pydantic
behavior in a single base class, the package avoids duplicated validation
settings and keeps configuration semantics uniform across modules.

The main purpose of this module is to provide a reusable configuration
foundation on top of which all specialized models are built.

Notes
-----
This module defines validation policy, not domain-specific configuration
content.

It is responsible for:
- enforcing strict handling of unknown fields
- enabling assignment validation
- providing a shared base class for all configuration sections

It is not responsible for:
- chart semantics
- plotting logic
- psychrometric equations
- YAML loading
- runtime conversion

See Also
--------
app
    Root validated configuration model.
chart
    Chart-level configuration definitions.
isolines
    Isoline-family configuration models.
indexes
    Index configuration models.

Examples
--------
Define a strict configuration model:

>>> class ExampleConfig(StrictModel):
...     name: str
...     enabled: bool = True
...
>>> cfg = ExampleConfig.model_validate({"name": "demo"})
>>> cfg.name
'demo'
>>> cfg.enabled
True
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """
    Strict base model for configuration sections.

    This class provides a shared Pydantic configuration policy for all
    strongly typed configuration models in the project. It is intended to be
    subclassed by specialized configuration sections such as chart settings,
    isoline definitions, index descriptions, and other nested application
    configuration blocks.

    The main purpose of this base class is to enforce predictable and safe
    validation behavior across the configuration system.

    Parameters
    ----------
    None
        This class does not define concrete data fields by itself. Concrete
        subclasses introduce the actual configuration attributes.

    Returns
    -------
    StrictModel
        An instance of a concrete subclass after validation.

    Raises
    ------
    pydantic.ValidationError
        Raised when input data contains invalid field types, missing required
        fields in subclasses, or unknown keys that are explicitly forbidden by
        this base model configuration.

    Notes
    -----
    The internal ``model_config`` enforces three important behaviors:

    ``extra="forbid"``
        Rejects unknown fields instead of silently ignoring them. This is
        especially important for configuration systems, because misspelled keys
        can otherwise pass unnoticed and produce confusing runtime behavior.

    ``validate_assignment=True``
        Revalidates values when attributes are modified after model creation.
        This helps preserve consistency over the full lifecycle of the object.

    ``populate_by_name=True``
        Allows field population by their declared names, which is useful when
        aliases are introduced in downstream configuration models.

    This class is intentionally minimal. It centralizes validation policy, so
    individual configuration models do not need to repeat the same Pydantic
    settings.

    See Also
    --------
    pydantic.BaseModel
        Core Pydantic base class from which this strict configuration base
        inherits.
    pydantic.ConfigDict
        Declarative configuration object used to customize model behavior.

    Examples
    --------
    Create a concrete configuration model derived from ``StrictModel``:

    >>> class DatabaseConfig(StrictModel):
    ...     host: str
    ...     port: int
    ...
    >>> cfg = DatabaseConfig.model_validate({"host": "localhost", "port": 5432})
    >>> cfg.host
    'localhost'
    >>> cfg.port
    5432

    Unknown fields are rejected to avoid silent configuration mistakes:

    >>> DatabaseConfig.model_validate(
    ...     {"host": "localhost", "port": 5432, "timeout": 10}
    ... )
    Traceback (most recent call last):
        ...
    pydantic_core._pydantic_core.ValidationError: ...

    Assignment is also validated after instantiation:

    >>> cfg = DatabaseConfig.model_validate({"host": "localhost", "port": 5432})
    >>> cfg.port = 3306
    >>> cfg.port
    3306
    """

    # ``model_config`` centralizes the validation policy shared by every
    # configuration model that inherits from this base class.
    model_config = ConfigDict(
        # Reject unexpected keys to prevent silent acceptance of typos or
        # unsupported configuration options.
        extra="forbid",
        # Re-run validation whenever an attribute is reassigned after model
        # creation, preserving type and semantic consistency.
        validate_assignment=True,
        # Allow population using declared field names, which is useful when
        # subclasses define aliases or alternate external representations.
        populate_by_name=True,
    )
