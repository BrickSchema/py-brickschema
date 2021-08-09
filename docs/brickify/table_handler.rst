.. _TableHandler:

Table Handler
-------------

The Table Handler processes input datasets row by row. The Table Halder is invoked with the ``--input-format`` is set to TSV, CSV, or table.

We have already seen parts of the TableHandler. Let's recall the config file we used earlier:

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

Internally, Brickify converts each 'data' operation to a SPARQL insert operation.
If the 'data' operation fires, because all of the variables referenced in the operation are present in that row, Brickify executes a SPARQL `INSERT DATA` statement.
This is the SPARQL generated from the first row:

:: 

  INSERT DATA { bldg:A rdf:type brick:VAV ;
                  brick:hasPoint bldg:A_ts ;
                  brick:hasPoint bldg:A_sp .
  bldg:A_ts rdf:type brick:Temperature_Sensor .
  bldg:A_sp rdf:type brick:Temperature_Setpoint . }


Conditional syntax
^^^^^^^^^^^^^^^^^^

Brickify implements conditions by taking the condition and feeding it to Python's ``eval`` method.
If the condition evaluates to True, the data method fires, and if the method evaluates to False, the condition fails.
Consider this input file:

+--------+------------------+--------------------+----------+------+
|VAV name|temperature sensor|temperature setpoint|has_reheat|thresh|
+========+==================+====================+==========+======+
|A       | A_ts             | A_sp               | false    |  16  |
+--------+------------------+--------------------+----------+------+
|B       | B_ts             | B_sp               | true     |  12  |
+--------+------------------+--------------------+----------+------+

One of the things that can be a little tricky with the 'condition' operation is ensuring that the types are correct when crossing from CSV/TSV and into Python, especially for strings and Booleans.

For example, this expression will fire for row A but not row B:

:: 

    conditions:
      - |
        {thresh} > 14

Internally, this is converted to the string ``'16 > 14'`` and then passed to the Python ``eval()`` method, which returns ``True``. 

A trickier version - which looks like our earlier example but is *slightly* different: 

:: 

    conditions:
      - |
        {has_reheat}

In our example, this will fail! (Spoiler: we took away the quotes from our earlier example)

The issue is that the has_reheat column is pulled in as a string, but is not valid Python because the capitalization of 'true' and 'false' is incorrect in the TSV file.

One way to fix this is to correct the data:

+--------+------------------+--------------------+----------+------+
|VAV name|temperature sensor|temperature setpoint|has_reheat|thresh|
+========+==================+====================+==========+======+
|A       | A_ts             | A_sp               | False    |  16  |
+--------+------------------+--------------------+----------+------+
|B       | B_ts             | B_sp               | True     |  12  |
+--------+------------------+--------------------+----------+------+

This will match the condition because we have capitalized True and False. 
Unfortunately, changing the data in the input CSV you are processing may not always be possible. 

As a compromise, to support this common use case where the input strings look like booleans but are not quite formatted right, Brickify expects Boolean conditions to be handled first as quoted strings:
:: 

    conditions:
      - |
        '{has_reheat}'

Brickify will pass that code to the Python ``eval()`` method, which will return ``'true'``, which is type ``str`` (and not ``True`` which is type ``Boolean``) 
However, as a special case, Brickify converts the following strings to booleans: 
["TRUE", "true", "True", "on", "ON"] all become ``True``, and ["FALSE", "false", "False", "off", "OFF"] are converted to ``False``.

An important note: the replacement text is not carried out on the substrings. At present, this will **not** work:

:: 

    conditions:
      - |
        {thresh} > 12 and '{has_reheat}'

Template Operation
^^^^^^^^^^^^^^^^^^

The TableHandler supports an additional operation, similar to the 'data' operation, that uses Jinja2 templates.
This introduces a new section into the configuration file for defining Jinja2 templates, the 'macros' section, which is added at the top level of the configuration file.

The new **operation** is a 'template' operation, which can reference the Jinja2 macros from the top-level macro section. 
Much like 'data' operations, a 'template' operation only fires if all of the referenced variables are present in the row being processed.

Consider this input table:

+--------+------------------+--------------------+----------+-------+---------+
|VAV name|temperature sensor|temperature setpoint|has_reheat|sensors|setpoints|
+========+==================+====================+==========+=======+=========+
|A       | A_ts             | A_sp               | False    |  4    |    3    |
+--------+------------------+--------------------+----------+-------+---------+
|B       | B_ts             | B_sp               | True     |  5    |    3    |
+--------+------------------+--------------------+----------+-------+---------+

The example config file below defines two template operations. 
The template uses a 'for' loop to create multiple sensors and setpoints, following a naming pattern provided to macro as arguments.
The numbers of sensors and setpoints come from the input CSV file. 

.. code-block:: yaml

  ---
  namespace_prefixes:
    brick: "https://brickschema.org/schema/Brick#"
  operations:
    -
      data: |-
        bldg:{VAV name}_0 rdf:type brick:VAV .
    -
      conditions:
        - |
          '{has_reheat}'
      data: |-
        bldg:{VAV name} rdf:type brick:RVAV .

    - template: |-
        {{ num_triples(value['VAV name'], "brick:hasPoint", value['temperature sensor'], value['sensors'], "brick:Temperature_Sensor") }}

    - template: |-
        {{ num_triples(value['VAV name'], "brick:hasPoint", value['temperature setpoint'], value['setpoints'], "brick:Temperature_Setpoint") }}

  macros:
    - |-
      {% macro num_triples(subject, predicate, name, num, type) %}
          {% for i in range(num) %}
            bldg:{{ name }}_{{ i }} a {{ type }} .
            bldg:{{ subject }} {{ predicate }} bldg:{{ name }}_{{ i }} .
          {% endfor %}
      {% endmacro %}

And the output, just for the building B row:

::

      bldg:B_ts_0 a brick:Temperature_Sensor .
      bldg:B brick:hasPoint bldg:B_ts_0 .
    
      bldg:B_ts_1 a brick:Temperature_Sensor .
      bldg:B brick:hasPoint bldg:B_ts_1 .
    
      bldg:B_ts_2 a brick:Temperature_Sensor .
      bldg:B brick:hasPoint bldg:B_ts_2 .
    
      bldg:B_ts_3 a brick:Temperature_Sensor .
      bldg:B brick:hasPoint bldg:B_ts_3 .
    
      bldg:B_ts_4 a brick:Temperature_Sensor .
      bldg:B brick:hasPoint bldg:B_ts_4 .

      bldg:B_sp_0 a brick:Temperature_Setpoint .
      bldg:B brick:hasPoint bldg:B_sp_0 .
    
      bldg:B_sp_1 a brick:Temperature_Setpoint .
      bldg:B brick:hasPoint bldg:B_sp_1 .
    
      bldg:B_sp_2 a brick:Temperature_Setpoint .
      bldg:B brick:hasPoint bldg:B_sp_2 .

