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

                # validate a building against the default shapes and extra shapes created by the uer
                brick_validate myBuilding.ttl -s extraShapes.ttl

Sample output
~~~~~~~~~~~~~

::

   Constraint violation:
   [] a sh:ValidationResult ;
       sh:focusNode bldg:VAV2-3 ;
       sh:resultMessage "Must have at least 1 hasPoint property" ;
       sh:resultPath brick:hasPoint ;
       sh:resultSeverity sh:Violation ;
       sh:sourceConstraintComponent sh:MinCountConstraintComponent ;
       sh:sourceShape [ sh:message "Must have at least 1 hasPoint property" ;
            sh:minCount 1 ;
            sh:path brick:hasPoint ] .
    Violation hint (subject predicate cause):
    bldg:VAV2-3 brick:hasPoint "sh:minCount 1" .

    Constraint violation:
    [] a sh:ValidationResult ;
        sh:focusNode bldg:VAV2-4.DPR ;
        sh:resultMessage "Property hasPoint has object with incorrect type" ;
        sh:resultPath brick:hasPoint ;
        sh:resultSeverity sh:Violation ;
        sh:sourceConstraintComponent sh:ClassConstraintComponent ;
        sh:sourceShape [ sh:class brick:Point ;
             sh:message "Property hasPoint has object with incorrect type" ;
             sh:path brick:hasPoint ] ;
    sh:value bldg:Room-410 .
    Offending triple:
    bldg:VAV2-4.DPR brick:hasPoint bldg:Room-410 .
