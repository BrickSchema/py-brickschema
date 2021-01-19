.. brickschema documentation master file, created by
   sphinx-quickstart on Mon Jan 27 12:41:13 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

BrickSchema Documentation
=======================================

The ``brickschema`` package makes it easy to get started with Brick and Python. Among the features it provides are:

- management and querying of Brick models
- simple OWL inference
- inference of Brick models from Haystack exports

.. code-block:: python

 # if your building's Brick model is stored in 'mybuilding.ttl'
 from brickschema import Graph
 # create a graph to hold the model, loading the latest Brick release
 bldg = Graph(load_brick_nightly=True)
 # load in the model from the file
 bldg.load_file('mybuilding.ttl')
 bldg.expand(profile="owlrl")

 # validate your Brick graph against built-in shapes (or add your own)
 valid, _, resultsText = bldg.validate()
 if not valid:
     print("Graph is not valid!")
     print(resultsText)

 # execute queries!
 res = bldg.query("""SELECT ?ahu ?vav WHERE {
                      ?ahu  a  brick:AHU .
                      ?vav  a  brick:VAV .
                      ?ahu  brick:feeds ?vav
                   }""")
 for row in res:
    print(f"AHU {row[0]} feeds VAV {row[1]}")


Installation
------------

The ``brickschema`` package requires Python >= 3.6. It can be installed with ``pip``:

.. code-block:: bash

   pip install brickschema

.. toctree::
   :maxdepth: 2

   quickstart
   orm
   validate
   brick_validate

   source/brickschema


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
