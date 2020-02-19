"""
The `validate` module implements a wrapper of [pySHACL](https://github.com/RDFLib/pySHACL) to
validate an ontology graph against default Brick Schema constraints (called *shapes*) and user-defined
shapes
"""
import logging
from rdflib import Graph, Namespace, URIRef, BNode
from rdflib.plugins.sparql import prepareQuery
from .namespaces import BRICK, A, RDF, RDFS, BRICK, BSH, SH, SKOS, bind_prefixes
from . import graph as bsGraph
import pyshacl

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S', level=logging.INFO)

class Validate():

    # build accumulative namespace index from participating files
    # build list of violations, each is a graph
    def __init__(self):
        logging.info('BrickShape init')

        # Read in Brick.ttl.  Remove rdfs:domain and rdfs:range.  Use the modified
        # ontology for reasoning.  See DESIGN.md for more discussion
        self.brickG = bsGraph.Graph(load_brick=True).g
        self.namespaceDict = {}
        self.__buildNamespaceDict(self.brickG)
        self.brickG.update('DELETE { ?s rdfs:domain ?o .} WHERE { ?s rdfs:domain ?o . }',
                           initNs=self.namespaceDict)
        self.brickG.update('DELETE { ?s rdfs:range ?o .} WHERE { ?s rdfs:range ?o . }',
                           initNs=self.namespaceDict)

        # Read in basic shapes for Brick.
        bsGraphObj = bsGraph.Graph()
        bsGraphObj.load_file(filename='ontologies/BrickShape.ttl')
        # bsGraphObj.load_file(filename='/home/czang/py-brickschema/brickschema/ontologies/BrickShape.ttl')
        self.shapeG = bsGraphObj.g


    def validate(self, data_graph, shacl_graph=None, ont_graph=None,
                 inference='rdfs', abort_on_error=False,
                 meta_shacl=False, debug=False):
        logging.info('wrapper function for pySHACL validate()')

        sg = shacl_graph if shacl_graph else self.shapeG
        og = ont_graph if ont_graph else self.brickG

        self.data_graph = data_graph
        (self.conforms, self.results_graph, self.results_text) = pyshacl.validate(
            data_graph, shacl_graph=sg, ont_graph=og,
            inference=inference, abort_on_error=abort_on_error,
            meta_shacl=meta_shacl, debug=debug)

        self.__attachOffendingTriples()
        print(self.conforms, self.results_graph, self.results_text)
        return (self.conforms, self.results_graph, self.results_text)

    # Post process after calling pySHACL.validate to find offending
    # triple(s) for each violation.
    def __attachOffendingTriples(self):
        logging.info('find offending triple(s) for each violation')

        self.namespaceDict = {}
        self.__buildNamespaceDict(self.results_graph)
        self.__buildNamespaceDict(self.data_graph)

        # results_graph from pyshacl.validate() is a list of graphs.
        # Some graphs are violation graphs each representing
        # a violation with the sh:result predicate.
        # There are also other graphs without sh:result and we
        # don't care about them.
        # To filter out the unwanted graphs, we
        # iterate the results_graph twice:
        # Round 1: Create a graph for each violation and index it.
        # Round 2: Add all triples belonging to a violation to proper entry.

        self.violationDict = {}
        for (s, p, o) in self.results_graph:
            if (o not in self.violationDict) and (p == SH.result):
                self.violationDict[o] = Graph()
                for n in self.namespaceDict:
                    self.violationDict[o].bind(n, self.namespaceDict[n])

        for (s, p, o) in self.results_graph:
            if s in self.violationDict:
                self.violationDict[s].add((s, p, o))

        # find the offending triple(s) for each violation graph and add into it
        for k, violation in self.violationDict.items():
            self.__triplesForOneViolation(violation)

    # Load namespaces into a dictionary which is accumulative with
    # the shape graph and data graph.
    def __buildNamespaceDict(self, g):
        for (prefix, path) in g.namespaces():
            assert (prefix not in self.namespaceDict) or \
                (Namespace(path) == self.namespaceDict[prefix]), \
                "Same prefix \'%s\' used for %s and %s" % \
                (prefix, self.namespaceDict[prefix], path)

            if prefix not in self.namespaceDict:
                self.namespaceDict[prefix] = Namespace(path)

    # Query data graph and return the list of resulting triples
    def __queryDataGraph(self, s, p, o):
        q = prepareQuery('SELECT ?s ?p ?o WHERE {%s %s %s .}' %
                         (s if s else '?s',
                          p if p else '?p',
                          o if o else '?o'),
                         initNs=self.namespaceDict
                         )
        res = self.data_graph.query(q)
        assert len(res), \
            'Must have at lease one triple like \'%s %s %s\'' % (s, p, o)
        return res


    # Take one contraint violation (a graph) and a sh: predicate,
    # find the object which is a node in the data graph.
    # Return the object found or None.
    def __violationPredicateObj(self, violation, predicate, mustFind=True):
        q = prepareQuery('SELECT ?s ?p ?o WHERE {?s %s ?o .}' % predicate,
                         initNs=self.namespaceDict
                        )
        res = violation.query(q)
        if mustFind:
            assert len(res) == 1, 'Must have predicate \'%s\'' % predicate
        if len(res):
            for (s, p, o) in res:
                return o
        return None  # Ok to miss certain predicate, such as sh:resultPath


    # Take one contraint violation (a graph) and find the potential offending
    # triples.  Return the triples in a list.
    def __triplesForOneViolation(self, violation):
        resultPath = self.__violationPredicateObj(violation,
                                                'sh:resultPath',
                                                mustFind=False)
        if resultPath:
            focusNode = self.__violationPredicateObj(violation, 'sh:focusNode')
            valueNode = self.__violationPredicateObj(violation, 'sh:value')

            # TODO: Although we haven't seen a violation with sh:resultPath where
            # focusNode and valueNode are the same, the case should be considered.
            # The triple probably should be queried using queryDataGraph() instead
            # of assuming focusNode is the subject here.

            g = Graph()
            g.add((focusNode, resultPath, valueNode))
            violation.add((BNode(), BSH['offendingTriple'], g))
            return

        # Without sh:resultPath in the violation. We are currently only concerned
        # with the RDFS.domain shape.
        sourceShape = self.__violationPredicateObj(violation, 'sh:sourceShape')
        (bsh, shapeName) = sourceShape.split('#')

        if shapeName.endswith('DomainShape'):
            # For a brick property xyz with RDFS.domain predicate, the shape's name
            # is bsh:xyzDomainShape.  Here we tease out brick:xyz to make the query.
            brickProp = shapeName[:-len('DomainShape')]
            path = 'brick:' + brickProp
            fullPath = self.namespaceDict['brick'] + brickProp

            # The full name (http...) of the focusNode doesn't seem to work
            # in the query.  Therefore make a prefixed version for the query.
            focusNode = self.__violationPredicateObj(violation, 'sh:focusNode')
            (ns, name) = focusNode.split('#')
            namespaces = [key  for (key, value) in self.namespaceDict.items() \
                          if Namespace(ns+'#') == value]
            assert len(namespaces), "Must find a prefix for %s" % focusNode
            res = self.__queryDataGraph('%s:%s' % (namespaces[0], name), path, None)

            # Due to inherent ambiguity of this kind of shape,
            # multiple triples may be found.
            for (s, p, o) in res:
                g = Graph()
                g.add((focusNode, URIRef(fullPath), o))
                violation.add((BNode(), BSH['offendingTriple'], g))

            return

        # When control reaches here, a handler is missing for the violation.
        logging.error('no triple finder for violation %s' % g.serialize(format='ttl'))

        return

    # end of triplesForOneViolation()

# end of class BrickShape()
