"""
The `inference` module implements inference of Brick entities from tags
and other representations of building metadata
"""
import pkgutil
import pickle
from collections import defaultdict
from .namespaces import BRICK, A
from rdflib import Namespace
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
        g.g.serialize('input.ttl', format='turtle')
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


class TagInferenceSession:
    """
    Provides methods and an interface for inferring Brick classes from
    sets of Brick tags. If you want to work with non-Brick tags, you
    will need to use a wrapper class (see HaystackInferenceSession)
    """

    def __init__(self, load_brick=True, rebuild_tag_lookup=False, approximate=False):
        """
        Creates new Tag Inference session
        Args:
            load_brick (bool): if True, load Brick ontology into the graph
            rebuild_tag_lookup (bool): if True, rebuild the dictionary
                used for performing the inference of tags -> classes.
                By default, uses the dictionary for the packaged Brick
                version
            approximate (bool): if True, considers a more permissive set of
                possibly related classes. If False, performs exact tag mapping
        """
        self.g = Graph(load_brick=True)
        self._approximate = approximate
        if rebuild_tag_lookup:
            self._make_tag_lookup()
        else:
            # get ontology data from package
            data = pkgutil.get_data(__name__, "ontologies/taglookup.pickle")
            # TODO: move on from moving pickle to something more secure?
            self.lookup = pickle.loads(data)

    def _make_tag_lookup(self):
        """
        Builds taglookup dictionary. You shouldn't need to do this unless
        the taglookup dictionary is out of date
        """
        self.lookup = defaultdict(set)
        res = self.g.query("""SELECT ?class ?p ?o ?restrictions WHERE {
          ?class rdfs:subClassOf+ brick:Class.
          ?class owl:equivalentClass ?restrictions.
          ?restrictions owl:intersectionOf ?inter.
          ?inter rdf:rest*/rdf:first ?node.
          {
              BIND (brick:hasTag as ?p)
              ?node owl:onProperty ?p.
              ?node owl:hasValue ?o.
          }
        }""")
        class2tag = defaultdict(set)
        for (cname, p, o, rest) in res:
            cname = cname.split('#')[1]
            o = o.split('#')[1]
            if p == BRICK.hasTag:
                class2tag[cname].add(o)
        for cname, tagset in class2tag.items():
            self.lookup[tuple(sorted(tagset))].add(cname)
        pickle.dump(self.lookup, open('taglookup.pickle', 'wb'))

    def lookup_tagset(self, tagset):
        """
        Returns the Brick classes and tagsets that are supersets OR
        subsets of the given tagsets
        Args:
            tagset (list of str): a list of tags
        """
        s = set(map(_to_tag_case, tagset))
        if self._approximate:
            return [(klass, set(tagset))
                    for tagset, klass in self.lookup.items()
                    if s.issuperset(set(tagset)) or s.issubset(set(tagset))]
        return [(klass, set(tagset)) for tagset, klass in self.lookup.items()
                if s == set(tagset)]

    def most_likely_tagsets(self, orig_s, num=-1):
        """
        Returns the list of likely classes for a given set of tags,
        as well as the list of tags that were 'leftover', i.e. not
        used in the inference of a class
        Args:
            tagset (list of str): a list of tags
            num (int): number of likely tagsets to be returned; -1 returns all
        Returns:
            most_likely_classes (list of str): list of Brick classes
            leftover (set of str): list of tags not used
        """
        s = set(map(_to_tag_case, orig_s))
        tagsets = self.lookup_tagset(s)
        if len(tagsets) == 0:
            # no tags
            return [], orig_s
        # find the highest number of tags that overlap
        most_overlap = max(map(lambda x: len(s.intersection(x[1])), tagsets))

        # return the class with the fewest tags >= the overlap size
        candidates = list(filter(lambda x:
                                 len(s.intersection(x[1])) == most_overlap,
                                 tagsets))

        # When calculating the minimum difference, we calculate it form the
        # perspective of the candidate tagsets because they will have more tags
        # We want to find the tag set(s) who has the fewest tags over what was
        # provided
        min_difference = min(map(lambda x: len(x[1].difference(s)),
                                 candidates))
        most_likely = list(filter(lambda x:
                                  len(x[1].difference(s)) == min_difference,
                                  candidates))

        leftover = s.difference(most_likely[0][1])
        most_likely_classes = [list(x[0])[0] for x in most_likely]
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
        Returns:
            graph (brickschema.graph.Graph): a Graph object containing the
                inferred triples in addition to the regular graph
        """
        for triple in graph:
            self.g.add(triple)
        entity_tags = defaultdict(set)
        res = self.g.query("""SELECT ?ent ?tag WHERE {
            ?ent brick:hasTag ?tag
        }""")
        for ent, tag in res:
            entity_tags[ent].add(tag)
        for entity, tagset in entity_tags.items():
            tagset = list(map(lambda x: x.split('#')[-1], tagset))
            lookup = self.lookup_tagset(tagset)
            if len(lookup) == 0:
                continue
            klasses = list(lookup[0][0])
            self.g.add((entity, A, BRICK[klasses[0]]))
        return _return_correct_type(graph, self.g)


class HaystackInferenceSession(TagInferenceSession):
    """
    Wraps TagInferenceSession to provide inference of a Brick model
    from a Haystack model. The haystack model is expected to be encoded
    as a dictionary with the keys "cols" and "rows"; I believe this is
    a standard Haystack JSON export.
    TODO: double check this
    """

    def __init__(self, namespace):
        """
        Creates a new HaystackInferenceSession that infers entities into
        the given namespace
        Args:
            namespace (str): namespace into which the inferred Brick entities
                             are deposited. Should be a valid URI
        """
        super(HaystackInferenceSession, self).__init__(approximate=True)
        self._BLDG = Namespace(namespace)
        self._tagmap = {
            'cmd': 'command',
            'sp': 'setpoint',
            'temp': 'temperature',
            'lights': 'lighting',
            'rtu': 'RTU',
            'ahu': 'AHU',
            'freq': 'frequency',
            'equip': 'equipment',
        }
        self._filters = [
                lambda x: not x.startswith('his'),
                lambda x: not x.endswith('Ref'),
                lambda x: not x.startswith('cur'),
                lambda x: x != ('disMacro'),
                lambda x: x != 'navName',
                lambda x: x != 'tz',
                lambda x: x != 'mod',
                lambda x: x != 'id',
                ]
        self._point_tags = ['point', 'sensor', 'command', 'setpoint', 'alarm',
                            'status', 'parameter', 'limit']

    def infer_entity(self, tagset, identifier=None):
        """
        Produces the Brick triples representing the given Haystack tag set
        Args:
            tagset (list of str): a list of tags representing a Haystack entity
        Keyword Args:
            identifier (str): if provided, use this identifier for the entity,
                              otherwise, generate a random string.
        """
        triples = []
        infer_results = []
        if identifier is None:
            raise Exception("PROVIDE IDENTIFIER")

        non_point_tags = set(tagset).difference(self._point_tags)
        non_point_tags.add('equip')
        inferred_equip_classes, leftover_equip = \
            self.most_likely_tagsets(non_point_tags)

        # choose first class for now
        equip_entity_id = identifier.replace(' ', '_') + '_equip'
        point_entity_id = identifier.replace(' ', '_') + '_point'

        # check if this is a point; if so, infer what it is
        if set(tagset).intersection(self._point_tags):
            if 'point' in tagset:
                tagset.remove('point')
            inferred_point_classes, leftover_points = \
                self.most_likely_tagsets(tagset)
            triples.append((self._BLDG[point_entity_id], A,
                            BRICK[inferred_point_classes[0]]))
            infer_results.append(
                (identifier, list(tagset), inferred_point_classes)
            )

        if len(inferred_equip_classes) > 0 and \
           inferred_equip_classes[0] != 'Equipment':
            triples.append((self._BLDG[equip_entity_id], A,
                           BRICK[inferred_equip_classes[0]]))
            triples.append((self._BLDG[equip_entity_id], BRICK.hasPoint,
                           self._BLDG[point_entity_id]))
            infer_results.append(
                (identifier, list(tagset), inferred_equip_classes)
            )
        return triples, infer_results

    def infer_model(self, model):
        """
        Produces the inferred Brick model from the given Haystack model
        Args:
            model (dict): a Haystack model
        """
        entities = model['rows']
        # index the entities by their ID field
        entities = {e['id'].replace('"', ''): {'tags': e} for e in entities}
        brickgraph = Graph(load_brick=True)

        # marker tag pass
        for entity_id, entity in entities.items():
            marker_tags = {k for k, v in entity['tags'].items()
                           if v == 'm:' or v == 'M'}
            for f in self._filters:
                marker_tags = list(filter(f, marker_tags))
            # translate tags
            entity_tagset = list(map(lambda x: self._tagmap[x.lower()]
                                     if x in self._tagmap else x, marker_tags))
            # infer tags for single entity
            triples, _ = self.infer_entity(entity_tagset, identifier=entity_id)
            brickgraph.add(*triples)

        # take a pass through for relationships
        for entity_id, entity in entities.items():
            relships = {k: v for k, v in entity['tags'].items()
                        if k.endswith('Ref')}
            # equip_entity_id = entity_id.replace(' ', '_') + '_equip'
            point_entity_id = entity_id.replace(' ', '_') + '_point'
            if 'equipRef' not in relships:
                continue
            reffed_equip = relships['equipRef'].replace(' ', '_')\
                                               .replace('"', '') + '_equip'
            if self._BLDG[point_entity_id] in brickgraph.nodes:
                brickgraph.add((self._BLDG[reffed_equip], BRICK.hasPoint,
                                self._BLDG[point_entity_id]))
        return brickgraph


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
