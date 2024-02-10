import pytest
from brickschema.inference import (
    TagInferenceSession,
    HaystackInferenceSession,
    VBISTagInferenceSession,
)
from brickschema.namespaces import RDF, RDFS, BRICK, TAG, OWL
from brickschema.graph import Graph
from rdflib import Namespace, BNode
import io
import json
import pkgutil


def filter_bnodes(input_res):
    res = []
    for row in input_res:
        row = tuple(filter(lambda x: not isinstance(x, BNode), row))
        res.append(row)
    return list(filter(lambda x: len(x) > 0, res))


def test_tagset_inference():

    g = Graph(load_brick=False)
    g.load_extension("shacl_tag_inference")
    data = pkgutil.get_data(__name__, "data/tags.ttl").decode()
    g.load_file(source=io.StringIO(data))
    g.expand(profile="shacl")

    afs1 = g.query("SELECT ?x WHERE { ?x rdf:type brick:Air_Flow_Sensor }")
    assert len(afs1) == 1
    afsp1 = g.query("SELECT ?x WHERE { ?x rdf:type brick:Air_Flow_Setpoint }")
    assert len(afsp1) == 1
    mafs1 = g.query("SELECT ?x WHERE { ?x rdf:type brick:Max_Air_Flow_Setpoint_Limit }")
    assert len(mafs1) == 1


def test_lookup_tagset():
    session = TagInferenceSession(approximate=False)
    assert session is not None

    tagsets = session.lookup_tagset(["AHU", "Equipment"])
    assert tagsets[0][0] == set(["AHU"])

    tagsets = session.lookup_tagset(["Air", "Flow", "Sensor", "Point"])
    assert tagsets[0][0] == set(["Air_Flow_Sensor"])

    tagsets = session.lookup_tagset(["Air", "Flow", "Sensor", "Equipment"])
    assert len(tagsets) == 0

    tagsets = session.lookup_tagset(["Air", "Flow", "Setpoint", "Point"])
    assert tagsets[0][0] == set(["Air_Flow_Setpoint"])

    tagsets = session.lookup_tagset(
        ["Air", "Flow", "Setpoint", "Limit", "Parameter", "Point"]
    )
    assert tagsets[0][0] == set(["Air_Flow_Setpoint_Limit"])

    tagsets = session.lookup_tagset(
        ["Max", "Air", "Flow", "Setpoint", "Limit", "Parameter", "Point"]
    )
    assert tagsets[0][0] == set(["Max_Air_Flow_Setpoint_Limit"])


def test_most_likely_tagsets():
    session = TagInferenceSession(approximate=True)
    assert session is not None

    tagset1 = ["AHU", "Equipment"]
    inferred, leftover = session.most_likely_tagsets(tagset1)
    assert inferred == ["AHU"]
    assert len(leftover) == 0

    tagset2 = ["Air", "Flow", "Sensor"]
    inferred, leftover = session.most_likely_tagsets(tagset2)
    assert inferred == ["Air_Flow_Sensor"]
    assert len(leftover) == 0

    tagset3 = ["Air", "Flow", "Sensor", "Equipment"]
    inferred, leftover = session.most_likely_tagsets(tagset3)
    assert inferred == ["Air_Flow_Sensor"]
    assert len(leftover) == 1

    tagset4 = ["Air", "Flow", "Setpoint"]
    inferred, leftover = session.most_likely_tagsets(tagset4, num=1)
    assert inferred == ["Air_Flow_Setpoint"]
    assert len(leftover) == 0

    tagset5 = ["Air", "Flow", "Setpoint", "Limit"]
    inferred, leftover = session.most_likely_tagsets(tagset5, num=1)
    assert inferred == ["Air_Flow_Setpoint_Limit"]
    assert len(leftover) == 0

    tagset6 = ["Max", "Air", "Flow", "Setpoint", "Limit"]
    inferred, leftover = session.most_likely_tagsets(tagset6, num=1)
    assert inferred == ["Max_Air_Flow_Setpoint_Limit"]
    assert len(leftover) == 0


def test_brick_inference():
    g = Graph(load_brick=True)
    g.load_extension("shacl_tag_inference")

    data = pkgutil.get_data(__name__, "data/brick_inference_test.ttl").decode()
    g.load_file(source=io.StringIO(data))

    g.expand(profile="shacl", backend="pyshacl")

    r = g.query("SELECT ?x WHERE { ?x rdf:type brick:Air_Temperature_Sensor }")
    urls = set([str(row[0]) for row in r])
    real_sensors = set(
        [
            "http://example.com/mybuilding#sensor1",
            "http://example.com/mybuilding#sensor2",
            "http://example.com/mybuilding#sensor3",
        ]
    )
    assert urls == real_sensors


@pytest.mark.skip(
    "Haystack inference is currently broken. See https://github.com/gtfierro/Brick-Haystack-harmonization"
)
def test_haystack_inference():
    data = pkgutil.get_data(__name__, "data/carytown.json").decode()
    raw_model = json.loads(data)
    brick_model = Graph(load_brick=True).from_haystack(
        "http://example.org/carytown", raw_model
    )
    points = brick_model.query(
        """SELECT ?p WHERE {
        ?p rdf:type/rdfs:subClassOf* brick:Point
    }"""
    )
    assert len(points) == 17

    equips = brick_model.query(
        """SELECT ?e WHERE {
        ?e rdf:type/rdfs:subClassOf* brick:Equipment
    }"""
    )
    assert len(equips) == 4


def test_rdfs_inference_subclass():
    EX = Namespace("http://example.com/building#")
    graph = Graph(load_brick=True).from_triples(
        [(EX["a"], RDF.type, BRICK.Temperature_Sensor)]
    )
    graph.expand(profile="rdfs")

    res1 = graph.query(
        f"""SELECT ?type WHERE {{
        <{EX["a"]}> rdf:type ?type
    }}"""
    )

    expected = [
        BRICK.Point,
        BRICK.Class,
        BRICK.Entity,
        BRICK.Sensor,
        RDFS.Resource,
        BRICK.Temperature_Sensor,
    ]

    # filter out BNodes
    res = []
    for row in res1:
        row = tuple(filter(lambda x: not isinstance(x, BNode), row))
        res.append(row)
    res = list(filter(lambda x: len(x) > 0, res))

    assert len(res) == len(expected), f"Results were {res}"
    for expected_class in expected:
        assert (expected_class,) in res, f"{expected_class} not found in {res}"


def test_inference_tags():
    EX = Namespace("http://example.com/building#")
    graph = Graph(load_brick=True).from_triples(
        [(EX["a"], RDF.type, BRICK.Air_Flow_Setpoint)]
    )
    graph.expand(profile="shacl", backend="topquadrant")

    res1 = graph.query(
        f"""SELECT ?type WHERE {{
        <{EX["a"]}> rdf:type ?type
    }}"""
    )

    expected = [
        BRICK.Air_Flow_Setpoint,
    ]
    # filter out BNodes
    res1 = filter_bnodes(res1)

    assert set(res1) == set(map(lambda x: (x,), expected))

    res2 = graph.query(
        f"""SELECT ?tag WHERE {{
        <{EX["a"]}> brick:hasTag ?tag
    }}"""
    )

    expected = [
        TAG.Point,
        TAG.Air,
        TAG.Flow,
        TAG.Setpoint,
    ]
    res2 = filter_bnodes(res2)

    assert set(res2) == set(map(lambda x: (x,), expected))
