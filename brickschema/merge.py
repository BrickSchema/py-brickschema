"""
The `merge` module implements data integration methods for merging Brick graphs
together. This is based on techniques described in 'Shepherding Metadata Through
the Building Lifecycle' published in BuildSys 2020
"""
from rdflib import URIRef
from collections import defaultdict
import dedupe
from .graph import Graph
from .namespaces import BRICK

DEBUG = False


def unify_entities(G, e1, e2):
    """
    Replaces all instances of e2 with e1 in graph G
    """
    print(f"Unifying {e1} and {e2}")
    e1 = URIRef(e1)
    e2 = URIRef(e2)
    pos = G.predicate_objects(subject=e2)
    for (p, o) in pos:
        G.remove((e2, p, o))
        G.add((e1, p, o))

    sps = G.subject_predicates(object=e2)
    for (s, p) in sps:
        G.remove((s, p, e2))
        G.add((s, p, e1))


def get_entity_feature_vectors(g, namespace):
    """
    Returns a dictionary of features for each entity in graph 'g'.

    Entities are any node with at least one `rdf:type` edge that is in the given namespace.
    """
    entities = g.query(
        f"""SELECT ?ent ?type ?label WHERE {{
        ?ent rdf:type ?type .
        OPTIONAL {{ ?ent rdfs:label ?label }} .
        FILTER(STRSTARTS(STR(?ent), STR(<{namespace}>)))
    }}"""
    )
    features = defaultdict(lambda: defaultdict(set))
    for row in entities:
        entity, etype, label = row
        features[str(entity)]["type"].add(str(etype))
        features[str(entity)]["label"].add(str(label))
        features[str(entity)]["uri"].add(str(entity))

    if DEBUG:
        for ent, featurelist in features.items():
            print(ent)
            for name, vals in featurelist.items():
                print(f"   {name} = {vals}")

    return features


def flatten_features(features):
    for _, flist in features.items():
        for k, v in flist.items():
            if isinstance(v, (list, set)):
                flist[k] = list(v)[0]


def cluster_by_type(g1, g2, namespace):
    clusters = defaultdict(lambda: {"g1": {}, "g2": {}})
    g1_features = get_entity_feature_vectors(g1, namespace)
    g2_features = get_entity_feature_vectors(g2, namespace)
    for g1_ent, g1_ent_feat in g1_features.items():
        for etype in g1_ent_feat["type"]:
            flat_features = g1_ent_feat.copy()
            flat_features["type"] = etype
            clusters[etype]["g1"][g1_ent] = flat_features

    for g2_ent, g2_ent_feat in g2_features.items():
        for etype in g2_ent_feat["type"]:
            flat_features = g2_ent_feat.copy()
            flat_features["type"] = etype
            clusters[etype]["g2"][g2_ent] = flat_features

    if DEBUG:
        for ent_type, cluster in clusters.items():
            print(ent_type)
            print("   ", cluster["g1"].keys())
            print("   ", cluster["g2"].keys())
            print()

    return clusters


def merge_type_cluster(g1, g2, namespace, similarity_threshold=0.9, merge_types=None):
    merge_types = list(map(str, get_common_types(g1, g2, namespace)))
    _g1 = Graph(load_brick_nightly=True).from_triples(g1.triples((None, None, None)))
    _g1.expand("brick")

    _g2 = Graph(load_brick_nightly=True).from_triples(g2.triples((None, None, None)))
    _g2.expand("brick")
    clusters = cluster_by_type(_g1, _g2, namespace)

    G = g1 + g2

    linked = set()
    for etype, cluster in clusters.items():
        if merge_types and etype not in merge_types:
            continue
        print(f"Handling clusters for {etype}")
        # if not same # of entities in both clusters,
        # then type alignment will be less successful
        for e in linked:
            if e in cluster["g1"]:
                cluster["g1"].pop(e)
            if e in cluster["g2"]:
                cluster["g2"].pop(e)
        if not len(cluster["g1"]) or not len(cluster["g2"]):
            continue
        g1_features = cluster["g1"].copy()
        g2_features = cluster["g2"].copy()
        flatten_features(g1_features)
        flatten_features(g2_features)
        fields = [
            # {"field": "uri", "type": "String"},
            {"field": "type", "type": "String"},
            {"field": "label", "type": "String"},
        ]
        linker = dedupe.RecordLink(fields)

        linker.prepare_training(g1_features, g2_features)
        dedupe.console_label(linker)
        linker.train()
        linked_records = linker.join(g1_features, g2_features, 0.0)
        for link in linked_records:
            (e1, e2), similarity = link
            if similarity < similarity_threshold:
                print(
                    f"cannot merge {e1}, {e2} due to similarity threshold {similarity} < {similarity_threshold}"
                )
                continue
            linked.add(e1)
            linked.add(e2)
            unify_entities(G, e1, e2)
    return G


def merge_record_linkage(g1, g2, namespace):
    g1_features = get_entity_feature_vectors(g1, namespace)
    g2_features = get_entity_feature_vectors(g2, namespace)

    flatten_features(g1_features)
    flatten_features(g2_features)

    fields = [
        {"field": "uri", "type": "String"},
        {"field": "type", "type": "String"},
        {"field": "label", "type": "String"},
    ]
    linker = dedupe.RecordLink(fields)

    linker.prepare_training(g2_features, g1_features)
    dedupe.console_label(linker)
    linker.train()
    linked_records = linker.join(g1_features, g2_features, 0.0)
    print(linked_records)


def get_common_types(g1, g2, namespace):
    """
    Returns the list of types that are common to both graphs. A type is included
    if both graphs have instances of that type
    """
    g1ents = g1.query(
        f"""SELECT DISTINCT ?type WHERE {{
        ?ent rdf:type ?type .
        FILTER(STRSTARTS(STR(?ent), STR(<{namespace}>)))
    }}"""
    )

    g2ents = g2.query(
        f"""SELECT DISTINCT ?type WHERE {{
        ?ent rdf:type ?type .
        FILTER(STRSTARTS(STR(?ent), STR(<{namespace}>)))
    }}"""
    )

    g1types = set([x[0] for x in g1ents])
    g2types = set([x[0] for x in g2ents])
    return list(g1types.intersection(g2types))
