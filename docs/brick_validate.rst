brick_validate Command
=========

The `brick_validate` command is similar to the `pyshacl`_ command with simplied command
line arguments to validate a building data graph against the Brick ontology and
`Shapes Contraint Language (SHACL)`_ contraints.

If the validation results show contraint violations, the `brick_validate` command provides
the offending triples associated to the violations in addition to the violation report by `pyshacl`.

Please note: If the command cannot find an offending triple for a reported violation,
it means there is no appropriate handler for the perticular SHACL shape yet.  In such case
please open an issue with the `brickschema`_ module.


.. _`pySHACL`: https://github.com/RDFLib/pySHACL
.. _`Shapes Contraint Language (SHACL)`: https://www.w3.org/TR/shacl
.. _`brickschema`: https://github.com/BrickSchema/py-brickschema/issues


Example
~~~~~~~

.. code-block:: bash
