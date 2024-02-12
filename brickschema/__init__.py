"""
Python package `brickschema` provides a set of tools, utilities and interfaces
for working with, developing and interacting with Brick models.
"""

import logging
from . import inference, namespaces, graph
from .graph import Graph, GraphCollection

logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-7s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.WARNING,
)

try:
    from . import rdflib_sqlalchemy
except ImportError:
    logging.warning(
        "sqlalchemy not installed. SQL-backed graph support will not be available."
    )

__version__ = "0.2.0"
__all__ = ["graph", "inference", "namespaces"]
