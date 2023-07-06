Persistent and Versioned Graphs
===============================

.. tip::
   To use this feature, install brickschema with the "persistence" feature: `pip install brickschema[persistence]` or `pip install brickschema[all]`

The default :class:`~brickschema.graph.Graph` and :class:`~brickschema.graph.GraphCollection` classes implement in-memory stores that only track the latest version of the graph. Often, it is helpful to not just keep track of the history of how the graph has changed, but also to persist that graph so that it lasts beyond the lifetime of a program.

:class:`~brickschema.persistent.PersistentGraph` is a subclass of :class:`~brickschema.graph.Graph` that implements a persistent store backed by `RDFlib-SQLAlchemy <https://github.com/RDFLib/rdflib-sqlalchemy>`_. The contents of the graph are stored in a SQL database given by the connection string passed to the constructor:

.. code-block:: python

   from brickschema.persistent import PersistentGraph
   from brickschema.namespaces import RDF, BRICK
   # stores the graph in a local SQlite database
   g = PersistentGraph("sqlite:///mygraph.sqlite", load_brick_nightly=True)
   # PersistentGraph supports the full API of the normal transient Graph class
   g.add((URIRef("http://example.org/mybuilding/ts1"), RDF.type, BRICK.Temperature_Sensor))
   g.expand("shacl")

:class:`~brickschema.persistent.VersionedGraphCollection` is another option which combines the persistence of `PersistentGraph`, the functionality of the base :class:`~brickschema.graph.Graph` class, and a transactional API for manipulating the graph.  The versioned graph supports the following helpful features:

- undo/redo functionality for "rolling back" changes to the graph
- checkout a specific version of the graph at a point in time
- pre-commit and post-commit hooks for performing actions on the graph before and after the graph is committed

.. code-block:: python

    from brickschema.persistent import VersionedGraphCollection
    from brickschema.namespaces import RDF, BRICK

    g = VersionedGraphCollection("sqlite://") # in-memory

    # can add precommit and postcommit hooks to implement desired functionality
    # precommit hooks are run *before* the transaction is committed but *after* all of
    # the changes have been made to the graph.
    # postcommit hooks are run *after* the transaction is committed.
    def validate(graph):
        print("Validating graph")
        valid, _, report = graph.validate()
        assert valid, report
    g.add_postcommit_hook(validate)

    with g.new_changeset("my-building") as cs:
        # 'cs' is a rdflib.Graph that supports queries -- updates on it
        # are buffered in the transaction and cannot be queried until
        # the transaction is committed (at the end of the context block)
        cs.add((BLDG.vav1, A, BRICK.VAV))
        cs.add((BLDG.vav1, BRICK.feeds, BLDG.zone1))
        cs.add((BLDG.zone1, A, BRICK.HVAC_Zone))
        cs.add((BLDG.zone1, BRICK.hasPart, BLDG.room1))
    print(f"Have {len(g)} triples")

    snapshot = g.latest_version['timestamp']

    with g.new_changeset("my-building") as cs:
        cs.remove((BLDG.zone1, A, BRICK.HVAC_Zone))
        cs.add((BLDG.zone1, A, BRICK.Temperature_Sensor))
    print(f"Have {len(g)} triples")

    # query the graph 3 seconds ago (before the latest commit)
    print("Loop through versions")
    for v in g.versions():
        print(f"{v.timestamp} {v.id} {v.graph}")
    g = g.graph_at(timestamp=snapshot)
    print(f"Have {len(g)} triples")
    res = g.query("SELECT * WHERE { ?x a brick:Temperature_Sensor }")
    num_results = len(list(res))
    assert num_results == 0, num_results # should be 0 because sensor not added yet

Furthermore, the :class:`~brickschema.persistent.VersionedGraphCollection` also acts like the :class:`~brickschema.graph.GraphCollection` where metadata can be managed.

.. code-block:: python

    from brickschema.persistent import VersionedGraphCollection
    from brickschema.namespaces import BRICK, A
    from rdflib import Namespace

    vgc = VersionedGraphCollection(uri="sqlite://")

    PROJECT = Namespace("https://example.org/my-project#")

    # load Brick ontology
    with vgc.new_changeset("Brick") as cs:
        cs.load_file("https://sparql.gtf.fyi/ttl/Brick1.3rc1.ttl")

    # load other changes
    with vgc.new_changeset("My-Project") as cs:
        cs.add((PROJECT["my-sensor"], A, BRICK.Zone_Air_Temperature_Sensor))

    res = vgc.query("""SELECT * WHERE {
        ?sensor rdf:type/rdfs:subClassOf* brick:Temperature_Sensor
    }""")

    # the query on the entire graph collection should find the sensor
    assert len(res) == 1

    g = vgc.graph_at(graph="My-Project")
    res = g.query("""SELECT * WHERE {
        ?sensor rdf:type/rdfs:subClassOf* brick:Temperature_Sensor
    }""")

    # the same query but just on the graph "My-Project" should not have found any results
    assert len(res) == 0

    # serialize the graph without the Brick ontology
    g.serialize("JustTheProject.ttl")