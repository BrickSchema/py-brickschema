import brickschema
from brickschema.validate import Validator
from rdflib import Graph
import pytest
import os
import sys
import io
import pkgutil


def loadGraph(resource):
    data = pkgutil.get_data(__name__, resource).decode()
    g = Graph()
    g.parse(source=io.StringIO(data), format="turtle")
    return g


# NOTE: Assertions on number of violations is tighly coupled with 1.
# the default and extra (if any) shape files, 2. the data graph.
# Changes in Brick.ttl and pyshacl package, though less frequent
# can have impact, too.


def test_validate_bad():
    dataG = loadGraph("data/badBuilding.ttl")
    g = brickschema.Graph(load_brick=True)
    g += dataG
    conforms, _, _ = g.validate()
    assert not conforms


def test_validate_ok():
    dataG = loadGraph("data/goodBuilding.ttl")
    g = brickschema.Graph(load_brick=True)
    g += dataG
    conforms, _, report_str = g.validate()
    assert conforms, f"expect no constraint violations in goodBuilding.ttl {report_str}"


def test_useOnlyExtraShapeGraph():
    dataG = loadGraph("data/badBuilding.ttl")
    shapeG = loadGraph("data/extraShapes.ttl")
    g = brickschema.Graph(load_brick=True)
    g += dataG
    conforms, _, _ = g.validate(shape_graphs=[shapeG])
    assert not conforms, "expect constraint violations in badBuilding.ttl"


def test_useExtraShapeGraph():
    dataG = loadGraph("data/badBuilding.ttl")
    shapeG = loadGraph("data/extraShapes.ttl")
    g = brickschema.Graph()
    g += dataG
    conforms, _, _ = g.validate(shape_graphs=[shapeG])
    assert not conforms, "expect constraint violations in badBuilding.ttl"


def test_useExtraOntGraphShapeGraph():
    dataG = loadGraph("data/badBuilding.ttl")
    ontG1 = loadGraph("data/extraOntology1.ttl")
    ontG2 = loadGraph("data/extraOntology2.ttl")
    g = brickschema.Graph(load_brick=True)
    g += dataG

    # Without extra shapes for the extra ontology files
    # we shouldn't see more violations
    conforms, _, _ = g.validate(shape_graphs=[ontG1])
    assert not conforms, "expect constraint violations in badBuilding.ttl"
    # assert len(result.violationGraphs) == 4, "unexpected # of violations"

    conforms, _, _ = g.validate(shape_graphs=[ontG1, ontG2])
    assert not conforms, "expect constraint violations in badBuilding.ttl"
    # assert len(result.violationGraphs) == 4, "unexpected # of violations"

    shapeG1 = loadGraph("data/extraShapes.ttl")
    shapeG2 = loadGraph("data/extraShapesWithExtraOnt.ttl")

    # Add one extraShape file
    # result = v.validate(dataG, ont_graphs=[ontG1, ontG2], shacl_graphs=[shapeG1])
    conforms, _, _ = g.validate(shape_graphs=[shapeG1, ontG1, ontG2])
    assert not conforms, "expect constraint violations in badBuilding.ttl"
    # assert len(result.violationGraphs) == 9, "unexpected # of violations"

    # Add second extraShape file that goes with the extra ontology
    # result = v.validate(
    #    dataG, ont_graphs=[ontG1, ontG2], shacl_graphs=[shapeG1, shapeG2]
    # )
    conforms, _, _ = g.validate(shape_graphs=[shapeG1, shapeG2, ontG1, ontG2])
    assert not conforms, "expect constraint violations in badBuilding.ttl"
    # assert len(result.violationGraphs) == 11, "unexpected # of violations"
