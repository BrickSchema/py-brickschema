from brickschema import Graph
from brickschema.namespaces import BRICK


def test_specific_classes():
    g = Graph(load_brick=True)

    classlist = [BRICK.HVAC, BRICK.Equipment, BRICK.Fan, BRICK.Discharge_Fan]
    specific = g.get_most_specific_class(classlist)
    assert specific == [BRICK.Discharge_Fan]

    classlist = [
        BRICK.HVAC,
        BRICK.Equipment,
        BRICK.Fan,
        BRICK.Discharge_Fan,
        BRICK.Exhaust_Fan,
    ]
    specific = g.get_most_specific_class(classlist)
    assert specific == [BRICK.Discharge_Fan, BRICK.Exhaust_Fan]
