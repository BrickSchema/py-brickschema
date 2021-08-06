"""
The `graph` module provides a wrapper class + convenience methods for
building and querying a Brick graph
"""
import io
import os
import sys
import glob
import functools
import pkgutil
import rdflib
import owlrl
import pyshacl
import logging
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

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Graph(rdflib.Graph):
    def __init__(
        self,
        *args,
        load_brick=False,
        load_brick_nightly=False,
        brick_version="1.2",
        postpone_init=False,
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
            postpone_init (bool): useful if you are using rdflib_sqlalchemy or other
                RDFlib plugins that require additional graph initialization (e.g.
                Graph.open()). If True, will delay loading in Brick definitions until
                self.open() is called or self._graph_init()

        Returns:
            A Graph object
        """
        super().__init__(*args, **kwargs)
        self._brick_version = brick_version
        self._load_brick = load_brick
        self._load_brick_nightly = load_brick_nightly
        if not postpone_init:
            self.graph_init()

    def graph_init(self):
        """
        Initializes the graph by downloading or loading from local cache the requested
        versions of the Brick ontology. If Graph() is initialized without postpone_init=False
        (the default value), then this needs to be called manually. Using Graph.open() as
        part of an external store will also call this method automatically
        """
        ns.bind_prefixes(self, brick_version=self._brick_version)

        if self._load_brick_nightly:
            self.parse(
                "https://github.com/BrickSchema/Brick/releases/download/nightly/Brick.ttl",
                format="turtle",
            )
        elif self._load_brick:
            # get ontology data from package
            data = pkgutil.get_data(
                __name__, f"ontologies/{self._brick_version}/Brick.ttl"
            ).decode()
            # wrap in StringIO to make it file-like
            self.parse(source=io.StringIO(data), format="turtle")

        self._tagbackend = None

    def open(self, *args, **kwargs):
        """
        Open the RDFlib graph store (see https://rdflib.readthedocs.io/en/stable/apidocs/rdflib.html?highlight=open#rdflib.Graph.open)

        Might be necessary for stores that require opening a connection to a
        database or acquiring some resource.
        """
        super().open(*args, **kwargs)
        self._graph_init()

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

        If the last item of a triple is a list/tuple of length-2 lists/tuples,
        then this method will substitute a blank node as the object of the original
        triple, add the new triples, and add as many triples as length-2 items in the
        list with the blank node as the subject and the item[0] and item[1] as the predicate
        and object, respectively.

        For example, calling add((X, Y, [(A,B), (C,D)])) produces the following triples:

            X Y _b1 .
            _b1 A B .
            _b1 C D .

        or, in turtle:

            X Y [
              A B ;
              C D ;
            ] .
        """
        for triple in triples:
            assert len(triple) == 3
            obj = triple[2]
            if isinstance(obj, (list, tuple)):
                for suffix in obj:
                    assert len(suffix) == 2
                bnode = rdflib.BNode()
                self.add((triple[0], triple[1], bnode))
                for (nested_pred, nested_obj) in obj:
                    self.add((bnode, nested_pred, nested_obj))
            else:
                super().add(triple)

    @property
    def nodes(self):
        """
        Returns all nodes in the graph

        Returns:
            nodes (list of rdflib.URIRef): nodes in the graph
        """
        return self.all_nodes()

    def rebuild_tag_lookup(self, brick_file=None):
        """
        Rebuilds the internal tag lookup dictionary used for Brick tag->class inference.
        This is broken out as its own method because it is potentially an expensive operation.
        """
        self._tagbackend = TagInferenceSession(
            rebuild_tag_lookup=True, brick_file=brick_file, approximate=False
        )

    def get_most_specific_class(self, classlist):
        """
        Given a list of classes (rdflib.URIRefs), return the 'most specific' classes
        This is a subset of the provided list, containing classes that are not subclasses
        of anything else in the list. Uses the class definitions in the graph to perform
        this task

        Args:
            classlist (list of rdflib.URIRef): list of classes

        Returns:
            classlist (list of rdflib.URIRef): list of specific classes
        """

        specific = []
        for c in classlist:
            # get subclasses of this class
            subc = set(
                [
                    r[0]
                    for r in self.query(
                        f"SELECT ?sc WHERE {{ ?sc rdfs:subClassOf+ <{c}> }}"
                    )
                ]
            )
            equiv = set(
                [
                    r[0]
                    for r in self.query(
                        f"SELECT ?eq WHERE {{ {{?eq owl:equivalentClass <{c}>}} UNION {{ <{c}> owl:equivalentClass ?eq }} }}"
                    )
                ]
            )
            if len(subc) == 0:
                # this class has no subclasses and is thus specific
                specific.append(c)
                continue
            subc.difference_update(equiv)
            overlap = len(subc.intersection(set(classlist)))
            if overlap > 0:
                continue
            specific.append(c)
        return specific

    def simplify(self):
        """
        Removes redundant and axiomatic triples and other detritus that is produced as a side effect of reasoning.
        Simplification consists of the following steps:
        - remove all "a owl:Thing", "a owl:Nothing" triples
        - remove all "a <blank node" triples
        - remove all "X owl:sameAs Y" triples
        """
        for entity, etype in self.subject_objects(ns.RDF.type):
            if etype in [ns.OWL.Thing, ns.OWL.Nothing]:
                self.remove((entity, ns.A, etype))
            elif isinstance(etype, rdflib.BNode):
                self.remove((entity, ns.A, etype))

        for a, b in self.subject_objects(ns.OWL.sameAs):
            if a == b:
                self.remove((a, ns.OWL.sameAs, b))

    def expand(self, profile=None, backend=None, simplify=True):
        """
        Expands the current graph with the inferred triples under the given entailment regime
        and with the given backend. Possible profiles are:
        - 'rdfs': runs RDFS rules
        - 'owlrl': runs full OWLRL reasoning
        - 'vbis': adds VBIS tags
        - 'shacl': does SHACL-AF reasoning (including tag inference, if the extension is loaded)

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
                self.expand(prf, backend=backend, simplify=simplify)
            return

        if profile == "brick":
            return self.expand("owlrl+shacl+owlrl", backend=backend, simplify=simplify)
        elif profile == "rdfs":
            owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(self)
            return
        elif profile == "shacl":
            pyshacl.validate(
                self, advanced=True, abort_on_first=True, allow_warnings=True
            )
            return self
        elif profile == "owlrl":
            self._inferbackend = OWLRLNaiveInferenceSession()
            try:
                if backend is None or backend == "reasonable":
                    self._inferbackend = OWLRLReasonableInferenceSession()
                    backend = "reasonable"
            except ImportError:
                logger.info("Could not load Reasonable reasoner")
                self._inferbackend = OWLRLNaiveInferenceSession()

            try:
                if backend is None or backend == "allegrograph":
                    self._inferbackend = OWLRLAllegroInferenceSession()
                    backend = "allegrograph"
            except (ImportError, ConnectionError):
                logger.info("Could not load Allegro reasoner")
                self._inferbackend = OWLRLNaiveInferenceSession()
        elif profile == "vbis":
            self._inferbackend = VBISTagInferenceSession(
                brick_version=self._brick_version
            )
        else:
            raise Exception(f"Invalid profile '{profile}'")
        self._inferbackend.expand(self)

        if simplify:
            self.simplify()
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

    def get_alignments(self):
        """
        Returns a list of Brick alignments

        This currently just lists the alignments already loaded into brickschema,
        but may in the future pull a list of alignments off of an online resolver
        """
        d = os.path.dirname(sys.modules[__name__].__file__)
        alignment_path = os.path.join(
            d, "ontologies", self._brick_version, "alignments"
        )
        alignments = glob.glob(os.path.join(alignment_path, "*.ttl"))
        return [
            os.path.basename(x)[len("Brick-") : -len("-alignment.ttl")]
            for x in alignments
        ]

    def load_alignment(self, alignment_name):
        """
        Loads the given alignment into the current graph by name.
        Use get_alignments() to get a list of alignments
        """
        alignment_name = f"Brick-{alignment_name}-alignment.ttl"
        alignment_path = os.path.join(
            "ontologies", self._brick_version, "alignments", alignment_name
        )
        data = pkgutil.get_data(__name__, alignment_path).decode()
        # wrap in StringIO to make it file-like
        self.parse(source=io.StringIO(data), format="turtle")

    def get_extensions(self):
        """
        Returns a list of Brick extensions

        This currently just lists the extensions already loaded into brickschema,
        but may in the future pull a list of extensions off of an online resolver
        """
        d = os.path.dirname(sys.modules[__name__].__file__)
        extension_path = os.path.join(
            d, "ontologies", self._brick_version, "extensions"
        )
        extensions = glob.glob(os.path.join(extension_path, "*.ttl"))
        return [
            os.path.basename(x).strip(".ttl")[len("brick_extension_") :]
            for x in extensions
        ]

    def load_extension(self, extension_name):
        """
        Loads the given extension into the current graph by name.
        Use get_extensions() to get a list of extensions
        """
        extension_name = f"brick_extension_{extension_name}.ttl"
        extension_path = os.path.join(
            "ontologies", self._brick_version, "extensions", extension_name
        )
        data = pkgutil.get_data(__name__, extension_path).decode()
        # wrap in StringIO to make it file-like
        self.parse(source=io.StringIO(data), format="turtle")

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
        return pyshacl.validate(
            self,
            shacl_graph=shapes,
            advanced=True,
            abort_on_first=True,
            allow_warnings=True,
        )

    def serve(self, address="127.0.0.1:8080", ignore_prefixes=[]):
        """
        Start web server offering SPARQL queries and 1-click reasoning capabilities

        Args:
          address (str): <host>:<port> of the web server
          ignore_prefixes (list[str]): list of prefixes not to be added to the query editor's namespace bindings.
        """
        srv = web.Server(self, ignore_prefixes=ignore_prefixes)
        srv.start(address)
