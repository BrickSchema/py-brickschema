Handler
--------

The base Brickify Handler takes in an existing graph and updates it. 
The handler reads the entire graph into memory in one pass, and then runs each **operation** once against the entire graph. 
(Note that this is different than the TableHandler we were using in the example, which goes row-by-row through the input file, and runs the full set of operations against each row, e.g. if you have 3 rows and 2 operations, each of the 2 operations are run 3 times, once per row, for a total of 6 operations overall)

The base Handler is invoked when the ``--input-format`` option is set to ``graph`` or ``rdf`` or is left unspecified. 

The supported **operations** for the base Handler are 'query' and 'data'. The 'query' operation executes a SPARQL update query to transform the input graph. 
Consider this example template.yml file:

.. code-block:: yaml

  ---
  namespace_prefixes:
    brick: "https://brickschema.org/schema/Brick#"
    yao: "https://example.com/YetAnotherOnology#"
  operations:
    -
      query: |-
          DELETE {{
            ?vav a yao:vav .
          }}
          INSERT {{
            ?vav a brick:VAV .
          }}
          WHERE {{
            ?vav a yao:vav .
          }}
    -
      query: |-
          DELETE {{
            ?rvav a yao:vav_with_reheat .
          }}
          INSERT {{
            ?rvav a brick:RVAV .
          }}
          WHERE {{
            ?rvav a yao:vav_with_reheat .
          }}

This example has two **operations**, both of which are 'query' operations. 
Each operation is basically translating between one namespace and into another. 
The queries select a set of triples from the original graph, delete them from the original graph, and reinsert them into the new graph but in a new namespace.
