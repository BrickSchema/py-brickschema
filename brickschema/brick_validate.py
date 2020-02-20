#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is
# https://github.com/RDFLib/pySHACL/blob/master/pyshacl/cli.py
# @ release 0.11.3 when this comment is made
# with minimal changes to find offending triples for each
# reported constraint violation -- see offendingTriples.py.

import sys
import argparse
from .validate import Validate
from rdflib import Graph

parser = argparse.ArgumentParser(description='pySHACL wrapper for reporting constraint violating triples.')
parser.add_argument('data', metavar='DataGraph', type=argparse.FileType('rb'),
                    help='Data graph file.')
parser.add_argument('-s', '--shacl', dest='shacl', action='store', nargs='?',
                    help='SHACL shapes graph file (default to BrickShape.ttl).')
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


def main():
    args = parser.parse_args()

    dataG = Graph()
    dataG = dataG.parse(args.data, format='turtle')

    shaclG = None
    if args.shacl:
        shaclG = Graph()
        shaclG.parse(args.shacl, format='turtle')

    ontG = None
    if args.ont:
        ontG = Graph()
        ontG.parse(args.ont, format='turtle')

    (conforms, results_graph, results_text) = Validate().validate(
        dataG, shacl_graph=shaclG, ont_graph=ontG,
        inference=args.inference, abort_on_error=args.abort,
        advanced=args.advanced, meta_shacl=args.metashacl, debug=args.debug)
    args.output.write(results_text)
    args.output.close()
    exit(0 if conforms else -1)

if __name__ == "__main__":
    main()
