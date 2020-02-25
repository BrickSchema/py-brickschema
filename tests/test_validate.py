from brickschema.validate import Validate, ResultsSerialize
from brickschema.namespaces import RDF, RDFS, BRICK, TAG, OWL
from rdflib import Namespace, BNode, Graph
import pytest
import os, sys
import io
import pkgutil

def fullPath(resource):
    return os.path.join(os.path.dirname(sys.modules[__name__].__file__), resource)

def loadGraph(resource):
    data = pkgutil.get_data(__name__, resource).decode()
    g = Graph()
    g.parse(source=io.StringIO(data), format='turtle')
    return g

def printExtra(v):
    ResultsSerialize(v.violationList(),
                     v.accumulatedNamespaces(),
                     sys.stdout).appendToOutput()

# NOTE: Assertions on number of violations is tighly coupled with 1.
# the default and extra (if any) shape files, 2. the data graph.
# Changes in Brick.ttl and pyshacl package, though less frequent
# can have impact, too.

def test_validate_error():
    dataG = loadGraph('data/badBuilding.ttl')
    v = Validate()
    (conforms, results_graph, results_text) = v.validate(dataG)
    assert not conforms, 'expect constraint violations in badBuilding.ttl'
    assert len(v.violationList()) == 5, 'unexpected # of violations'

def test_validate_ok():
    dataG = loadGraph('data/goodBuilding.ttl')
    v = Validate()
    (conforms, results_graph, results_text) = v.validate(dataG)
    assert conforms, 'expect no constraint violations in goodBuilding.ttl'

def test_useExtraShapeFileONLY():
    dataG = loadGraph('data/badBuilding.ttl')
    v = Validate(useDefaultShapes=False)  # do not use default shapes
    v.addShapeFile(fullPath('data/extraShapes.ttl'))
    (conforms, results_graph, results_text) = v.validate(dataG)
    assert not conforms, 'expect constraint violations in badBuilding.ttl'
    assert len(v.violationList()) == 4, 'unexpected # of violations'

def test_useExtraShapeFile():
    dataG = loadGraph('data/badBuilding.ttl')
    v = Validate()
    v.addShapeFile(fullPath('data/extraShapes.ttl'))
    (conforms, results_graph, results_text) = v.validate(dataG)
    assert not conforms, 'expect constraint violations in badBuilding.ttl'
    printExtra(v)
    assert len(v.violationList()) == 9, 'unexpected # of violations'

def test_useExtraShapeGraph():
    dataG = loadGraph('data/badBuilding.ttl')
    v = Validate()
    shapeG = loadGraph('data/extraShapes.ttl')
    v.addShapeGraph(shapeG)
    (conforms, results_graph, results_text) = v.validate(dataG)
    assert not conforms, 'expect constraint violations in badBuilding.ttl'
    assert len(v.violationList()) == 9, 'unexpected # of violations'
