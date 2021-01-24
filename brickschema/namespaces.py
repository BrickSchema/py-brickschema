"""
The `namespaces` module provides pointers to standard Brick namespaces
and related ontology namespaces
wrapper class and convenience methods for a Brick graph
"""
from rdflib import Namespace

BRICK11 = Namespace("https://brickschema.org/schema/1.1/Brick#")
TAG11 = Namespace("https://brickschema.org/schema/1.1/BrickTag#")
BSH11 = Namespace("https://brickschema.org/schema/1.1/BrickShape#")

BRICK12 = Namespace("https://brickschema.org/schema/1.2/Brick#")
TAG12 = Namespace("https://brickschema.org/schema/1.2/BrickTag#")
BSH12 = Namespace("https://brickschema.org/schema/1.2/BrickShape#")

BRICK = BRICK12
TAG = TAG12
BSH = BSH12
OWL = Namespace("http://www.w3.org/2002/07/owl#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
SH = Namespace("http://www.w3.org/ns/shacl#")

A = RDF.type


def bind_prefixes(graph, brick_version="1.2"):
    """
    Associate common prefixes with the graph
    """
    graph.bind("rdf", RDF)
    graph.bind("owl", OWL)
    graph.bind("rdfs", RDFS)
    graph.bind("skos", SKOS)
    graph.bind("sh", SH)

    if brick_version == "1.2":
        graph.bind("brick", BRICK12)
        graph.bind("tag", TAG12)
        graph.bind("bsh", BSH12)
    elif brick_version == "1.1":
        graph.bind("brick", BRICK11)
        graph.bind("tag", TAG11)
        graph.bind("bsh", BSH11)
    else:
        raise Exception("Invalid Brick version")
