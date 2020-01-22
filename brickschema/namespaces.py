"""
The `namespaces` module provides pointers to standard Brick namespaces
and related ontology namespaces
wrapper class and convenience methods for a Brick graph
"""
from rdflib import Namespace

BRICK = Namespace("https://brickschema.org/schema/1.1.0/Brick#")
TAG = Namespace("https://brickschema.org/schema/1.1.0/BrickTag#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")

A = RDF.type


def bind_prefixes(graph):
    """
    Associate common prefixes with the graph
    """
    graph.g.bind('rdf', RDF)
    graph.g.bind('owl', OWL)
    graph.g.bind('rdfs', RDFS)
    graph.g.bind('skos', SKOS)
    graph.g.bind('brick', BRICK)
    graph.g.bind('tag', TAG)
