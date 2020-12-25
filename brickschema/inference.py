import logging
import itertools
import shutil
import csv
import re
import pkgutil
import io
import pickle
from collections import defaultdict
from .namespaces import BRICK, A, RDFS
from rdflib import Namespace, Literal
from .tagmap import tagmap
import rdflib
import owlrl
import tarfile

class OWLRLNaiveInferenceSession:
    """
    Provides methods and an inferface for producing the deductive closure
    of a graph under OWL-RL semantics. WARNING this may take a long time
    """

    def expand(self, graph):
        """
        Applies OWLRL reasoning from the Python owlrl library to the graph

        Args:
            graph (brickschema.graph.Graph): a Graph object containing triples
        """
        owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(graph)

class OWLRLReasonableInferenceSession:
    """
    Provides methods and an inferface for producing the deductive closure
    of a graph under OWL-RL semantics. WARNING this may take a long time
    """

    def __init__(self):
        """
        Creates a new OWLRL Inference session
        """
        try:
            from reasonable import PyReasoner
        except ImportError:
            raise ImportError(
                "'reasonable' package not found. Install\
support for the reasonable Reasoner with 'pip install brickschema[reasonable].\
Currently only works on Linux and MacOS"
            )
        self.r = PyReasoner()

    def expand(self, graph):
        """
        Applies OWLRL reasoning from the Python reasonable library to the graph

        Args:
            graph (brickschema.graph.Graph): a Graph object containing triples
        """
        self.r.from_graph(graph)
        triples = self.r.reason()
        graph.add(*triples)


class OWLRLAllegroInferenceSession:
    """
    Provides methods and an inferface for producing the deductive closure
    of a graph under OWL-RL semantics. WARNING this may take a long time

    Uses the Allegrograph reasoning implementation
    """

    def __init__(self):
        """
        Creates a new OWLRL Inference session backed by the Allegrograph
        reasoner (https://franz.com/agraph/support/documentation/current/materializer.html).
        Requires the docker package to work; recommended method of installing
        is to use the 'allegro' option with pip:
            pip install brickschema[allegro]
        """

        try:
            import docker
        except ImportError:
            raise ImportError(
                "'docker' package not found. Install support \
for Allegro with 'pip install brickschema[allegro]"
            )

        self._client = docker.from_env(version="auto")
        containers = self._client.containers.list(all=True)
        print(f"Checking {len(containers)} containers")
        for c in containers:
            if c.name != "agraph":
                continue
            if c.status == "running":
                print("Killing running agraph")
                c.kill()
            print("Removing old agraph")
            c.remove(v=True)
            break

    def _setup_input(self, g):
        """
        Add our serialized graph to an in-memory tar file
        that we can send to Docker
        """
        g.g.serialize("input.ttl", format="turtle")
        tarbytes = io.BytesIO()
        tar = tarfile.open(name="out.tar", mode="w", fileobj=tarbytes)
        tar.add("input.ttl", arcname="input.ttl")
        tar.close()
        # seek to beginning so our file is not empty when docker sees it
        tarbytes.seek(0)
        return tarbytes

    def expand(self, graph):
        """
        Applies OWLRL reasoning from the Python owlrl library to the graph

        Args:
            graph (brickschema.graph.Graph): a Graph object containing triples
        """
        def check_error(res):
            exit_code, message = res
            if exit_code > 0:
                print(f"Non-zero exit code {exit_code} with message {message}")

        # setup connection to docker
        tar = self._setup_input(graph)
        # TODO: temporary name so we can have more than one running?
        agraph = self._client.containers.run(
            "franzinc/agraph:v7.0.0", name="agraph", detach=True, shm_size="1G"
        )
        if not agraph.put_archive("/tmp", tar):
            print("Could not add input.ttl to docker container")
        check_error(agraph.exec_run("chown -R agraph /tmp", user="root"))
        check_error(
            agraph.exec_run(
                "/agraph/bin/agraph-control --config /agraph/etc/agraph.cfg start",
                user="agraph",
            )
        )
        check_error(
            agraph.exec_run(
                "/agraph/bin/agload test \
/tmp/input.ttl",
                user="agraph",
            )
        )
        check_error(
            agraph.exec_run(
                "/agraph/bin/agmaterialize test \
--rule all",
                user="agraph",
            )
        )
        check_error(
            agraph.exec_run(
                "/agraph/bin/agexport -o turtle test\
 /tmp/output.ttl",
                user="agraph",
            )
        )
        bits, stat = agraph.get_archive("/tmp/output.ttl")
        with open("output.ttl.tar", "wb") as f:
            for chunk in bits:
                f.write(chunk)
        tar = tarfile.open("output.ttl.tar")
        tar.extractall()
        tar.close()

        agraph.stop()
        agraph.remove(v=True)
        graph.load_file("output.ttl")

        # cleanup
        shutil.rm('output.ttl')
        shutil.rm('output.ttl.tar')
        shutil.rm('input.ttl')


class VBISTagInferenceSession:
    """
    Add appropriate VBIS tag annotations to the entities inside the provided Brick model

    Algorithm:
    - get all Equipment entities in the Brick model (VBIs currently only deals w/ equip)

    Args:
        alignment_file (str): use the given Brick/VBIS alignment file. Defaults to a
                pre-packaged version.
        master_list_file (str): use the given VBIS tag master list. Defaults to a
                pre-packaged version.

    Returns:
        A VBISTagInferenceSession object
    """

    def __init__(self, alignment_file=None, master_list_file=None):
        self._alignment_file = alignment_file
        self._master_list_file = master_list_file

    def expand(self, graph):
        """
        Args:
            graph (brickschema.graph.Graph): a Graph object containing triples
        """

        ALIGN = Namespace("https://brickschema.org/schema/1.1/Brick/alignments/vbis#")

        if self._alignment_file is None:
            data = pkgutil.get_data(
                __name__, "ontologies/Brick-VBIS-alignment.ttl"
            ).decode()
            graph.parse(source=io.StringIO(data), format="ttl")
        else:
            graph.load_file(alignment_file)

        if master_list_file is None:
            data = pkgutil.get_data(__name__, "ontologies/vbis-masterlist.csv").decode()
            master_list_file = io.StringIO(data)
        else:
            master_list_file = open(master_list_file)

        # query the graph for all VBIS patterns that are linked to Brick classes
        # Build a lookup table from the results
        self._pattern2class = defaultdict(list)
        self._class2pattern = {}
        res = graph.query(
            """SELECT ?class ?vbispat WHERE {
            ?shape  a   sh:NodeShape .
            ?shape  sh:targetClass  ?class .
            { ?shape  sh:property/sh:pattern ?vbispat }
            UNION
            { ?shape  sh:or/rdf:rest*/rdf:first/sh:pattern ?vbispat }
        }"""
        )
        for row in res:
            brickclass, vbispattern = row
            self._pattern2class[vbispattern].append(brickclass)
            self._class2pattern[brickclass] = vbispattern

        # Build a lookup table of VBIS pattern -> VBIS tag. The VBIS patterns
        # used as keys are from the above lookup table, so they all correspond
        # to a Brick class
        self._pattern2vbistag = defaultdict(list)
        rdr = csv.DictReader(master_list_file)
        for row in rdr:
            for pattern in self._pattern2class.keys():
                if re.match(pattern, row["VBIS Tag"]):
                    self._pattern2vbistag[pattern].append(row["VBIS Tag"])
        master_list_file.close()

        equip_and_shape = graph.query(
            """SELECT ?equip ?class ?shape WHERE {
             ?class rdfs:subClassOf* brick:Equipment .
             ?equip rdf:type ?class .
             ?shape sh:targetClass ?class .
        }"""
        )
        equips = set([row[0] for row in equip_and_shape])
        for equip in equips:
            rows = [row for row in equip_and_shape if row[0] == equip]
            classes = set([row[1] for row in rows])
            brickclass = self._filter_to_most_specific(graph, classes)
            applicable_vbis = self._pattern2vbistag[self._class2pattern[brickclass]]
            if len(applicable_vbis) == 1:
                graph.add((equip, ALIGN.hasVBISTag, Literal(applicable_vbis[0])))
            elif len(applicable_vbis) > 1:
                common_pfx = _get_common_prefix(applicable_vbis)
                graph.add((equip, ALIGN.hasVBISTag, Literal(common_pfx)))
            else:
                logging.info(f"No VBIS tags found for {equip} with type {brickclass}")

    def _filter_to_most_specific(self, graph, classlist):
        """
        Given a list of Brick classes (rdflib.URIRef), return the most specific one
        (the one that is not a superclass of the others)
        """
        candidates = {}
        for brickclass in classlist:
            sc_query = f"SELECT ?subclass WHERE {{ ?subclass rdfs:subClassOf+ <{brickclass}> }}"
            subclasses = set([x[0] for x in graph.query(sc_query)])
            # if there are NO subclasses of 'brickclass', then it is specific
            if len(subclasses) == 0:
                candidates[brickclass] = 0
                continue
            # 'subclasses' are the subclasses of 'brickclass'. If any of these appear in
            # 'classlist', then we know that 'brickclass' is not the most specific
            intersection = set(classlist).intersection(subclasses)
            if len(intersection) == 1 and brickclass in intersection:
                candidates[brickclass] = 1
            else:
                candidates[brickclass] = len(intersection)
        most_specific = None
        mincount = float("inf")
        for specific, score in candidates.items():
            if score < mincount:
                most_specific = specific
                mincount = score
        return most_specific

    def lookup_brick_class(self, vbistag):
        """
        Returns all Brick classes that are appropriate for the given VBIS tag

        Args:
            vbistag (str): the VBIS tag  that we want to retrieve Brick classes for. Pattern search
                is not supported yet
        Returns:
            brick_classes (list of rdflib.URIRef): list of the Brick classes that match the VBIS tag
        """
        if "*" in vbistag:
            raise Exception("Pattern search not supported in current release")
        classes = set()
        for pattern, brickclasses in self._pattern2class.items():
            if re.match(pattern, vbistag):
                classes.update(brickclasses)
        return list(classes)


def _get_common_prefix(list_of_strings):
    """
    Returns the longest common prefix among the set of strings.
    Helpful for finding a VBIS tag prefix.

    Args:
        list_of_strings (list of str): list of strings
    Returns:
        pfx (str): longest common prefix
    """
    # https://stackoverflow.com/questions/6718196/determine-prefix-from-a-set-of-similar-strings
    def all_same(x):
        return all(x[0] == y for y in x)

    char_tuples = zip(*list_of_strings)
    prefix_tuples = itertools.takewhile(all_same, char_tuples)
    return "".join(x[0] for x in prefix_tuples).strip("-")


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
