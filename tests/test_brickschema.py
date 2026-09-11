from importlib.metadata import version

from brickschema import __version__


def test_version():
    # __version__ is read from package metadata rather than hardcoded, so it
    # cannot drift away from the version in pyproject.toml
    assert __version__ == version("brickschema")
