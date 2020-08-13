"""
The `validate` module implements a wrapper of `pySHACL`_ to
validate an ontology graph against the default Brick Schema constraints (called *shapes*) and user-defined shapes.

.. _`pySHACL`: https://github.com/RDFLib/pySHACL
"""
import sys
import argparse
from rdflib import Graph
from brickschema.validate import Validator


def main():
    parser = argparse.ArgumentParser(
        description="pySHACL wrapper for reporting constraint violating triples."
    )
    parser.add_argument(
        "data",
        metavar="DataGraph",
        type=argparse.FileType("rb"),
        help="Data graph file.",
    )
    parser.add_argument(
        "-s",
        "--shacl",
        dest="shacl",
        action="append",
        nargs="?",
        help="SHACL shapes graph files (accumulative) (in addition to BrickShape.ttl).",
    )
    parser.add_argument(
        "-e",
        "--ont-graph",
        dest="ont",
        action="append",
        nargs="?",
        help="Ontology graph files (accumulative) (in addition to Brick.ttl).",
    )
    parser.add_argument(
        "--noBrickSchema",
        dest="noBrickSchema",
        action="store_true",
        default=False,
        help="Do not use Brick.ttl as an ontology file.",
    )
    parser.add_argument(
        "--noDefaultShapes",
        dest="noDefaultShapes",
        action="store_true",
        default=False,
        help="Do not use BrickShape.ttl as an shape file.",
    )
    parser.add_argument(
        "-i",
        "--inference",
        dest="inference",
        action="store",
        default="rdfs",
        choices=("none", "rdfs", "owlrl", "both"),
        help="Type of inference against data graph before validating.",
    )
    parser.add_argument(
        "-m",
        "--metashacl",
        dest="metashacl",
        action="store_true",
        default=False,
        help="Validate SHACL shapes graph against shacl-shacl "
        "shapes graph before validating data graph.",
    )
    parser.add_argument(
        "-a",
        "--advanced",
        dest="advanced",
        action="store_true",
        default=False,
        help="Enable features from SHACL Advanced Features specification.",
    )
    parser.add_argument(
        "--abort",
        dest="abort",
        action="store_true",
        default=False,
        help="Abort on first error.",
    )
    parser.add_argument(
        "-d",
        "--debug",
        dest="debug",
        action="store_true",
        default=False,
        help="Output additional runtime messages.",
    )

    args = parser.parse_args()

    dataG = Graph()
    dataG = dataG.parse(args.data, format="turtle")

    shaclGraphs = []
    if args.shacl:
        for shaclFile in args.shacl:
            shaclG = Graph()
            shaclG.parse(shaclFile, format="turtle")
            shaclGraphs.append(shaclG)

    ontGraphs = []
    if args.ont:
        for ontFile in args.ont:
            ontG = Graph()
            ontG.parse(ontFile, format="turtle")
            ontGraphs.append(ontG)

    v = Validator(
        useBrickSchema=(False if args.noBrickSchema else True),
        useDefaultShapes=(False if args.noDefaultShapes else True),
    )
    result = v.validate(
        dataG,
        ont_graphs=ontGraphs,
        shacl_graphs=shaclGraphs,
        inference=args.inference,
        abort_on_error=args.abort,
        advanced=args.advanced,
        meta_shacl=args.metashacl,
        debug=args.debug,
    )
    print(result.textOutput)
    exit(0 if result.conforms else -1)


if __name__ == "__main__":
    main()
