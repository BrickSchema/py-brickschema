Validate
========

The module utilizes the `pySHACL`_ package to validate a building ontology against the Brick Schema, its default constraints (shapes) and user provided shapes.

Please read `Shapes Constraint Language (SHACL)`_
to see how it is used to validate RDF graphs against a set of constraints.

.. _`pySHACL`: https://github.com/RDFLib/pySHACL
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
  valid, _, report = g.validate(shape_graphs=[external])
  print(f"Graph is valid? {valid}")
  if not valid:
    print(report)

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
