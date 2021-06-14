Inference
=========


``brickschema`` makes it easier to employ reasoning on your graphs. Simply call the ``expand`` method on the Graph object with one of the following profiles:

- ``"rdfs"``: RDFS reasoning
- ``"owlrl"``: OWL-RL reasoning (using 1 of 3 implementations below)
- ``"vbis"``: add VBIS tags to Brick entities
- ``"shacl"``: perform advanced SHACL reasoning

By default, ``expand`` will *simplify* the graph. Simplification is the process by which axiomatic, redundant or other "stray" triples are removed from the graph that may be added by a reasoner. This includes items like the following:

- triples that assert an entity to be an instance of ``owl:Thing`` or ``owl:Nothing``
- triples that assert an entity to be a blank node
- triples that assert an entity to be the same as itself

To turn simplification off, simply add ``simplify=False`` when calling ``expand``.

.. code-block:: python

  from brickschema import Graph

  g = Graph(load_brick=True)
  g.load_file("test.ttl")
  g.expand(profile="owlrl")
  print(f"Inferred graph has {len(g)} triples")


Brickschema also supports inference "schedules", where different inference regimes can be applied to a graph one after another. Specify a schedule by using ``+`` to join the profiles in the call to ``expand``.

.. code-block:: python

  from brickschema import Graph

  g = Graph(load_brick=True)
  g.load_file("test.ttl")
  # apply owlrl, shacl, vbis, then shacl again
  g.expand(profile="owlrl+shacl+vbis+shacl")
  print(f"Inferred graph has {len(g)} triples")


The package will automatically use the fastest available reasoning implementation for your system:

- ``reasonable`` (fastest, Linux-only for now): ``pip install brickschema[reasonable]``
- ``Allegro`` (next-fastest, requires Docker): ``pip install brickschema[allegro]``
- OWLRL (default, native Python implementation): ``pip install brickschema``

To use a specific reasoner, specify ``"reasonable"``, ``"allegrograph"`` or ``"owlrl"`` as the value for the ``backend`` argument to ``graph.expand``.
