"""
The `graph` module provides a wrapper class + convenience methods for
building and querying a Brick graph
"""
import io
import pkgutil
import rdflib
import owlrl
from .inference import OWLRLNaiveInferenceSession, OWLRLReasonableInferenceSession
from . import namespaces as ns


class Graph(rdflib.Graph):
    def __init__(self, *args, load_brick=False, load_brick_nightly=False, **kwargs):
        """Wrapper class and convenience methods for handling Brick models
        and graphs. Accepts the same arguments as RDFlib.Graph

        Args:
            load_brick (bool): if True, loads packaged Brick ontology
                into graph
            load_brick_nightly (bool): if True, loads latest nightly Brick build
                into graph (requires internet connection)

        Returns:
            A Graph object
        """
        super().__init__(*args, **kwargs)
        ns.bind_prefixes(self)

        if load_brick_nightly:
            self.parse("https://github.com/BrickSchema/Brick/releases/download/nightly/Brick.ttl", format="turtle")
        elif load_brick:
            # get ontology data from package
            data = pkgutil.get_data(__name__, "ontologies/Brick.ttl").decode()
            # wrap in StringIO to make it file-like
            self.parse(source=io.StringIO(data), format="turtle")

    def load_file(self, filename=None, source=None):
        """
        Imports the triples contained in the indicated file into the graph

        Args:
            filename (str): relative or absolute path to the file
            source (file): file-like object
        """
        if filename is not None:
            if filename.endswith(".ttl"):
                self.g.parse(filename, format="ttl")
            elif filename.endswith(".n3"):
                self.g.parse(filename, format="n3")
        elif source is not None:
            for fmt in ["ttl", "n3"]:
                try:
                    self.g.parse(source=source, format=fmt)
                    return
                except Exception as e:
                    print(f"could not load {filename} as {fmt}: {e}")
            raise Exception(f"unknown file format for {filename}")
        else:
            raise Exception(
                "Must provide either a filename or file-like\
source to load_file"
            )

    def add(self, *triples):
        """
        Adds triples to the graph. Triples should be 3-tuples of rdflib.Nodes
        """
        for triple in triples:
            assert len(triple) == 3
            self.g.add(triple)

    @property
    def nodes(self):
        """
        Returns all nodes in the graph

        Returns:
            nodes (list of rdflib.URIRef): nodes in the graph
        """
        return self.all_nodes()

    @property
    def triples(self):
        return list(self)

    def query(self, querystring):
        """
        Executes a SPARQL query against the underlying graph and returns
        the results

        Args:
            querystring (str): SPARQL query string to be executed

        Returns:
            results (list of list of rdflib.URIRef): query results
        """
        return list(self.query(querystring))

    def expand(self, profile=None, backend=None):
        """
        Expands the current graph with the inferred triples under the given entailment regime
        and with the given backend. Possible profiles are:
        - 'rdfs': runs RDFS rules
        - 'owlrl': runs full OWLRL reasoning
        - 'vbis': adds VBIS tags
        - 'tag': infers Brick classes from Brick tags

        Possible backends are:
        - 'reasonable': default, fastest backend
        - 'allegrograph': uses Docker to interface with allegrograph
        - 'owlrl': native-Python implementation

        Not all backend work with all profiles. In that case, brickschema will use the fastest appropriate
        backend in order to perform the requested inference.
        """

        if profile == 'rdfs':
            triples = owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(self)
            self.add(*triples)
            return
        elif profile == 'owlrl':
            self._inferbackend = OWLRLNaiveInferenceSession()
            try:
                if backend == 'allegro':
                    self._inferbackend = OWLRLAllegroInferenceSession()
                if backend == 'reasonable':
                    self._inferbackend = OWLRLReasonableInferenceSession
            except Exception as e:
                self._inferbackend = OWLRLNaiveInferenceSession()
        elif profile == 'vbis':
            pass
        elif profile == 'tag':
            pass

