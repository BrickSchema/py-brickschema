"""
Python package `brickschema` provides a set of tools, utilities and interfaces
for working with, developing and interacting with Brick models.
"""

import logging
from .graph import Graph
from .namespaces import bind_prefixes
from . import inference, namespaces, validate, web

logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-7s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.WARNING,
)


__version__ = "0.2.0"
__all__ = ["graph", "inference", "namespaces", "orm", "validate", "web"]
