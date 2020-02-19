from brickschema.shacl import BrickShape
from brickschema.namespaces import RDF, RDFS, BRICK, TAG, OWL
from rdflib import Namespace, BNode, Graph
import pytest

def test_validate():
    dataG = Graph()
    dataG.parse('sample_graph.ttl', format='turtle')
    bs = BrickShape()
    (conforms, results_graph, results_text) = bs.validate(dataG)
    print(results_text)
