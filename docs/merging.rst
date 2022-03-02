Merging Brick Models
====================

.. tip::
   To use this feature, install brickschema with the "merge" feature: `pip install brickschema[merge]` or `pip install brickschema[all]`

This module implements techniques for merging multiple Brick models into a single cohesive graph using techniques from a `BuildSys 2020 paper`_. Eventually, other implementations may make their way into this module.

The module defines a `merge_type_cluster` function which interactively merges two Brick graphs together. This function finds instances in both graphs which are of the same type

.. _`BuildSys 2020 paper`: https://dl.acm.org/doi/abs/10.1145/3408308.3427627


Example
~~~~~~~

.. code-block:: python

    import brickschema
    from brickschema.merge import merge_type_cluster
    from rdflib import Namespace

    # both graphs must have the same namespace
    # AND must have RDFS.label for all entities
    BLDG = Namespace("http://example.org/building/")

    def validate(g):
        valid, _, report = g.validate()
        if not valid:
            raise Exception(report)

    g1 = brickschema.Graph().load_file("bldg1")
    #validate(g1)

    g2 = brickschema.Graph().load_file("bldg2")
    #validate(g2)

    G = merge_type_cluster(g1, g2, BLDG, similarity_threshold=0.1)
    validate(G)
    G.serialize("merged.ttl", format="ttl")
