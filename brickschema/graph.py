"""
The `graph` module provides a wrapper class + convenience methods for
building and querying a Brick graph
"""
import io
from warnings import warn
import os
import sys
import glob
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

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BrickBase(rdflib.Graph):
    def rebuild_tag_lookup(self, brick_file=None):
        """
        Rebuilds the internal tag lookup dictionary used for Brick tag->class inference.
        This is broken out as its own method because it is potentially an expensive operation.
        """
        self._tagbackend = TagInferenceSession(
            rebuild_tag_lookup=True, brick_file=brick_file, approximate=False
        )

    def to_networkx(self):
        """
        Exports the graph as a NetworkX DiGraph. Edge labels are stored in the 'name' attribute
        Returns:
            graph (networkx.DiGraph): networkx object representing this graph
        """
        try:
            import networkx as nx
        except ImportError as e:
            warn("Could not import NetworkX. Need 'networkx' option during install.")
            raise e
        g = nx.DiGraph()
        for (s, p, o) in self.triples((None, None, None)):
            g.add_edge(s, o, name=p)
        return g

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
        shapes = self
        if shape_graphs is not None and isinstance(shape_graphs, list):
            for sg in shape_graphs:
                shapes += sg
        return pyshacl.validate(
            self,
            shacl_graph=shapes,
            ont_graph=shapes,
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
        try:
            from . import web
        except ImportError:
            warn(
                "Using the webserver requires the 'web' option:\n\n\tpip install brickschema[web]"
            )
            import sys

            sys.exit(1)
        srv = web.Server(self, ignore_prefixes=ignore_prefixes)
        srv.start(address)

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

    def _iterative_expand(self, og: "Graph"):
        old_size = len(self)
        for _ in range(3):
            valid, _, report = pyshacl.validate(
                data_graph=self,
                shacl_graph=og,
                ont_graph=og,
                advanced=True,
                allow_warnings=True,
                abort_on_first=True,
                inplace=True,
            )
            if not valid:
                logger.warn(report)
            if len(self) == old_size:
                break

    def expand(
        self, profile, backend=None, simplify=True, ontology_graph=None, iterative=True
    ):
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
            og = None
            if ontology_graph:
                og = ontology_graph.skolemize()
            valid, _, report = pyshacl.validate(
                data_graph=self,
                shacl_graph=og,
                ont_graph=og,
                advanced=True,
                allow_warnings=True,
                abort_on_first=True,
                inplace=True,
            )
            if not valid:
                logger.warn(report)
            if iterative:
                self._iterative_expand(og)
            return self
        elif profile == "owlrl":
            self._inferbackend = OWLRLNaiveInferenceSession()
            try:
                if backend is None or backend == "reasonable":
                    self._inferbackend = OWLRLReasonableInferenceSession()
                    backend = "reasonable"
            except ImportError:
                warn(
                    "Could not load Reasonable reasoner. Needs 'reasonable' option during install."
                )
                self._inferbackend = OWLRLNaiveInferenceSession()

            try:
                if backend is None or backend == "allegrograph":
                    self._inferbackend = OWLRLAllegroInferenceSession()
                    backend = "allegrograph"
            except (ImportError, ConnectionError):
                warn(
                    "Could not load Allegro reasoner. Needs 'allegro' option during install."
                )
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


class GraphCollection(rdflib.Dataset, BrickBase):
    def __init__(
        self,
        *args,
        load_brick=False,
        load_brick_nightly=False,
        brick_version="1.3",
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
            A GraphCollection object
        """
        kwargs.update({"default_union": True})
        super().__init__(*args, **kwargs)
        self._brick_version = brick_version
        self._load_brick = load_brick
        self._load_brick_nightly = load_brick_nightly
        self._graph_init()
        # subset of graphs in the store to use; if this is length-0, then
        # all graphs are used
        self._subset = set()

    def __iter__(self):
        """Iterates over all quads in the store"""
        for (s, p, o, _) in self.quads((None, None, None, None)):
            yield (s, p, o)

    def load_graph(
        self,
        filename: str = None,
        source: io.IOBase = None,
        format: str = None,
        graph: rdflib.Graph = None,
        graph_name: rdflib.URIRef = None,
    ):
        """
        Imports the triples contained in the indicated file (or graph) into the graph.
        Names the graph using any owl:Ontology declaration found in the file
        or using the 'graph_name' argument if it is provided

        Args:
            filename (str): relative or absolute path to the file
            source (file): file-like object
            graph (brickschema.Graph): graph to load into the collection
            graph_name (rdflib.URIRef): name of the graph (defaults to owl:Ontology instance or 'default')

        Return:
            parsed (rdflib.Graph): the graph loaded from parsing the input
        """
        if graph is None:
            graph = Graph().load_file(filename=filename, source=source, format=format)
        if graph_name is None:
            try:
                graph_name = next(graph.subjects(rdflib.RDF.type, ns.OWL.Ontology))
            except StopIteration:
                warn(
                    f"No owl:Ontology found in graph {filename or source}. Using default graph"
                )
                graph_name = rdflib.graph.DATASET_DEFAULT_GRAPH_ID
        else:
            graph_name = rdflib.URIRef(graph_name)
        g = self.graph(graph_name)
        for (s, p, o) in graph.triples((None, None, None)):
            g.add((s, p, o))
        return g

    def remove_graph(self, graph_name):
        """
        Removes the named graph from the graph store

        Args:
            graph_name (str): name of the graph to remove
        """
        self.remove_graph(graph_name)

    def _graph_init(self):
        """
        Initializes the graph by downloading or loading from local cache the requested
        versions of the Brick ontology.
        """
        ns.bind_prefixes(self, brick_version=self._brick_version)

        if self._load_brick_nightly:
            self.parse(
                "https://github.com/BrickSchema/Brick/releases/download/nightly/Brick.ttl",
                format="turtle",
                graph_name="https://brickschema.org/schema/Brick#",
            )
        elif self._load_brick:
            # get ontology data from package
            data = pkgutil.get_data(
                __name__, f"ontologies/{self._brick_version}/Brick.ttl"
            ).decode()
            # wrap in StringIO to make it file-like
            self.load_graph(
                source=io.StringIO(data),
                format="turtle",
                graph_name="https://brickschema.org/schema/Brick#",
            )

        self._tagbackend = None

    @property
    def graph_names(self):
        """
        Returns a list of the names of the graphs in the graph store

        Returns:
            list: list of graph names
        """
        if self._subset:
            return list(self._subset)
        else:
            return [g.identifier for g in self.graphs()]

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
        self.load_graph(source=io.StringIO(data), format="turtle")

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
        self.load_graph(source=io.StringIO(data), format="turtle")

    def contexts(self, triple=None):
        """Iterate over all contexts in the graph

        If triple is specified, iterate over all contexts the triple is in.
        """
        for context in self.store.contexts(triple):
            if len(self._subset) > 0 and context not in self._subset:
                continue
            if isinstance(context, Graph):
                # TODO: One of these should never happen and probably
                # should raise an exception rather than smoothing over
                # the weirdness - see #225
                yield context
            else:
                yield self.get_context(context)


class Graph(BrickBase):
    def __init__(
        self,
        *args,
        load_brick=False,
        load_brick_nightly=False,
        brick_version="1.3",
        _delay_init=False,
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
            _delay_init (bool): if True, the graph will not call internal initialization logic.
                You should not need to touch this.

        Returns:
            A Graph object
        """
        super().__init__(*args, **kwargs)
        self._brick_version = brick_version
        self._load_brick = load_brick
        self._load_brick_nightly = load_brick_nightly
        if not _delay_init:
            self._graph_init()

    def _graph_init(self):
        """
        Initializes the graph by downloading or loading from local cache the requested
        versions of the Brick ontology. If Graph() is initialized Using Graph.open() as
        part of an external store will also call this method automatically
        """
        ns.bind_prefixes(self, brick_version=self._brick_version)

        if self._load_brick_nightly:
            self.load_file(
                "https://github.com/BrickSchema/Brick/releases/download/nightly/Brick.ttl",
                format="turtle",
            )
        elif self._load_brick:
            # get ontology data from package
            data = pkgutil.get_data(
                __name__, f"ontologies/{self._brick_version}/Brick.ttl"
            ).decode()
            # wrap in StringIO to make it file-like
            self.load_file(source=io.StringIO(data), format="turtle")

        self._tagbackend = None

    def load_file(self, filename=None, source=None, format=None):
        """
        Imports the triples contained in the indicated file into the default graph.

        Args:
            filename (str): relative or absolute path to the file
            source (file): file-like object
        """
        if filename is not None:
            fmt = format if format else rdflib.util.guess_format(filename)
            self.parse(filename, format=fmt)
        elif source is not None:
            for fmt in [format, "ttl", "n3", "xml"]:
                try:
                    self.parse(source=source, format=fmt)
                    return self
                except Exception as e:
                    warn(f"could not load {filename} as {fmt}: {e}")
            raise Exception(f"unknown file format for {filename}")
        else:
            raise Exception(
                "Must provide either a filename or file-like\
source to load_file"
            )
        return self

    def add(self, *triples):
        """
        Adds triples to the graph. Triples should be 3-tuples of rdflib.Nodes (or alternatively 4-tuples
        if each triple has a context).

        If the object of a triple is a list/tuple of length-2 lists/tuples,
        then this method will substitute a blank node as the object of the original
        triple, add the new triples, and add as many triples as length-2 items in the
        list with the blank node as the subject and the item[0] and item[1] as the predicate
        and object, respectively.

        For example, calling add((X, Y, [(A,B), (C,D)])) produces the following triples::

            X Y _b1 .
            _b1 A B .
            _b1 C D .

        or, in turtle::

            X Y [
              A B ;
              C D ;
            ] .

        Otherwise, acts the same as rdflib.Graph.add
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
        self.load_file(source=io.StringIO(data), format="turtle")

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
        self.load_file(source=io.StringIO(data), format="turtle")
