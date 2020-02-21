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


def test_validate_error():
    v = Validate()

    dataG = loadGraph('data/badBuilding.ttl')
    (conforms, results_graph, results_text) = v.validate(dataG)
    assert not conforms, 'expect constraint violations in badBuilding.ttl'
    printExtra(v)
    assert len(v.violationList()) == 5, 'unexpected # of violations'

def test_validate_no_error():
    v = Validate()

    dataG = loadGraph('data/goodBuilding.ttl')
    (conforms, results_graph, results_text) = v.validate(dataG)
    assert conforms, 'expect no constraint violations in goodBuilding.ttl'

def test_addShapeFile():
    v = Validate(attachOffender=False)
    v.addShapeFile(fullPath('data/extraShapes.ttl'))

    dataG = loadGraph('data/badBuilding.ttl')
    (conforms, results_graph, results_text) = v.validate(dataG)
    assert not conforms, 'expect constraint violations in badBuilding.ttl'
    print(results_text)
