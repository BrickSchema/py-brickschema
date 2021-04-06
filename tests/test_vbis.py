from brickschema.inference import VBISTagInferenceSession
from brickschema.graph import Graph
from brickschema.namespaces import BRICK
from rdflib import Namespace
import pytest
import pkgutil
import io


def test_vbis_to_brick_inference():
    session = VBISTagInferenceSession()
    assert session is not None

    # input a fully-qualified VBIS tag, get Brick classes out
    test_cases = [
        ("ME-AHU-Su", BRICK.AHU),
        ("ME-AHU-Su-BU", BRICK.AHU),
        ("ME-ATU-VAV-SD", BRICK.VAV),
    ]
    for (vbistag, brickclass) in test_cases:
        predicted_classes = session.lookup_brick_class(vbistag)
        assert brickclass in predicted_classes


@pytest.mark.skip(
    reason="VBIS/Brick classification differences mean that this test does not pass currently"
)
def test_brick_to_vbis_inference_with_owlrl():
    ALIGN = Namespace("https://brickschema.org/schema/Brick/alignments/vbis#")

    # input brick model; instances should have appropriate VBIS tags
    g = Graph(load_brick=True)
    data = pkgutil.get_data(__name__, "data/vbis_inference_test.ttl").decode()
    g.load_file(source=io.StringIO(data))
    g.expand(profile="owlrl")
    g.expand(profile="vbis")

    test_cases = [
        ("http://bldg#f1", "ME-Fa"),
        ("http://bldg#rtu1", "ME-ACU"),
    ]
    for (entity, vbistag) in test_cases:
        query = f"SELECT ?tag WHERE {{ <{entity}> <{ALIGN.hasVBISTag}> ?tag }}"
        res = list(g.query(query))
        assert len(res) == 1
        assert str(res[0][0]) == vbistag

    conforms, _, results = g.validate()
    assert conforms, results


# TODO: do without owlrl inference
