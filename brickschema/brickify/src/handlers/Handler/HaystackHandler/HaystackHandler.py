from typing import Optional

import importlib_resources
import rdflib

from brickschema.brickify.src.handlers.Handler.Handler import Handler
from brickschema.brickify.src.handlers.Handler.HaystackHandler.utils.HaystackRDFInferenceSession import (
    HaystackRDFInferenceSession,
)


class HaystackHandler(Handler):
    def __init__(
        self,
        source,
        input_format: Optional[str] = "turtle",
        config_file: Optional[str] = None,
    ):
        module_path = (
            [
                "brickschema.brickify.src.handlers.Handler.HaystackHandler.conversions",
                "haystack.json",
            ]
            if not config_file
            else []
        )
        super().__init__(
            source=source,
            input_format=input_format,
            module_path=module_path,
            config_file=config_file,
        )
        self.hs_graph = rdflib.Graph()
        self.input_graph = rdflib.Graph()
        self.h2b_graph = rdflib.Graph()
        self.hs_graph.parse(
            source="https://project-haystack.dev/download/defs.ttl", format="turtle"
        )
        with importlib_resources.path(module_path[0], "analogy.ttl") as data_file:
            with open(data_file, "r") as h2b:
                self.h2b_graph.load(h2b, format="turtle")

    def ingest_data(self):
        super().ingest_data()
        self.input_graph += self.graph
        self.graph += self.hs_graph
        self.graph += self.h2b_graph

    def translate(self):
        super().translate()

    def infer(self):
        super().infer()
        haysess = HaystackRDFInferenceSession("https://project-haystack.dev/example#")
        haysess.infer_model(self.graph)

    def clean_up(self):
        self.graph -= self.hs_graph
        self.graph -= self.input_graph
        self.graph -= self.h2b_graph
        self.graph.update(
            """
            DELETE { ?thing brick:label ?label . } 
            INSERT { ?thing rdfs:label ?label . } 
            WHERE { ?thing brick:label ?label . }
            """
        )
        self.graph.update(
            'DELETE { ?subject ?predicate ?object . } WHERE { ?subject ?predicate ?object . FILTER ( STRSTARTS(STR(?predicate), "https://project-haystack.org/def/ph") )  }'
        )
        self.graph.update(
            'DELETE { ?subject ?predicate ?object . } WHERE { ?subject ?predicate ?object . FILTER ( STRSTARTS(STR(?subject), "https://project-haystack.org/def/ph") )  }'
        )
        self.graph.update(
            'DELETE { ?subject ?predicate ?object . } WHERE { ?subject ?predicate ?object . FILTER ( STRSTARTS(STR(?object), "https://project-haystack.org/def/ph") )  }'
        )
        self.graph.update(
            """
            DELETE { ?part brick:hasLocation ?location . }
            WHERE { ?thing brick:hasLocation ?location . ?part brick:isPartOf|^brick:hasPart ?thing . }
            """
        )
        self.graph.update(
            """
            DELETE { ?thing brick:hasPart ?part . ?part brick:isPartOf ?thing . }
            WHERE { ?part brick:isPointOf|^brick:hasPoint ?thing . ?part brick:isPartOf|^brick:hasPart ?thing . }
            """
        )
