"""
The `validate` module implements a wrapper of `pySHACL`_ to
validate an ontology graph against the default Brick Schema constraints (called *shapes*) and user-defined shapes.

.. _`pySHACL`: https://github.com/RDFLib/pySHACL
"""
import sys
import argparse
import logging
from rdflib import Graph, Namespace, URIRef, BNode, Literal
from rdflib.plugins.sparql import prepareQuery
from brickschema.namespaces import BRICK, A, RDF, RDFS, BRICK, BSH, SH, SKOS, bind_prefixes
from brickschema.validate import Validate, ResultsSerialize
import pyshacl
import io
import pkgutil

def main():
    parser = argparse.ArgumentParser(description='pySHACL wrapper for reporting constraint violating triples.')
    parser.add_argument('data', metavar='DataGraph', type=argparse.FileType('rb'),
                        help='Data graph file.')
    parser.add_argument('-s', '--shacl', dest='shacl', action='append', nargs='?',
                        help='SHACL shapes graph file (accumulative) (default to BrickShape.ttl).')
    parser.add_argument('-e', '--ont-graph', dest='ont', action='store', nargs='?',
                        help='Ontology graph file (default to Brick.ttl).')
    parser.add_argument('-i', '--inference', dest='inference', action='store',
                        default='rdfs', choices=('none', 'rdfs', 'owlrl', 'both'),
                        help='Type of inference against data graph before validating.')
    parser.add_argument('-m', '--metashacl', dest='metashacl', action='store_true',
                        default=False,
                        help='Validate SHACL shapes graph against shacl-shacl '
                        'shapes graph before validating data graph.')
    parser.add_argument('-a', '--advanced', dest='advanced', action='store_true',
                        default=False,
                        help='Enable features from SHACL Advanced Features specification.')
    parser.add_argument('--abort', dest='abort', action='store_true',
                        default=False, help='Abort on first error.')
    parser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        default=False, help='Output additional runtime messages.')
    parser.add_argument('-o', '--output', dest='output', nargs='?',
                        type=argparse.FileType('w'),
                        help='Send output to a file (default to stdout).',
                        default=sys.stdout)

    args = parser.parse_args()

    dataG = Graph()
    dataG = dataG.parse(args.data, format='turtle')

    shaclGraphs = []
    if args.shacl:
        for shaclFile in args.shacl:
            shaclG = Graph()
            shaclG.parse(shaclFile, format='turtle')
            shaclGraphs.append(shaclG)

    ontG = None
    if args.ont:
        ontG = Graph()
        ontG.parse(args.ont, format='turtle')

    vModule = Validate(useBrickSchema=(False if args.ont else True),
                       useDefaultShapes=(False if shaclGraphs else True))
    for g in shaclGraphs:
        vModule.addShapeGraph(g)
    (conforms, results_graph, results_text) = vModule.validate(
        dataG, ont_graph=ontG,
        inference=args.inference, abort_on_error=args.abort,
        advanced=args.advanced, meta_shacl=args.metashacl, debug=args.debug)
    args.output.write(results_text)

    if not conforms:
        ResultsSerialize(vModule.violationList(),
                         vModule.accumulatedNamespaces(),
                         args.output).appendToOutput()
    args.output.close()
    exit(0 if conforms else -1)

if __name__ == "__main__":
   main()
