"""
The `namespaces` module provides pointers to standard Brick namespaces
and related ontology namespaces
wrapper class and convenience methods for a Brick graph
"""
from rdflib import Namespace, XSD

BRICK11 = Namespace("https://brickschema.org/schema/1.1/Brick#")
TAG11 = Namespace("https://brickschema.org/schema/1.1/BrickTag#")
BSH11 = Namespace("https://brickschema.org/schema/1.1/BrickShape#")

# all versions of Brick > 1.1 have these namespaces
BRICK = Namespace("https://brickschema.org/schema/Brick#")
TAG = Namespace("https://brickschema.org/schema/BrickTag#")
BSH = Namespace("https://brickschema.org/schema/BrickShape#")

# defaults
OWL = Namespace("http://www.w3.org/2002/07/owl#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
SH = Namespace("http://www.w3.org/ns/shacl#")

# QUDT namespaces
QUDT = Namespace("http://qudt.org/schema/qudt/")
QUDTQK = Namespace("http://qudt.org/vocab/quantitykind/")
QUDTDV = Namespace("http://qudt.org/vocab/dimensionvector/")
UNIT = Namespace("http://qudt.org/vocab/unit/")

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
    graph.bind("qudtqk", QUDTQK)
    graph.bind("qudt", QUDT)
    graph.bind("unit", UNIT)

    if brick_version == "1.1":
        graph.bind("brick", BRICK11)
        graph.bind("tag", TAG11)
        graph.bind("bsh", BSH11)
    else:
        graph.bind("brick", BRICK)
        graph.bind("tag", TAG)
        graph.bind("bsh", BSH)
