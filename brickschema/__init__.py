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

has_sqlalchemy = False
try:
    import rdflib_sqlalchemy
    has_sqlalchemy = True
except ImportError as e:
    print(e)
    logging.warning(
        "sqlalchemy not installed. SQL-backed graph support will not be available. Try 'pip install brickschema[persistence]' to install it."
    )

__version__ = "0.2.0"
__all__ = ["graph", "inference", "namespaces"]
if has_sqlalchemy:
    __all__.append("rdflib_sqlalchemy")
