"""
The `graph` module provides a wrapper class + convenience methods for
building and querying a Brick graph
"""
import io
import functools
import pkgutil
import rdflib
import owlrl
import pyshacl
from .inference import (
    OWLRLNaiveInferenceSession,
    OWLRLReasonableInferenceSession,
    OWLRLAllegroInferenceSession,
    TagInferenceSession,
    HaystackInferenceSession,
    VBISTagInferenceSession,
)
from . import namespaces as ns
from . import web


class Graph(rdflib.Graph):
    def __init__(
        self,
        *args,
        load_brick=False,
        load_brick_nightly=False,
        brick_version="1.2",
        **kwargs,
    ):
        """Wrapper class and convenience methods for handling Brick models
        and graphs. Accepts the same arguments as RDFlib.Graph

        Args:
            load_brick (bool): if True, loads packaged Brick ontology
                into graph
            load_brick_nightly (bool): if True, loads latest nightly Brick build
                into graph (requires internet connection)
            brick_version (string): the MAJOR.MINOR version of the Brick ontology
                to load into the graph. Only takes effect for the load_brick argument

        Returns:
            A Graph object
        """
        super().__init__(*args, **kwargs)
        ns.bind_prefixes(self, brick_version=brick_version)
        self._brick_version = brick_version

        if load_brick_nightly:
            self.parse(
                "https://github.com/BrickSchema/Brick/releases/download/nightly/Brick.ttl",
                format="turtle",
            )
        elif load_brick:
            # get ontology data from package
            data = pkgutil.get_data(
                __name__, f"ontologies/{brick_version}/Brick.ttl"
            ).decode()
            # wrap in StringIO to make it file-like
            self.parse(source=io.StringIO(data), format="turtle")

        self._tagbackend = None

    def load_file(self, filename=None, source=None):
        """
        Imports the triples contained in the indicated file into the graph

        Args:
            filename (str): relative or absolute path to the file
            source (file): file-like object
        """
        if filename is not None:
            self.parse(filename, format=rdflib.util.guess_format(filename))
        elif source is not None:
            for fmt in ["ttl", "n3", "xml"]:
                try:
                    self.parse(source=source, format=fmt)
                    return
                except Exception as e:
                    print(f"could not load {filename} as {fmt}: {e}")
            raise Exception(f"unknown file format for {filename}")
        else:
            raise Exception(
                "Must provide either a filename or file-like\
source to load_file"
            )
        return self

    def add(self, *triples):
        """
        Adds triples to the graph. Triples should be 3-tuples of rdflib.Nodes
        """
        for triple in triples:
            assert len(triple) == 3
            super().add(triple)

    @property
    def nodes(self):
        """
        Returns all nodes in the graph

        Returns:
            nodes (list of rdflib.URIRef): nodes in the graph
        """
        return self.all_nodes()

    def query(self, querystring):
        """
        Executes a SPARQL query against the underlying graph and returns
        the results

        Args:
            querystring (str): SPARQL query string to be executed

        Returns:
            results (list of list of rdflib.URIRef): query results
        """
        return super().query(querystring)

    def rebuild_tag_lookup(self, brick_file=None):
        """
        Rebuilds the internal tag lookup dictionary used for Brick tag->class inference.
        This is broken out as its own method because it is potentially an expensive operation.
        """
        self._tagbackend = TagInferenceSession(
            rebuild_tag_lookup=True, brick_file=brick_file, approximate=False
        )

    def expand(self, profile=None, backend=None):
        """
        Expands the current graph with the inferred triples under the given entailment regime
        and with the given backend. Possible profiles are:
        - 'rdfs': runs RDFS rules
        - 'owlrl': runs full OWLRL reasoning
        - 'vbis': adds VBIS tags
        - 'shacl': does SHACL-AF reasoning
        - 'tag': infers Brick classes from Brick tags

        Possible backends are:
        - 'reasonable': default, fastest backend
        - 'allegrograph': uses Docker to interface with allegrograph
        - 'owlrl': native-Python implementation

        Not all backend work with all profiles. In that case, brickschema will use the fastest appropriate
        backend in order to perform the requested inference.

        To perform more than one kind of inference in sequence, use '+' to join the profiles:

            import brickschema
            g = brickschema.Graph()
            g.expand(profile='rdfs+shacl') # performs RDFS inference, then SHACL-AF inference
            g.expand(profile='shacl+rdfs') # performs SHACL-AF inference, then RDFS inference


        # TODO: currently nothing is cached between expansions
        """

        if "+" in profile:
            for prf in profile.split("+"):
                self.expand(prf, backend=backend)
            return

        if profile == "brick":
            return self.expand("owlrl+shacl+owlrl", backend=backend)
        elif profile == "rdfs":
            owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(self)
            return
        elif profile == "shacl":
            pyshacl.validate(self, advanced=True, abort_on_error=False)
            return self
        elif profile == "owlrl":
            self._inferbackend = OWLRLNaiveInferenceSession()
            try:
                if backend is None or backend == "reasonable":
                    self._inferbackend = OWLRLReasonableInferenceSession()
                    backend = "reasonable"
            except ImportError:
                self._inferbackend = OWLRLNaiveInferenceSession()

            try:
                if backend is None or backend == "allegrograph":
                    self._inferbackend = OWLRLAllegroInferenceSession()
                    backend = "allegrograph"
            except ImportError:
                self._inferbackend = OWLRLNaiveInferenceSession()
        elif profile == "vbis":
            self._inferbackend = VBISTagInferenceSession()
        elif profile == "tag":
            self._inferbackend = TagInferenceSession(approximate=False)
            if self._tagbackend is not None:
                self._inferbackend.lookup = self._tagbackend.lookup
        else:
            raise Exception(f"Invalid profile '{profile}'")
        self._inferbackend.expand(self)
        return self

    def from_haystack(self, namespace, model):
        """
        Adds to the graph the Brick triples inferred from the given Haystack model.
        The model should be a Python dictionary produced from the Haystack JSON export

        Args:
            model (dict): a Haystack model
        """
        sess = HaystackInferenceSession(namespace)
        self.add(*sess.infer_model(model))
        return self

    def from_triples(self, triples):
        """
        Creates a graph from the given list of triples

        Args:
            triples (list of rdflib.Node): triples to add to the graph
        """
        self.add(*triples)
        return self

    def validate(self, shape_graphs=None, default_brick_shapes=True):
        """
        Validates the graph using the shapes embedded w/n the graph. Optionally loads in normative Brick shapes
        and externally defined shapes

        Args:
          shape_graphs (list of rdflib.Graph or brickschema.graph.Graph): merges these graphs and includes them in
                the validation
          default_brick_shapes (bool): if True, loads in the default Brick shapes packaged with brickschema

        Returns:
          (conforms, resultsGraph, resultsText) from pyshacl
        """
        shapes = None
        if shape_graphs is not None and isinstance(shape_graphs, list):
            shapes = functools.reduce(lambda x, y: x + y, shape_graphs)
        return pyshacl.validate(self, shacl_graph=shapes)

    def serve(self, address="127.0.0.1:8080"):
        """
        Start web server offering SPARQL queries and 1-click reasoning capabilities

        Args:
          address (str): <host>:<port> of the web server
        """
        srv = web.Server(self)
        srv.start(address)
