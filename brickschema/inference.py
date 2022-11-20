import logging
import time
import tempfile
import itertools
import csv
import secrets
import re
import pkgutil
import io
import pickle
from collections import defaultdict
from .namespaces import BRICK, A, RDFS
import rdflib
from .tagmap import tagmap
import owlrl
import tarfile

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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

        try:
            self._client = docker.from_env(version="auto")
        except Exception as e:
            logger.error(
                f"Could not connect to docker ({e}); defaulting to naive evaluation"
            )
            raise ConnectionError(e)
        self._container_name = f"agraph-{secrets.token_hex(8)}"
        logger.info(f"container will be {self._container_name}")

    def _setup_input(self, g):
        """
        Add our serialized graph to an in-memory tar file
        that we can send to Docker
        """
        tarbytes = io.BytesIO()
        with tempfile.NamedTemporaryFile() as f:
            g.serialize(f.name, format="turtle")
            tar = tarfile.open(name="out.tar", mode="w", fileobj=tarbytes)
            tar.add(f.name, arcname="input.ttl")
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
            exit_code == int(exit_code)
            if exit_code == 0:
                return
            elif exit_code == 1:  # critical
                raise Exception(
                    f"Non-zero exit code {exit_code} with message {message}"
                )
            elif exit_code == 2:  # problematic, but can continue
                logging.error(f"Non-zero exit code {exit_code} with message {message}")

        logger.debug("setup inputs to docker + connection")
        # setup connection to docker
        tar = self._setup_input(graph)
        logger.debug("run agraph container")
        agraph = self._client.containers.run(
            "franzinc/agraph:v7.1.0",
            name=self._container_name,
            detach=True,
            shm_size="1G",
            remove=True,
        )
        logger.debug("should be started; copying input to container")
        if not agraph.put_archive("/tmp", tar):
            print("Could not add input.ttl to docker container")
        check_error(agraph.exec_run("chown -R agraph /tmp", user="root"))

        # wait until agraph.cfg is created
        logger.debug("checking agraph cfg")
        exit_code, _ = agraph.exec_run("ls /agraph/etc/agraph.cfg")
        while exit_code > 0:
            time.sleep(1)
            exit_code, _ = agraph.exec_run("ls /agraph/etc/agraph.cfg")
        logger.debug("cfg should exist; starting server")

        exit_code, _ = agraph.exec_run(
            "/agraph/bin/agraph-control --config /agraph/etc/agraph.cfg status"
        )
        while exit_code > 0:
            time.sleep(1)
            exit_code, _ = agraph.exec_run(
                "/agraph/bin/agraph-control --config /agraph/etc/agraph.cfg status"
            )

        # check_error(
        #    agraph.exec_run(
        #        "/agraph/bin/agraph-control --config /agraph/etc/agraph.cfg start",
        #        user="agraph",
        #    )
        # )
        check_error(
            agraph.exec_run(
                "/agraph/bin/agload test \
/tmp/input.ttl",
                user="agraph",
            ),
        )
        check_error(
            agraph.exec_run(
                "/agraph/bin/agtool materialize test \
--rule all --bulk",
                user="agraph",
            ),
        )
        check_error(
            agraph.exec_run(
                "/agraph/bin/agexport -o turtle test\
 /tmp/output.ttl",
                user="agraph",
            )
        )
        logger.debug("retrieving archive")
        bits, _ = agraph.get_archive("/tmp/output.ttl")

        with tempfile.NamedTemporaryFile() as f:
            for chunk in bits:
                f.write(chunk)
            f.seek(0)
            with tarfile.open(fileobj=f) as tar:
                out = tar.extractfile("output.ttl")
                graph.parse(out, format="ttl")
                # tar.extractall()

        logger.debug("stopping container + removing")
        # container will automatically remove when stopped
        agraph.stop()


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
        brick_version (string): the MAJOR.MINOR version of the Brick ontology
            to load into the graph. Only takes effect for the load_brick argument

    Returns:
        A VBISTagInferenceSession object
    """

    def __init__(self, alignment_file=None, master_list_file=None, brick_version="1.3"):
        self._alignment_file = alignment_file
        self._master_list_file = master_list_file

        from .graph import Graph

        self._graph = Graph()
        if self._alignment_file is None:
            self._graph.load_alignment("VBIS")
        else:
            self._graph.load_file(self._alignment_file)

        if self._master_list_file is None:
            data = pkgutil.get_data(
                __name__, f"ontologies/{brick_version}/vbis-masterlist.csv"
            ).decode()
            master_list_file = io.StringIO(data)
        else:
            master_list_file = open(self._master_list_file)

        # query the graph for all VBIS patterns that are linked to Brick classes
        # Build a lookup table from the results
        self._pattern2class = defaultdict(list)
        self._class2pattern = {}
        res = self._graph.query(
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

    def expand(self, graph):
        """
        Args:
            graph (brickschema.graph.Graph): a Graph object containing triples
        """

        ALIGN = rdflib.Namespace(
            f"https://brickschema.org/schema/{graph._brick_version}/Brick/alignments/vbis#"
        )
        graph += self._graph

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
                graph.add((equip, ALIGN.hasVBISTag, rdflib.Literal(applicable_vbis[0])))
            elif len(applicable_vbis) > 1:
                common_pfx = _get_common_prefix(applicable_vbis)
                graph.add((equip, ALIGN.hasVBISTag, rdflib.Literal(common_pfx)))
            else:
                logger.info(f"No VBIS tags found for {equip} with type {brickclass}")

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


class TagInferenceSession:
    """
    Provides methods and an interface for inferring Brick classes from
    sets of Brick tags. If you want to work with non-Brick tags, you
    will need to use a wrapper class (see HaystackInferenceSession)
    """

    def __init__(
        self,
        load_brick=True,
        brick_version="1.3",
        rebuild_tag_lookup=False,
        approximate=False,
        brick_file=None,
    ):
        """
        Creates new Tag Inference session
        Args:
            load_brick (bool): if True, load Brick ontology into the graph
            brick_version (string): the MAJOR.MINOR version of the Brick ontology
                to load into the graph. Only takes effect for the load_brick argument
            brick_file (str): path to a Brick ttl file to use; will replace
                the internal version of Brick if provided and will treat
                'load_brick' as False
            rebuild_tag_lookup (bool): if True, rebuild the dictionary
                used for performing the inference of tags -> classes.
                By default, uses the dictionary for the packaged Brick
                version
            approximate (bool): if True, considers a more permissive set of
                possibly related classes. If False, performs exact tag mapping
        """
        from .graph import Graph

        if brick_file is not None:
            self.g = Graph(load_brick=False)
            self.g.load_file(brick_file)
        else:
            self.g = Graph(load_brick=load_brick, brick_version=brick_version)
        self._approximate = approximate
        if rebuild_tag_lookup:
            self._make_tag_lookup()
        else:
            # get ontology data from package
            data = pkgutil.get_data(
                __name__, f"ontologies/{brick_version}/taglookup.pickle"
            )
            # TODO: move on from moving pickle to something more secure?
            self.lookup = pickle.loads(data)

    def _make_tag_lookup(self):
        """
        Builds taglookup dictionary. You shouldn't need to do this unless
        the taglookup dictionary is out of date
        """
        self.lookup = defaultdict(set)
        res = self.g.query(
            """SELECT ?class ?tag WHERE {
          ?class rdfs:subClassOf+ brick:Class.
          ?class brick:hasAssociatedTag ?tag .
          ?tag rdf:type brick:Tag
        }"""
        )
        class2tag = defaultdict(set)
        for (cname, tag) in res:
            cname = cname.split("#")[1]
            tag = tag.split("#")[1]
            class2tag[cname].add(tag)
        for cname, tagset in class2tag.items():
            self.lookup[tuple(sorted(tagset))].add(cname)
        pickle.dump(self.lookup, open("taglookup.pickle", "wb"))

    def _is_point(self, classname):
        return (
            len(
                self.g.query(
                    f"SELECT ?x WHERE {{ \
            brick:{classname} rdfs:subClassOf* brick:Point . \
            brick:{classname} a ?x }}"
                )
            )
            > 0
        )

    def _is_equip(self, classname):
        return (
            len(
                self.g.query(
                    f"SELECT ?x WHERE {{ \
            brick:{classname} rdfs:subClassOf* brick:Equipment . \
            brick:{classname} a ?x }}"
                )
            )
            > 0
        )

    def _translate_tags(self, tags):
        """"""
        output_tags = []
        for tag in tags:
            tag = tag.lower()
            if tag not in tagmap:
                output_tags.append(tag)
                continue
            output_tags.extend(tagmap[tag])
        return set(output_tags)

    def lookup_tagset(self, tagset):
        """
        Returns the Brick classes and tagsets that are supersets OR
        subsets of the given tagsets

        Args:
            tagset (list of str): a list of tags
        """
        s = set(map(_to_tag_case, tagset))
        if self._approximate:
            s.add("Point")
            withpoint = [
                (klass, set(tagset))
                for tagset, klass in self.lookup.items()
                if s.issuperset(set(tagset)) or s.issubset(set(tagset))
            ]
            s.remove("Point")
            s.add("Equipment")
            withequip = [
                (klass, set(tagset))
                for tagset, klass in self.lookup.items()
                if s.issuperset(set(tagset)) or s.issubset(set(tagset))
            ]
            s.remove("Equipment")
            s.add("Location")
            withlocation = [
                (klass, set(tagset))
                for tagset, klass in self.lookup.items()
                if s.issuperset(set(tagset)) or s.issubset(set(tagset))
            ]
            return withpoint + withequip + withlocation

        return [
            (klass, set(tagset))
            for tagset, klass in self.lookup.items()
            if s == set(tagset)
        ]

    def most_likely_tagsets(self, orig_s, num=-1):
        """
        Returns the list of likely classes for a given set of tags,
        as well as the list of tags that were 'leftover', i.e. not
        used in the inference of a class

        Args:
            tagset (list of str): a list of tags
            num (int): number of likely tagsets to be returned; -1 returns all

        Returns:
            results (tuple): a 2-element tuple containing (1)
            most_likely_classes (list of str): list of Brick classes
            and (2) leftover (set of str): list of tags not used

        """
        s = set(map(_to_tag_case, orig_s))
        tagsets = self.lookup_tagset(s)
        if len(tagsets) == 0:
            # no tags
            return [], orig_s
        # find the highest number of tags that overlap
        most_overlap = max(map(lambda x: len(s.intersection(x[1])), tagsets))

        # return the class with the fewest tags >= the overlap size
        candidates = list(
            filter(lambda x: len(s.intersection(x[1])) == most_overlap, tagsets)
        )

        # When calculating the minimum difference, we calculate it form the
        # perspective of the candidate tagsets because they will have more tags
        # We want to find the tag set(s) who has the fewest tags over what was
        # provided
        min_difference = min(map(lambda x: len(x[1].difference(s)), candidates))
        most_likely = list(
            filter(lambda x: len(x[1].difference(s)) == min_difference, candidates)
        )

        leftover = s.difference(most_likely[0][1])
        most_likely_classes = list(set([list(x[0])[0] for x in most_likely]))
        # return most likely classes (list) and leftover tags
        # (what of 'orig_s' wasn't used)
        if num < 0:
            return most_likely_classes, leftover
        else:
            return most_likely_classes[:num], leftover

    def expand(self, graph):
        """
        Infers the Brick class for entities with tags; tags are indicated
        by the `brick:hasTag` relationship.
        Args:
            graph (brickschema.graph.Graph): a Graph object containing triples
        """
        for triple in self.g:
            graph.add(triple)
        entity_tags = defaultdict(set)
        res = graph.query(
            """SELECT ?ent ?tag WHERE {
            ?ent brick:hasTag ?tag
        }"""
        )
        for ent, tag in res:
            entity_tags[ent].add(tag)
        for entity, tagset in entity_tags.items():
            tagset = list(map(lambda x: x.split("#")[-1], tagset))
            lookup = self.lookup_tagset(tagset)
            if len(lookup) == 0:
                continue
            klasses = list(lookup[0][0])
            graph.add((entity, A, BRICK[klasses[0]]))


class HaystackInferenceSession(TagInferenceSession):
    """
    Wraps TagInferenceSession to provide inference of a Brick model
    from a Haystack model. The haystack model is expected to be encoded
    as a dictionary with the keys "cols" and "rows"; I believe this is
    a standard Haystack JSON export.
    """

    def __init__(self, namespace):
        """
        Creates a new HaystackInferenceSession that infers entities into
        the given namespace
        Args:
            namespace (str): namespace into which the inferred Brick entities
                             are deposited. Should be a valid URI
        """
        super(HaystackInferenceSession, self).__init__(
            approximate=True, load_brick=True
        )
        self._generated_triples = []
        self._BLDG = rdflib.Namespace(namespace)
        self._filters = [
            lambda x: not x.startswith("his"),
            lambda x: not x.endswith("Ref"),
            lambda x: not x.startswith("cur"),
            lambda x: x != ("disMacro"),
            lambda x: x != "navName",
            lambda x: x != "tz",
            lambda x: x != "mod",
            lambda x: x != "id",
        ]
        self._point_tags = [
            "point",
            "sensor",
            "command",
            "setpoint",
            "alarm",
            "status",
            "parameter",
            "limit",
        ]

    def infer_entity(self, tagset, identifier=None, equip_ref=None):
        """
        Produces the Brick triples representing the given Haystack tag set

        Args:
            tagset (list of str): a list of tags representing a Haystack entity
            equip_ref (str): reference to an equipment if one exists

        Keyword Args:
            identifier (str): if provided, use this identifier for the entity,
            otherwise, generate a random string.
        """
        triples = []
        infer_results = []
        if identifier is None:
            raise Exception("PROVIDE IDENTIFIER")

        # handle Site
        if "site" in tagset and "equip" not in tagset and "point" not in tagset:
            triples.append((self._BLDG[identifier.replace(" ", "_")], A, BRICK.Site))
            return triples, [(identifier, list(tagset), [BRICK.Site])]

        # take into account 'equipref' to avoid unnecessarily inventing equips
        if equip_ref is not None:
            equip_entity_id = equip_ref
            inferred_equip_classes = []
        else:
            non_point_tags = set(tagset).difference(self._point_tags)
            non_point_tags.add("equip")
            inferred_equip_classes, leftover_equip = self.most_likely_tagsets(
                non_point_tags
            )
            inferred_equip_classes = [
                c for c in inferred_equip_classes if self._is_equip(c)
            ]
            equip_entity_id = identifier.replace(" ", "_") + "_equip"

        # choose first class for now
        point_entity_id = identifier.replace(" ", "_") + "_point"

        # check if this is a point; if so, infer what it is
        if set(tagset).intersection(self._point_tags):
            tagset = set(tagset).difference(set(["equip"]))
            inferred_point_classes, leftover_points = self.most_likely_tagsets(tagset)
            inferred_point_classes = [
                c for c in inferred_point_classes if self._is_point(c)
            ]
            if len(inferred_point_classes) > 0:
                triples.append(
                    (self._BLDG[point_entity_id], A, BRICK[inferred_point_classes[0]])
                )
                triples.append(
                    (
                        self._BLDG[point_entity_id],
                        RDFS.label,
                        rdflib.Literal(identifier),
                    )
                )
                infer_results.append((identifier, list(tagset), inferred_point_classes))

        if len(inferred_equip_classes) > 0:
            triples.append(
                (self._BLDG[equip_entity_id], A, BRICK[inferred_equip_classes[0]])
            )
            triples.append(
                (
                    self._BLDG[equip_entity_id],
                    BRICK.hasPoint,
                    self._BLDG[point_entity_id],
                )
            )
            triples.append(
                (
                    self._BLDG[equip_entity_id],
                    RDFS.label,
                    rdflib.Literal(identifier + " equip"),
                )
            )
            triples.append(
                (
                    self._BLDG[point_entity_id],
                    RDFS.label,
                    rdflib.Literal(identifier + " point"),
                )
            )
            infer_results.append((identifier, list(tagset), inferred_equip_classes))
        return triples, infer_results

    def _translate_tags(self, haystack_tags):
        """"""
        output_tags = []
        for tag in haystack_tags:
            tag = tag.lower()
            if tag not in tagmap:
                output_tags.append(tag)
                continue
            output_tags.extend(tagmap[tag])
        return set(output_tags)

    def infer_model(self, model):
        """
        Produces the inferred Brick model from the given Haystack model
        Args:
            model (dict): a Haystack model
        Returns:
            graph (brickschema.graph.Graph): a Graph object containing the
                inferred triples in addition to the regular graph
        """

        from .graph import Graph

        entities = model["rows"]
        # index the entities by their ID field
        entities = {e["id"].replace('"', ""): {"tags": e} for e in entities}
        # TODO: add e['dis'] for a descriptive label?
        brickgraph = Graph(load_brick=False)

        # marker tag pass
        for entity_id, entity in entities.items():
            marker_tags = {
                k for k, v in entity["tags"].items() if v == "m:" or v == "M"
            }
            for f in self._filters:
                marker_tags = list(filter(f, marker_tags))
            # translate tags
            entity_tagset = list(self._translate_tags(marker_tags))

            equip_ref = entity["tags"].get("equipRef")
            # infer tags for single entity
            triples, _ = self.infer_entity(
                entity_tagset, identifier=entity_id, equip_ref=equip_ref
            )
            brickgraph.add(*triples)
            self._generated_triples.extend(triples)

        # take a pass through for relationships
        for entity_id, entity in entities.items():
            relships = {k: v for k, v in entity["tags"].items() if k.endswith("Ref")}
            # equip_entity_id = entity_id.replace(' ', '_') + '_equip'
            point_entity_id = entity_id.replace(" ", "_") + "_point"
            if "equipRef" not in relships:
                continue
            reffed_equip = (
                relships["equipRef"].replace(" ", "_").replace('"', "") + "_equip"
            )
            if self._BLDG[point_entity_id] in brickgraph.nodes:
                triple = (
                    self._BLDG[reffed_equip],
                    BRICK.hasPoint,
                    self._BLDG[point_entity_id],
                )
                brickgraph.add(triple)
                self._generated_triples.append(triple)
        return brickgraph


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
