brick_validate Command
======================

The `brick_validate` command is similar to the `pyshacl`_ command with simplied command
line arguments to validate a building ontology against the Brick Schema and
`Shapes Contraint Language (SHACL)`_ contraints made for it.

When the validation results show contraint violations, the `brick_validate` command provides
extra information associated with the violations in addition to the violation report by `pyshacl`.  The extra infomation may be the *offending triple* or *violation hint*.

If no extra information is given for a reported violation,
it means there is no appropriate handler for the perticular violation yet.
If you think extra info is needed for the particular case,
please open an issue with the `brickschema`_ module.

.. _`pySHACL`: https://github.com/RDFLib/pySHACL
.. _`Shapes Contraint Language (SHACL)`: https://www.w3.org/TR/shacl
.. _`brickschema`: https://github.com/BrickSchema/py-brickschema/issues


Example
~~~~~~~

.. code-block:: bash

                # BrickShape.ttl is the default shapes generated for Brick
                brick_validate myBuilding.ttl -s extraShapes.ttl -s BrickShape.ttl

Sample output
~~~~~~~~~~~~~

.. literalinclude:: brick_validate_sample_output
