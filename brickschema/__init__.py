"""
Python package `brickschema` provides a set of tools, utilities and interfaces
for working with, developing and interacting with Brick models.
"""

import importlib.util
import logging
from importlib.metadata import PackageNotFoundError, version as _version

from . import inference, namespaces, graph, shacl
from .graph import Graph, GraphCollection

logger = logging.getLogger(__name__)

try:
    __version__ = _version("brickschema")
except PackageNotFoundError:  # running from a source tree without an install
    __version__ = "0.0.0.dev0"

has_sqlalchemy = importlib.util.find_spec("rdflib_sqlalchemy") is not None
if not has_sqlalchemy:
    logger.debug(
        "rdflib-sqlalchemy not installed. SQL-backed graph support will not be "
        "available. Try 'pip install brickschema[persistence]' to install it."
    )

__all__ = ["Graph", "GraphCollection", "graph", "inference", "namespaces", "shacl"]
