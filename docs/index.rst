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
 from brickschema.inference import BrickInferenceSession
 from brickschema.graph import Graph
 # create a graph to hold the model
 bldg = Graph()
 # load in the model from the file (Brick is loaded in automatically)
 bldg.load_file('mybuilding.ttl')
 # "fill in" all the implied information
 sess = BrickInferenceSession()
 bldg = sess.expand(bldg)

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
