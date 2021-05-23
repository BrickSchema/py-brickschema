from brickschema.graph import Graph
import rdflib
import pkgutil
import io


def test_simplify():
    g = Graph(load_brick=True)
    data = pkgutil.get_data(__name__, "data/test.ttl").decode()
    g.load_file(source=io.StringIO(data))

    g.expand("brick", simplify=False)

    q = "SELECT ?type WHERE { bldg:VAV2-4.SUPFLOW a ?type }"
    rows = list(g.query(q))
    print(rows)
    bnodes = [r[0] for r in rows if isinstance(r[0], rdflib.BNode)]
    assert len(bnodes) > 0

    g.simplify()

    rows = list(g.query(q))
    bnodes = [r[0] for r in rows if isinstance(r[0], rdflib.BNode)]
    assert len(bnodes) == 0
