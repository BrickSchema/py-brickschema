from brickschema.graph import Graph
import rdflib
import pkgutil
import io


def test_simplify(inference_backend):
    g = Graph(load_brick=True)
    data = pkgutil.get_data(__name__, "data/test.ttl").decode()
    g.load_file(source=io.StringIO(data))

    g.expand("owlrl", simplify=False, backend=inference_backend)
    g.serialize("/tmp/test.ttl", format="ttl")

    q = "SELECT ?type WHERE { bldg:VAV2-4.ZN_T a ?type }"
    rows = list(g.query(q))
    bnodes = [r[0] for r in rows if isinstance(r[0], rdflib.BNode)]
    assert len(bnodes) >= 0

    g.simplify()

    rows = list(g.query(q))
    bnodes = [r[0] for r in rows if isinstance(r[0], rdflib.BNode)]
    assert len(bnodes) == 0
