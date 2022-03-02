Brickify tool
=========

.. tip::
   To use this feature, install brickschema with the "brickify" feature: `pip install brickschema[brickify]` or `pip install brickschema[all]`

The `brickify` tool is used to create Brick models from other data sources.
It is installed as part of the ``brickschema`` package.
If you installed py-brickschema from Github you may have usage examples included in the tests directory, otherwise, you can find them online in the `test source tree`_.

.. _`test source tree`: https://github.com/BrickSchema/py-brickschema/tree/master/tests/data/brickify

The `brickify` tool is built around the notion of **handlers** and **operations**.
**Handlers** are pieces of code (written in Python) that the `brickify` tool uses to carry out **operations** that transform data.

**Handlers** are how data is loaded by `brickify` and contain the code that executes the translations that are specified by the **operations**.

**Operations** are specified in a configuration file when the `brickify` tool is invoked by the user.


We expect that most users of `brickify` will not have to write a **Handler**, though they may need to write their own set of **operations**.
Over time, we hope to include an expanded library of useful **Handlers** in `brickify` as well as example **operations** that can be easily customized for a particular job.

We expect a common scenario will be for `brickify` and the included **handlers** to be used as a tool in a building system integration job, where the **operations** might be written by the technical support team supporting the integration job, and then invoked by the field team against different data sources and building systems, with perhaps a small bit of customization.

Using Brickify
--------------
The `brickify` tool can be invoked on the command line as follows:

.. code-block:: bash

                brickify sheet.tsv --output bldg.ttl --input-type tsv --config template.yml

where sheet.tsv might be a tabled stored in CSV/TSV file.

`brickify` starts with an empty graph, and uses **handlers** and **operations** to add the data from the input file (in this case, sheet.tsv) to the graph, and then write that graph out to a file (bldg.ttl)

For example, consider the following basic table with two rows that might be stored in ``sheet.tsv``


+--------+------------------+--------------------+----------+
|VAV name|temperature sensor|temperature setpoint|has_reheat|
+========+==================+====================+==========+
|A       | A_ts             | A_sp               | false    |
+--------+------------------+--------------------+----------+
|B       | B_ts             | B_sp               | true     |
+--------+------------------+--------------------+----------+

`Brickify` selects the handler to use based on the input-type of the file. In this case, `brickify` will use the **TableHandler** to process the data.

Brickify loads the **operations** from the config file specified when `brickify` is run.
The config file can be in either YAML or JSON, but for our examples we will use YAML.
Here is an example `template.yml`

.. code-block:: yaml

  ---
  namespace_prefixes:
    brick: "https://brickschema.org/schema/Brick#"
  operations:
    -
      data: |-
        bldg:{VAV name} rdf:type brick:VAV ;
                        brick:hasPoint bldg:{temperature sensor} ;
                        brick:hasPoint bldg:{temperature setpoint} .
        bldg:{temperature sensor} rdf:type brick:Temperature_Sensor .
        bldg:{temperature setpoint} rdf:type brick:Temperature_Setpoint .
    -
      conditions:
        - |
          '{has_reheat}'
      data: |-
        bldg:{VAV name} rdf:type brick:RVAV .


The above example configuration file has two **operations**. The first **operation** is a 'data' operation. In a 'data' operation, new data is added to the graph.
In a dataset processed by a TableHandler, each operation is checked against each row of the input table.
In a basic 'data' operation, if all of the variables mentioned in the operation are present in the row being processed, the body of the **operation** is updated using the values from the row being processed, and the data is inserted into the graph.
The first **operation** above references the 'VAV_name', 'temperature sensor', and 'temperature setpoint' variables, and all of them are present in the first row, so the following data is inserted into the graph:

::

        bldg:A rdf:type brick:VAV ;
                        brick:hasPoint bldg:A_ts ;
                        brick:hasPoint bldg:A_sp .
        bldg:A_ts rdf:type brick:Temperature_Sensor .
        bldg:A_sp rdf:type brick:Temperature_Setpoint .

Because the second row has all of the variables as well, the first operation is used again with the second row of the input file and the following information is inserted into the graph:

::

        bldg:B rdf:type brick:VAV ;
                        brick:hasPoint bldg:B_ts ;
                        brick:hasPoint bldg:B_sp .
        bldg:B_ts rdf:type brick:Temperature_Sensor .
        bldg:B_sp rdf:type brick:Temperature_Setpoint .


The second **operation** in the file is a 'conditional' operation. A 'conditional' operation is much like a 'data' operation, and all of the variables specified in a 'conditional' operation must be present for the operation to be invoked, but a 'conditional' operation also includes an extra check to see if it should be used for a given row.
In this case, the 'conditional' operation says that the has_reheat variable must be **true** in order for the associated 'data' operation to be invoked.
In our example, the first row (for VAV 'A') under the column 'has_reheat' is listed as 'false' and so the 'data' operation does not fire.
The second row (for VAV 'B') the 'has_reheat' column is 'true' and the 'data' operation fires, inserting the following triple into the graph

::

        bldg:B a brick:RVAV .

The details of the 'conditional' syntax is detailed in the :ref:`TableHandler` section below.

Namespace and Prefix updates
----------------------------

Often, you would like to reuse a configuration file such as the 'template.yml' we used in our earlier examples, but you want to be able to customize them for a specific building or site.
Brickify allows you to substitute a new namespace and RDF prefix for the building and site by using the command line.
Brickify will replace the text from the template to be the new values on the command line.

.. code-block:: bash

                brickify sheet.tsv --output bldg.ttl --input-type tsv --config template.yml --building-prefix mybldg --building-namespace https://mysite.local/mybldg/#


Will produce in bldg.ttl:

::

    @prefix brick: <https://brickschema.org/schema/Brick#> .
    @prefix mybldg: <https://mysite.local/mybldg/#> .

    mybldg:A a brick:VAV ;
        brick:hasPoint mybldg:A_sp,
            mybldg:A_ts .



.. include:: handler.rst
.. include:: table_handler.rst
.. include:: haystack_handler.rst
