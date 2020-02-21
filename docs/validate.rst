Brick Validate
==============

The `validate` module implements a wrapper of `pySHACL`_ to
validate an ontology graph against default Brick Schema constraints (called *shapes*) and user-defined
shapes.

Please read `Shapes Contraint Language (SHACL)`_
for how it can be used to validate RDF graphs against a set of constraints.

The `Validate.validate()` function is similar to the `pyshacl.validate()` function with the
following addition:  If the
validation results in non-conforming, then each validation graph (representing a single
violation) contains triples predicated by the `offendingTriple` property which help the
user to  pinpoint the violation.  If a violation does not have `offending triples`,
it means there is no appropriate handler for the perticular SHACL shape yet.  In such case
please open an issue with the `brickschema`_ module.

.. _`pySHACL`: https://github.com/RDFLib/pySHACL
.. _`Shapes Contraint Language (SHACL)`: https://www.w3.org/TR/shacl
.. _`brickschema`: https://github.com/BrickSchema/py-brickschema/issues

Note: if validate() returns a violation without a triple predicated with
offendingTriple, that means there is no appropriate handler for the perticular
violation yet.  Please open an issue in such case.

Example
~~~~~~~

.. code-block:: python
