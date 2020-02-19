from brickschema.validate import Validate
from brickschema.namespaces import RDF, RDFS, BRICK, TAG, OWL
from rdflib import Namespace, BNode, Graph
import pytest

def test_validate():
    dataG = Graph()
    dataG.parse('sample_graph.ttl', format='turtle')
    v = Validate()
    (conforms, results_graph, results_text) = v.validate(dataG)
    print(results_text)
