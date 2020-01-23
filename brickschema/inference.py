"""
The `inference` module implements inference of Brick entities from tags
and other representations of building metadata
"""

from .graph import Graph
import rdflib
import owlrl
import io
import tarfile
import docker


class RDFSInferenceSession:
    """
    Provides methods and an inferface for producing the deductive closure
    of a graph under RDFS semantics
    """

    def __init__(self, load_brick=True):
        """
        Creates a new RDFS Inference session

        Args:
            load_brick (bool): if True, load Brick ontology into the graph
        """
        self.g = Graph(load_brick=load_brick)

    def expand(self, graph):
        """
        Applies RDFS reasoning from the Python owlrl library to the graph

        Args:
            graph (brickschema.graph.Graph): a Graph object containing triples

        Returns:
            graph (brickschema.graph.Graph): a Graph object containing the
                inferred triples in addition to the regular graph
        """
        for triple in graph:
            self.g.add(triple)
        owlrl.DeductiveClosure(owlrl.RDFS_Semantics).expand(self.g.g)
        return _return_correct_type(graph, self.g)

    @property
    def triples(self):
        return self.g.triples


class OWLRLInferenceSession:
    """
    Provides methods and an inferface for producing the deductive closure
    of a graph under OWL-RL semantics. WARNING this may take a long time
    """

    def __init__(self, load_brick=True):
        """
        Creates a new OWLRL Inference session

        Args:
            load_brick (bool): if True, load Brick ontology into the graph
        """
        self.g = Graph(load_brick=load_brick)

    def expand(self, graph):
        """
        Applies OWLRL reasoning from the Python owlrl library to the graph

        Args:
            graph (brickschema.graph.Graph): a Graph object containing triples

        Returns:
            graph (brickschema.graph.Graph): a Graph object containing the
                inferred triples in addition to the regular graph
        """
        for triple in graph:
            self.g.add(triple)
        owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(self.g.g)
        return _return_correct_type(graph, self.g)

    @property
    def triples(self):
        return self.g.triples


class OWLRLAllegroInferenceSession:
    """
    Provides methods and an inferface for producing the deductive closure
    of a graph under OWL-RL semantics. WARNING this may take a long time

    Uses the Allegrograph reasoning implementation
    """

    def __init__(self, load_brick=True):
        """
        Creates a new OWLRL Inference session

        Args:
            load_brick (bool): if True, load Brick ontology into the graph
        """
        self.g = Graph(load_brick=load_brick)

        self._client = docker.from_env()
        containers = self._client.containers.list(all=True)
        print(f"Checking {len(containers)} containers")
        for c in containers:
            if c.name != 'agraph':
                continue
            if c.status == 'running':
                print(f"Killing running agraph")
                c.kill()
            print(f"Removing old agraph")
            c.remove()
            break

    def _setup_input(self, g):
        """
        Add our serialized graph to an in-memory tar file
        that we can send to Docker
        """
        g.serialize('input.ttl', format='turtle')
        tarbytes = io.BytesIO()
        tar = tarfile.open(name='out.tar', mode='w', fileobj=tarbytes)
        tar.add('input.ttl', arcname='input.ttl')
        tar.close()
        # seek to beginning so our file is not empty when docker sees it
        tarbytes.seek(0)
        return tarbytes

    def expand(self, graph):
        """
        Applies OWLRL reasoning from the Python owlrl library to the graph

        Args:
            graph (brickschema.graph.Graph): a Graph object containing triples

        Returns:
            graph (brickschema.graph.Graph): a Graph object containing the
                inferred triples in addition to the regular graph
        """
        def check_error(res):
            exit_code, message = res
            if exit_code > 0:
                print(f"Non-zero exit code {exit_code} with message {message}")

        for triple in graph:
            self.g.add(triple)
        # setup connection to docker
        tar = self._setup_input(self.g)
        # TODO: temporary name so we can have more than one running?
        agraph = self._client.containers.run("franzinc/agraph", name="agraph",
                                             detach=True, shm_size='1G')
        if not agraph.put_archive('/opt', tar):
            print("Could not add input.ttl to docker container")
        check_error(agraph.exec_run("chown -R agraph /opt"))
        check_error(agraph.exec_run("/app/agraph/bin/agload test \
/opt/input.ttl", user='agraph'))
        check_error(agraph.exec_run("/app/agraph/bin/agmaterialize test \
--rule all", user='agraph'))
        check_error(agraph.exec_run("/app/agraph/bin/agexport -o turtle test\
 /opt/output.ttl", user='agraph'))
        bits, stat = agraph.get_archive('/opt/output.ttl')
        with open('output.ttl.tar', 'wb') as f:
            for chunk in bits:
                f.write(chunk)
        tar = tarfile.open('output.ttl.tar')
        tar.extractall()
        tar.close()

        agraph.stop()
        agraph.remove()
        self.g.parse('output.ttl', format='ttl')
        return _return_correct_type(graph, self.g)

    @property
    def triples(self):
        return self.g.triples


class InverseEdgeInferenceSession:
    """
    Provides methods and an inferface for producing the deductive closure
    of a graph that adds all properties implied by owl:inverseOf
    """

    def __init__(self, load_brick=True):
        """
        Creates a new OWLRL Inference session

        Args:
            load_brick (bool): if True, load Brick ontology into the graph
        """
        self.g = Graph(load_brick=load_brick)

    def expand(self, graph):
        """
        Adds inverse predicates to the graph that are modeled
        with OWL.inverseOf

        Args:
            graph (brickschema.graph.Graph): a Graph object containing triples

        Returns:
            graph (brickschema.graph.Graph): a Graph object containing the
                inferred triples in addition to the regular graph
        """
        for triple in graph:
            self.g.add(triple)
        # inverse relationships
        query = """
        INSERT {
            ?o ?invprop ?s
        } WHERE {
            ?s ?prop ?o.
            ?prop owl:inverseOf ?invprop.
        }
        """
        self.g.g.update(query)
        return _return_correct_type(graph, self.g)


def _to_tag_case(x):
    """
    Returns the string in "tag case" where the first letter
    is capitalized

    Args:
        x (str): input string
    Returns:
        x (str): transformed string
    """
    return x[0].upper() + x[1:]


def _return_correct_type(input_graph, output_graph):
    """
    Returns the correct type of output_graph (rdflib.Graph or
    brickschema.Graph) depending on the type of input_graph
    """
    if isinstance(input_graph, rdflib.Graph):
        return output_graph.g
    else:
        return output_graph
