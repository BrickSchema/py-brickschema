Validate
========

The `validate` module implements a wrapper of `pySHACL`_ to
validate an ontology graph against default Brick Schema constraints (called *shapes*) and user-defined
shapes.

Please read `Shapes Contraint Language (SHACL)`_
to see how it is used to validate RDF graphs against a set of constraints.

.. _`pySHACL`: https://github.com/RDFLib/pySHACL
.. _`Shapes Contraint Language (SHACL)`: https://www.w3.org/TR/shacl

Example
~~~~~~~

.. code-block:: python

                from brickschema.validate import Validator
                from rdflib import Graph

                # load my building file
                dataG = Graph()
                dataG.parse('myBuilding.ttl', format='turtle')

                # load extra shapes file
                shapeG = Graph()
                shapeG.parse('extraShapes.ttl', format='turtle')

                # validate building against default and extra shapes
                v = Validator()
                result = v.validate(dataG, shacl_graphs=[shapeG])

                # textOutput is meaningful for conforming case, too
                print(result.textOutput)

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
