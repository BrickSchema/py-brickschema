"""
Python package `brickschema` provides a set of tools, utilities and interfaces
for working with, developing and interacting with Brick models.

.. include:: index.rst
"""
from . import graph, inference, namespaces

__version__ = '0.0.12'
__all__ = ['graph', 'inference', 'namespaces', 'orm']
