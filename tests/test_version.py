import importlib.metadata as metadata

import psychchart


def test_public_version_matches_package_metadata():
    """The public package version must match installed package metadata."""
    assert psychchart.__version__ == metadata.version("psychchart")
