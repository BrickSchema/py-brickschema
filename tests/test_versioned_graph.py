from brickschema.persistent import VersionedGraphCollection
from brickschema.namespaces import BRICK, UNIT, A
from rdflib import Namespace, Literal, URIRef

def test_versioned_graph():
    g = VersionedGraphCollection("sqlite://")
    EX = Namespace("urn:ex#")
    g.bind("ex", EX)
    assert len(g) == 0
    with g.new_changeset("abc") as cs:
        cs.add((EX['a'], A, BRICK.Sensor))
    assert len(g) == 1
    with g.new_changeset("abc") as cs:
        cs.add((EX['b'], A, BRICK.Sensor))
    assert len(g) == 2
    g.undo()
    assert len(g) == 1
    g.redo()
    assert len(g) == 2