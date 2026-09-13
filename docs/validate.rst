Validate
========

``Graph.validate()`` validates a building ontology against the Brick Schema,
its default constraints (shapes) and user provided shapes. It does not modify
the graph.

Please read `Shapes Constraint Language (SHACL)`_
to see how it is used to validate RDF graphs against a set of constraints.

.. _`Shapes Contraint Language (SHACL)`: https://www.w3.org/TR/shacl

Example
~~~~~~~

.. code-block:: python

  from brickschema import Graph

  g = Graph(load_brick=True)
  g.load_file('myBuilding.ttl')
  valid, _, report = g.validate()
  print(f"Graph is valid? {valid}")
  if not valid:
    print(report)

  # validating using externally-defined shapes
  external = Graph()
  external.load_file("other_shapes.ttl")
  valid, _, report = g.validate(extra_graphs=[external])
  print(f"Graph is valid? {valid}")
  if not valid:
    print(report)

SHACL engines
~~~~~~~~~~~~~

Both :meth:`~brickschema.graph.BrickBase.validate` and
:meth:`~brickschema.graph.BrickBase.compile` are backed by a pluggable SHACL
engine, chosen with the ``engine`` keyword. When none is named, the first
installed engine from this list is used:

- ``"shifty"`` (default) -- Rust SHACL/SHACL-AF engine from ``pyshifty``,
  installed by default. Runs rules to a fixed point.
- ``"topquadrant"`` -- TopQuadrant's Java implementation; install with
  ``pip install brickschema[topquadrant]``.
- ``"pyshacl"`` -- pure-Python implementation, installed by default.

.. code-block:: python

  valid, _, report = g.validate(engine="pyshacl")

``min_iterations`` and ``max_iterations`` bound how many rule passes are made.
They apply to the ``pyshacl`` and ``topquadrant`` engines only, since
``shifty`` always runs to a fixed point.

Sample default shapes (in BrickShape.ttl)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    # brick:hasLocation's object must be of brick:Location type
    bsh:hasLocationRangeShape a sh:NodeShape ;
        sh:property [ sh:class brick:Location ;
            sh:message "Property hasLocation has object with incorrect type" ;
            sh:path brick:hasLocation ] ;
        sh:targetSubjectsOf brick:hasLocation .

    # brick:isLocationOf's subject must be of brick:Location type
    bsh:isLocationOfDomainShape a sh:NodeShape ;
        sh:class brick:Location ;
        sh:message "Property isLocationOf has subject with incorrect type" ;
        sh:targetSubjectsOf brick:isLocationOf .
