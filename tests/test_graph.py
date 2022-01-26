from brickschema import Graph, Collection
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
    g = Collection(load_brick=True)
    assert URIRef(BRICK) in g.graph_names
    assert len(g.graph_names) == 2

    EX = Namespace("urn:ex#")
    bldg = g.graph(EX)
    bldg.add((EX["a"], A, BRICK["Sensor"]))

    assert len(g.graph_names) == 3
    assert URIRef(EX) in g.graph_names
    assert URIRef(BRICK) in g.graph_names
