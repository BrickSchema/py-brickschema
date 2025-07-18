import brickschema
from ontoenv import OntoEnv, Config
from rdflib import Graph, OWL
import pytest
import os
import sys
import io
import pkgutil


def loadGraph(resource) -> brickschema.Graph:
    data = pkgutil.get_data(__name__, resource).decode()
    g = brickschema.Graph()
    g.parse(source=io.StringIO(data), format="turtle")
    return g


# NOTE: Assertions on number of violations is tighly coupled with 1.
# the default and extra (if any) shape files, 2. the data graph.
# Changes in Brick.ttl and pyshacl package, though less frequent
# can have impact, too.


def test_validate_bad(brick_with_imports):
    dataG = loadGraph("data/badBuilding.ttl")
    # remove imports from the Brick graph
    conforms, _, _ = dataG.validate(shape_graphs=[brick_with_imports], engine="topquadrant")
    assert not conforms, "expect constraint violations in badBuilding.ttl"


def test_validate_ok(brick_with_imports):
    dataG = loadGraph("data/goodBuilding.ttl")
    conforms, _, report_str = dataG.validate(shape_graphs=[brick_with_imports], engine="topquadrant")
    assert conforms, f"expect no constraint violations in goodBuilding.ttl {report_str}"


def test_useOnlyExtraShapeGraph():
    dataG = loadGraph("data/badBuilding.ttl")
    shapeG = loadGraph("data/extraShapes.ttl")
    brickG = brickschema.Graph(load_brick=True)
    brickG.remove((None, OWL.imports, None))
    conforms, _, _ = dataG.validate(shape_graphs=[shapeG, brickG], engine="topquadrant")
    assert not conforms, "expect constraint violations in badBuilding.ttl"


def test_useExtraShapeGraph():
    dataG = loadGraph("data/badBuilding.ttl")
    shapeG = loadGraph("data/extraShapes.ttl")
    brickG = brickschema.Graph(load_brick=True)
    brickG.remove((None, OWL.imports, None))
    conforms, _, _ = dataG.validate(shape_graphs=[shapeG, brickG], engine="topquadrant")
    assert not conforms, "expect constraint violations in badBuilding.ttl"


def test_useExtraOntGraphShapeGraph():
    dataG = loadGraph("data/badBuilding.ttl")
    ontG1 = loadGraph("data/extraOntology1.ttl")
    ontG2 = loadGraph("data/extraOntology2.ttl")
    brickG = brickschema.Graph(load_brick=True)
    brickG.remove((None, OWL.imports, None))

    # Without extra shapes for the extra ontology files
    # we shouldn't see more violations
    conforms, _, _ = dataG.validate(shape_graphs=[ontG1, brickG], engine="topquadrant")
    assert not conforms, "expect constraint violations in badBuilding.ttl"
    # assert len(result.violationGraphs) == 4, "unexpected # of violations"

    conforms, _, _ = dataG.validate(shape_graphs=[ontG1, ontG2, brickG], engine="topquadrant")
    assert not conforms, "expect constraint violations in badBuilding.ttl"
    # assert len(result.violationGraphs) == 4, "unexpected # of violations"

    shapeG1 = loadGraph("data/extraShapes.ttl")
    shapeG2 = loadGraph("data/extraShapesWithExtraOnt.ttl")

    # Add one extraShape file
    # result = v.validate(dataG, ont_graphs=[ontG1, ontG2], shacl_graphs=[shapeG1])
    conforms, _, _ = dataG.validate(shape_graphs=[shapeG1, ontG1, ontG2, brickG], engine="topquadrant")
    assert not conforms, "expect constraint violations in badBuilding.ttl"
    # assert len(result.violationGraphs) == 9, "unexpected # of violations"

    # Add second extraShape file that goes with the extra ontology
    # result = v.validate(
    #    dataG, ont_graphs=[ontG1, ontG2], shacl_graphs=[shapeG1, shapeG2]
    # )
    conforms, _, _ = dataG.validate(shape_graphs=[shapeG1, shapeG2, ontG1, ontG2, brickG], engine="topquadrant")
    assert not conforms, "expect constraint violations in badBuilding.ttl"
    # assert len(result.violationGraphs) == 11, "unexpected # of violations"
