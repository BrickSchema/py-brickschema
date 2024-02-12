import rdflib
from brickschema.inference import HaystackInferenceSession
from brickschema.namespaces import BRICK, A
from rdflib import Namespace, Graph
from typer import progressbar


class HaystackRDFInferenceSession(HaystackInferenceSession):
    def __init__(self, namespace):
        super().__init__(namespace)

    def infer_model(self, graph: rdflib.Graph):
        query = """
        SELECT DISTINCT ?instance (GROUP_CONCAT(?markers; SEPARATOR=" ") AS ?p) WHERE {
          ?instance ph:hasTag ?markers . ?markers (a|ph:is|rdfs:subClassOf)* ph:marker .
        } GROUP BY ?instance
        """
        bg = Graph()
        bg.bind("brick", BRICK)
        bg.bind("hs", Namespace("https://project-haystack.dev/example#"))
        with progressbar(graph.query(query)) as results:
            for instance, markers in results:
                marker_tags = [
                    marker.split("#")[-1] for marker in str(markers).split(" ")
                ]
                marker_tags = list(set(marker_tags))
                for f in self._filters:
                    marker_tags = list(filter(f, marker_tags))
                # translate tags
                entity_tagset = list(self._translate_tags(marker_tags))
                # infer tags for single entity
                triples, _ = self.infer_entity(entity_tagset, identifier="id")
                for triple in triples:
                    if triple[1] == A:
                        graph.add((instance, A, triple[2]))
                        graph.add((instance, BRICK.label, graph.label(instance)))
