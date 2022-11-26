from brickschema.namespaces import BRICK, A
from rdflib import Namespace
from brickschema.persistent import PersistentGraph


def test_persistent_graph():
    pg = PersistentGraph("sqlite://")
    assert len(pg) == 0

    pg = PersistentGraph("sqlite://", load_brick=True)
    assert len(pg) > 0

    EX = Namespace("http://example.com/building#")

    pg.add((EX["a"], A, BRICK.Temperature_Sensor))
    pg.serialize("/tmp/out.ttl", format="turtle")
    pg.expand("shacl")
    assert (EX["a"], A, BRICK.Sensor) in pg

    res = pg.query("SELECT * WHERE { ?x a brick:Temperature_Sensor }")
    assert len(res) == 1

    pg2 = PersistentGraph("sqlite://", load_brick=False)
    pg2.add((EX["b"], A, BRICK.Temperature_Sensor))
    res = pg2.query("SELECT * WHERE { ?x a brick:Temperature_Sensor }")
    assert len(res) == 1

    pg += pg2
    res = pg.query("SELECT * WHERE { ?x a brick:Temperature_Sensor }")
    assert len(res) == 2
