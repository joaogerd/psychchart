from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClassificationRule:
    """
    One semantic classification rule.

    Parameters
    ----------
    upper : float
        Exclusive upper bound for this class.
    color : str
        Color associated with this class.
    label : str
        Human-readable class label.
    """
    upper: float
    color: str
    label: str


@dataclass(frozen=True)
class ClassificationProfile:
    """
    Generic numeric classification profile.

    A profile is an ordered sequence of upper-bounded rules. The first rule
    whose upper bound is greater than the input value is selected.

    Parameters
    ----------
    name : str
        Profile name used in the registry and YAML.
    rules : tuple[ClassificationRule, ...]
        Ordered classification rules.
    """

    name: str
    rules: tuple[ClassificationRule, ...]

    def __post_init__(self) -> None:
        if not self.rules:
            raise ValueError(f"Classification profile {self.name!r} has no rules.")

        uppers = [rule.upper for rule in self.rules]
        if uppers != sorted(uppers):
            raise ValueError(
                f"Classification profile {self.name!r} must have rules sorted "
                f"by increasing upper bound."
            )

    def classify(self, value: float) -> ClassificationRule:
        """
        Classify one numeric value according to the profile rules.

        Parameters
        ----------
        value : float
            Input numeric value.

        Returns
        -------
        ClassificationRule
            Matching rule.
        """
        value = float(value)
        for rule in self.rules:
            if value < rule.upper:
                return rule
        return self.rules[-1]
