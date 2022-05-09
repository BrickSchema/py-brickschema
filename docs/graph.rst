Managing Metadata in Graphs
===========================

Graphs are the primary unit of management for Brick models. `brickschema` provides two ways of managing graphs and the triples inside them:

- as a single bag of triples (:class:`~brickschema.graph.Graph`, a subclass of `rdflib.Graph`)
- as a union of individually addressable bags of triples (:class:`~brickschema.graph.GraphCollection`, a subclass of `rdflib.Dataset`)

Both :class:`~brickschema.graph.Graph` and :class:`~brickschema.graph.GraphCollection` posess the ability to import triples from a variety of sources --- online resources, local files, etc --- and perform reasoning/inference, validation and querying over those triples. However, :class:`~brickschema.graph.Graph` does not provide any addressable subdivision of the ingested triples; once those triples are loaded into the graph, they are all considered part of the same flat set.

:class:`~brickschema.graph.GraphCollection` introduces a new method, :func:`~brickschema.graph.GraphCollection.load_graph`, which imports triples from the provided source into its *own graph*. This graph is an instance of :class:`~brickschema.graph.Graph` and can be queried, reasoned, validated just like other graphs. The name of the graph is a URI given by any `owl:Ontology` definition inside the graph (which can be overridden). The encapsulating `GraphCollection` object can query the constituent graphs individually, or as a union.

The advantage of `GraphCollection` over `Graph` is that it makes it easier to upgrade individual graphs --- ontology definitions, building instances, etc --- separately.

.. code-block:: python

   from brickschema import GraphCollection
   from brickschema.namespaces import BRICK
   from rdflib import Namespace

    # Create a new graph collection
    gc = GraphCollection(load_brick=True)
    # the Brick ontology is loaded under its own URI
    # the other graph is the "default" graph which contains
    # reasoned and inferred triples
    assert URIRef(BRICK) in g.graph_names
    assert len(g.graph_names) == 2

    brick = gc.graph(URIRef(BRICK))
    # we can work with the Brick ontology graph independently
    equipment_classes = brick.query("""
        SELECT ?equipment_class
        WHERE { ?equipment_class rdf:type brick:EquipmentClass }""")

    # add a building graph with a sensor
    EX1 = Namespace("urn:ex1#")
    # referring to the graph implicitly creates it
    bldg = gc.graph(EX1)
    bldg.add((EX1["a"], A, BRICK["Sensor"]))

    # perform SHACL reasoning on the graph; reasoned triples
    # will be added to the default graph
    gc.expand("shacl")

    # now we can query the graph collection all together
    assert len(g.graph_names) == 3
    assert URIRef(EX1) in g.graph_names
    assert URIRef(BRICK) in g.graph_names
    res = gc.query("SELECT * WHERE { ?x a brick:Sensor }")
    assert len(res) == 1, "Should have 1 sensor from adding graph"

    # now we can replace the Brick ontology definition with a newer version
    gc.remove_graph(URIRef(BRICK))
    gc.load_graph("https://github.com/BrickSchema/Brick/releases/download/nightly/Brick.ttl", graph_name=BRICK)


Second Example
==============

.. code-block:: python

    from brickschema.graph import GraphCollection
    from brickschema.namespaces import BRICK, A
    from rdflib import URIRef, Namespace

    # in-memory graph
    g = GraphCollection()

    # load Brick ontology
    g.load_graph("https://sparql.gtf.fyi/ttl/Brick1.3rc1.ttl", format="turtle")

    # declare namespace for the entities in the "instance" model
    BLDG = Namespace("urn:building-instance/")

    # grab the graph for the building instance model so we can add triples to it
    bldg_graph = g.graph(URIRef(BLDG))

    # now we can add triples to the building
    bldg_graph.add((BLDG["my-building"], A, BRICK.Building))
    bldg_graph.add((BLDG["my-sensor"], A, BRICK.Zone_Air_Temperature_Sensor))

    # when we run queries, run them against the "collection"
    res = g.query("""SELECT * WHERE {
        ?sensor rdf:type/rdfs:subClassOf* brick:Temperature_Sensor
    }""")
    assert len(res) == 1

    # we can save the building graph separately
    bldg_graph = g.graph(URIRef(BLDG))
    bldg_graph.serialize("my-building.ttl", format="turtle")
