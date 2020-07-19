from brickschema.inference import (
    TagInferenceSession,
    HaystackInferenceSession,
    RDFSInferenceSession,
    OWLRLInferenceSession,
    InverseEdgeInferenceSession,
    OWLRLReasonableInferenceSession,
    BrickInferenceSession,
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
    session = TagInferenceSession(approximate=False)
    assert session is not None
    g = Graph(load_brick=False)
    data = pkgutil.get_data(__name__, "data/tags.ttl").decode()
    g.load_file(source=io.StringIO(data))
    g = session.expand(g)

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
    session = BrickInferenceSession()
    assert session is not None
    g = Graph(load_brick=True)
    data = pkgutil.get_data(__name__, "data/brick_inference_test.ttl").decode()
    g.load_file(source=io.StringIO(data))
    g = session.expand(g)

    r = g.query("SELECT ?x WHERE { ?x rdf:type brick:Air_Temperature_Sensor }")
    # assert len(r) == 5
    urls = set([str(row[0]) for row in r])
    real_sensors = set(
        [
            "http://example.com/mybuilding#sensor1",
            "http://example.com/mybuilding#sensor2",
            "http://example.com/mybuilding#sensor3",
            "http://example.com/mybuilding#sensor4",
            "http://example.com/mybuilding#sensor5",
        ]
    )
    assert urls == real_sensors


def test_haystack_inference():
    session = HaystackInferenceSession("http://example.org/carytown")
    assert session is not None
    data = pkgutil.get_data(__name__, "data/carytown.json").decode()
    raw_model = json.loads(data)
    brick_model = session.infer_model(raw_model)
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
    session = RDFSInferenceSession()
    assert session is not None

    EX = Namespace("http://example.com/building#")
    graph = [(EX["a"], RDF.type, BRICK.Temperature_Sensor)]
    expanded_graph = session.expand(graph)

    res1 = expanded_graph.query(
        f"""SELECT ?type WHERE {{
        <{EX["a"]}> rdf:type ?type
    }}"""
    )

    expected = [
        BRICK.Point,
        BRICK.Class,
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


def test_owl_inference_tags():
    session = OWLRLInferenceSession()
    assert session is not None

    EX = Namespace("http://example.com/building#")
    graph = [(EX["a"], RDF.type, BRICK.Air_Flow_Setpoint)]
    expanded_graph = session.expand(graph)

    res1 = expanded_graph.query(
        f"""SELECT ?type WHERE {{
        <{EX["a"]}> rdf:type ?type
    }}"""
    )

    expected = [
        # RDF.Resource,
        # RDFS.Resource,
        OWL.Thing,
        BRICK.Point,
        BRICK.Class,
        BRICK.Setpoint,
        BRICK.Flow_Setpoint,
        BRICK.Air_Flow_Setpoint,
    ]
    # filter out BNodes
    res1 = filter_bnodes(res1)

    assert set(res1) == set(map(lambda x: (x,), expected))

    res2 = expanded_graph.query(
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


def test_owl_inference_tags_reasonable():
    session = OWLRLReasonableInferenceSession()
    assert session is not None

    EX = Namespace("http://example.com/building#")
    graph = [(EX["a"], RDF.type, BRICK.Air_Flow_Setpoint)]
    expanded_graph = session.expand(graph)

    res1 = expanded_graph.query(
        f"""SELECT ?type WHERE {{
        <{EX["a"]}> rdf:type ?type
    }}"""
    )

    expected = [
        OWL.Thing,
        BRICK.Point,
        BRICK.Class,
        BRICK.Setpoint,
        BRICK.Flow_Setpoint,
        BRICK.Air_Flow_Setpoint,
    ]
    # filter out BNodes
    res1 = filter_bnodes(res1)

    assert set(res1) == set(map(lambda x: (x,), expected))

    res2 = expanded_graph.query(
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


def test_inverse_edge_inference():
    session = InverseEdgeInferenceSession()
    assert session is not None

    EX = Namespace("http://example.com/building#")
    graph = [
        (EX["vav1"], RDF.type, BRICK.VAV),
        (EX["ahu1"], RDF.type, BRICK.AHU),
        (EX["ahu1"], BRICK.feeds, EX["vav1"]),
    ]
    expanded_graph = session.expand(graph)

    res1 = expanded_graph.query(
        f"""SELECT ?a ?b WHERE {{
        ?a brick:isFedBy ?b
    }}"""
    )
    expected = [(EX["vav1"], EX["ahu1"])]

    assert len(res1) == len(expected), f"Results were {res1}"
    for expected_row in expected:
        assert expected_row in res1, f"{expected_row} not found in {res1}"
