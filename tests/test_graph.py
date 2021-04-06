from brickschema import Graph
from brickschema.namespaces import BRICK, UNIT
from rdflib import Namespace, Literal


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
