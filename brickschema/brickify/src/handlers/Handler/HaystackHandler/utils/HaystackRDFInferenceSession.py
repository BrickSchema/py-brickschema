import rdflib
from brickschema.inference import HaystackInferenceSession
from brickschema.namespaces import BRICK, A, RDFS
from rdflib import Namespace, Graph
from typer import progressbar


class HaystackRDFInferenceSession(HaystackInferenceSession):
    def __init__(self, namespace):
        super().__init__(namespace)
        self._BLDG = Namespace(namespace)
        self._tagmap = {
            "cmd": "command",
            "sp": "setpoint",
            "temp": "temperature",
            "lights": "lighting",
            "rtu": "RTU",
            "ahu": "AHU",
            "freq": "frequency",
            "equip": "equipment",
        }
        self._filters = [
            lambda x: not x.startswith("his"),
            lambda x: not x.endswith("Ref"),
            lambda x: not x.startswith("cur"),
            lambda x: x != ("disMacro"),
            lambda x: x != "navName",
            lambda x: x != "tz",
            lambda x: x != "mod",
            lambda x: x != "id",
        ]

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
                entity_tagset = list(
                    map(
                        lambda x: self._tagmap[x.lower()] if x in self._tagmap else x,
                        marker_tags,
                    )
                )
                # infer tags for single entity
                triples, _ = self.infer_entity(entity_tagset, identifier="id")
                for triple in triples:
                    if triple[1] == A:
                        graph.add((instance, A, triple[2]))
                        graph.add((instance, BRICK.label, graph.label(instance)))
