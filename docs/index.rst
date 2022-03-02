.. brickschema documentation master file, created by
   sphinx-quickstart on Mon Jan 27 12:41:13 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

BrickSchema Documentation
=======================================

The ``brickschema`` package makes it easy to get started with Brick and Python. Among the features it provides are:

- management and querying of Brick models
- simple OWL-RL, SHACL and other inference
- Haystack and VBIS integration:
    - convert Haystack models to Brick
    - add VBIS tags to a Brick model, or get Brick types from VBIS tags

.. code-block:: python

  import brickschema

  # creates a new rdflib.Graph with a recent version of the Brick ontology
  # preloaded.
  g = brickschema.Graph(load_brick=True)
  # OR use the absolute latest Brick:
  # g = brickschema.Graph(load_brick_nightly=True)
  # OR create from an existing model
  # g = brickschema.Graph(load_brick=True).from_haystack(...)

  # load in data files from your file system
  g.load_file("mbuilding.ttl")
  # ...or by URL (using rdflib)
  g.parse("https://brickschema.org/ttl/soda_brick.ttl", format="ttl")

  # perform reasoning on the graph (edits in-place)
  g.expand(profile="shacl")

  # validate your Brick graph against built-in shapes (or add your own)
  valid, _, resultsText = g.validate()
  if not valid:
      print("Graph is not valid!")
      print(resultsText)

  # perform SPARQL queries on the graph
  res = g.query("""SELECT ?afs ?afsp ?vav WHERE  {
      ?afs    a       brick:Air_Flow_Sensor .
      ?afsp   a       brick:Air_Flow_Setpoint .
      ?afs    brick:isPointOf ?vav .
      ?afsp   brick:isPointOf ?vav .
      ?vav    a   brick:VAV
  }""")
  for row in res:
      print(row)

  # start a blocking web server with an interface for performing
  # reasoning + querying functions
  g.serve("localhost:8080")
  # now visit in http://localhost:8080


Installation
------------

The ``brickschema`` package requires Python >= 3.7. It can be installed with ``pip``:

.. code-block:: bash

   pip install brickschema

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2

   quickstart
   graph
   persistence
   inference
   validate
   extensions
   orm
   brick_validate
   merging
   brickify/index.rst

   source/brickschema


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
