"""
Python package `brickschema` provides a set of tools, utilities and interfaces
for working with, developing and interacting with Brick models.
"""

import logging

logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-7s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.WARNING)

from . import graph, inference, namespaces, validate

__version__ = '0.0.12'
__all__ = ['graph', 'inference', 'namespaces', 'orm', 'validate']
