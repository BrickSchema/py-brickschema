from brickschema import Graph, GraphCollection
from brickschema.namespaces import BRICK, UNIT, A
from rdflib import Namespace, Literal, URIRef


def test_specific_classes():
    g = Graph(load_brick=True)

    classlist = [BRICK.HVAC_Equipment, BRICK.Equipment, BRICK.Fan, BRICK.Discharge_Fan]
    specific = g.get_most_specific_class(classlist)
    assert specific == [BRICK.Discharge_Fan]

    classlist = [
        BRICK.HVAC_Equipment,
        BRICK.Equipment,
        BRICK.Fan,
        BRICK.Discharge_Fan,
        BRICK.Exhaust_Fan,
    ]
    specific = g.get_most_specific_class(classlist)
    assert specific == [BRICK.Discharge_Fan, BRICK.Exhaust_Fan]

    classlist = [BRICK.HVAC_Equipment, BRICK.Fan]
    specific = g.get_most_specific_class(classlist)
    assert specific == [BRICK.Fan]

    classlist = [BRICK.HVAC_Equipment, BRICK.Chiller, BRICK.Absorption_Chiller]
    specific = g.get_most_specific_class(classlist)
    assert specific == [BRICK.Absorption_Chiller]


def test_add_fancy():
    g = Graph()

    EX = Namespace("urn:ex#")
    g.bind("ex", EX)

    g.add(
        (EX.A, BRICK.area, [(BRICK.value, Literal(100)), (BRICK.hasUnit, UNIT["M3"])])
    )

    res = list(
        g.query(
            """SELECT ?area ?unit WHERE {
                            ?x brick:area/brick:value ?area .
                            ?x brick:area/brick:hasUnit ?unit
                        }"""
        )
    )
    assert len(res) == 1


def test_operator_overload():
    EX = Namespace("urn:ex#")

    g1 = Graph()
    g1.add((EX["a"], A, BRICK["Sensor"]))

    g2 = Graph()
    g2.add((EX["b"], A, BRICK["Sensor"]))

    g = g1 + g2

    g.expand("owlrl")

    res = g.query("SELECT * WHERE { ?x a brick:Sensor }")
    assert len(res) == 2, "Should have 2 sensors from adding graphs"


def test_collection():
    g = GraphCollection(load_brick=True)
    assert URIRef(BRICK) in g.graph_names
    assert len(g.graph_names) == 2

    EX1 = Namespace("urn:ex1#")
    bldg = g.graph(EX1)
    bldg.add((EX1["a"], A, BRICK["Sensor"]))

    assert len(g.graph_names) == 3
    assert URIRef(EX1) in g.graph_names
    assert URIRef(BRICK) in g.graph_names
    res = g.query("SELECT * WHERE { ?x a brick:Sensor }")
    assert len(res) == 1, "Should have 1 sensor from adding graph"

    EX2 = Namespace("urn:ex2#")
    bldg = g.graph(EX2)
    bldg.add((EX2["a"], A, BRICK["Sensor"]))

    assert len(g.graph_names) == 4
    assert URIRef(EX1) in g.graph_names
    assert URIRef(EX2) in g.graph_names
    assert URIRef(BRICK) in g.graph_names
    res = g.query("SELECT * WHERE { ?x a brick:Sensor }")
    assert len(res) == 2, "Should have 2 sensors from adding graph"

    # This needs more work!
    # # option 1: GraphCollection is the 'database' of multiple buildings
    # # - need to be able to pull a view of single building + Brick + other supporting ontologies
    # # - one copy of Brick
    # # - TODO: where do the 'reasoned' triples go? Can we direct some reasoned triples to the "original" graph?
    # # - TODO: need to have a r/w view of the graph
    # # - TODO: can we have the store support querying a subset of the graphs in a single Dataset/ConjunctiveGraph? RDFlib may be interested in this
    # # option 2: GraphCollection is 'database' of one building
    # # - no need to query a subset of the graphs
    # sg = g.subset_with([EX2, BRICK])
    # assert len(sg.graph_names) == 3, sg.graph_names
    # assert URIRef(EX1) not in sg.graph_names
    # assert URIRef(EX2) in sg.graph_names
    # assert URIRef(BRICK) in sg.graph_names
    # sg_ex2 = sg.graph(EX2)
    # sg_ex2.add((EX2["b"], A, BRICK["Sensor"]))
    # res = sg.query("SELECT * WHERE { ?x a brick:Sensor }")
    # assert len(res) == 2, "Should have 2 sensors in remaining graph (we added one)"

    # assert len(g.graph_names) == 4
    # assert URIRef(EX1) in g.graph_names
    # assert URIRef(EX2) in g.graph_names
    # assert URIRef(BRICK) in g.graph_names

    # res = g.query("SELECT * WHERE { ?x a brick:Sensor }")
    # assert len(res) == 3, "Should now have 3 sensors from adding graph"
