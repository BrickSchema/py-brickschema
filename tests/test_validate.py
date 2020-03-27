from brickschema.validate import Validator
from rdflib import Graph
import pytest
import os, sys
import io
import pkgutil

def loadGraph(resource):
    data = pkgutil.get_data(__name__, resource).decode()
    g = Graph()
    g.parse(source=io.StringIO(data), format='turtle')
    return g


# NOTE: Assertions on number of violations is tighly coupled with 1.
# the default and extra (if any) shape files, 2. the data graph.
# Changes in Brick.ttl and pyshacl package, though less frequent
# can have impact, too.

def test_validate_error():
    dataG = loadGraph('data/badBuilding.ttl')
    v = Validator()
    result = v.validate(dataG)
    assert not result.conforms, 'expect constraint violations in badBuilding.ttl'
    assert len(result.violationGraphs) == 5, 'unexpected # of violations'


def test_validate_ok():
    dataG = loadGraph('data/goodBuilding.ttl')
    v = Validator()
    result = v.validate(dataG)
    assert result.conforms, 'expect no constraint violations in goodBuilding.ttl'
    assert len(result.violationGraphs) == 0, 'unexpected # of violations'


def test_useOnlyExtraShapeGraph():
    dataG = loadGraph('data/badBuilding.ttl')
    shapeG = loadGraph('data/extraShapes.ttl')
    v = Validator(useDefaultShapes=False)  # do not use default shapes
    result = v.validate(dataG, shacl_graphs=[shapeG])
    assert not result.conforms, 'expect constraint violations in badBuilding.ttl'
    assert len(result.violationGraphs) == 5, 'unexpected # of violations'


def test_useExtraShapeGraph():
    dataG = loadGraph('data/badBuilding.ttl')
    shapeG = loadGraph('data/extraShapes.ttl')
    v = Validator()
    # (conforms, violationList, results_text) = v.validate(dataG,
    result = v.validate(dataG, shacl_graphs=[shapeG])
    assert not result.conforms, 'expect constraint violations in badBuilding.ttl'
    assert len(result.violationGraphs) == 10, 'unexpected # of violations'
    print(result.textOutput)


def test_useExtraOntGraphShapeGraph():
    dataG = loadGraph('data/badBuilding.ttl')
    ontG1 = loadGraph('data/extraOntology1.ttl')
    ontG2 = loadGraph('data/extraOntology2.ttl')
    v = Validator()

    # Without extra shapes for the extra ontology files
    # we shouldn't see more violations
    result = v.validate(dataG, ont_graphs=[ontG1])
    assert not result.conforms, 'expect constraint violations in badBuilding.ttl'
    assert len(result.violationGraphs) == 5, 'unexpected # of violations'

    result = v.validate(dataG, ont_graphs=[ontG1, ontG2])
    assert not result.conforms, 'expect constraint violations in badBuilding.ttl'
    assert len(result.violationGraphs) == 5, 'unexpected # of violations'

    shapeG1 = loadGraph('data/extraShapes.ttl')
    shapeG2 = loadGraph('data/extraShapesWithExtraOnt.ttl')

    # Add one extraShape file
    result = v.validate(dataG, ont_graphs=[ontG1, ontG2], shacl_graphs=[shapeG1])
    assert not result.conforms, 'expect constraint violations in badBuilding.ttl'
    assert len(result.violationGraphs) == 10, 'unexpected # of violations'

    # Add second extraShape file that goes with the extra ontology
    result = v.validate(dataG, ont_graphs=[ontG1, ontG2],
                        shacl_graphs=[shapeG1, shapeG2])
    assert not result.conforms, 'expect constraint violations in badBuilding.ttl'
    assert len(result.violationGraphs) == 12, 'unexpected # of violations'
