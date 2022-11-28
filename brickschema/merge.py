"""
The `merge` module implements data integration methods for merging Brick graphs
together. This is based on techniques described in 'Shepherding Metadata Through
the Building Lifecycle' published in BuildSys 2020
"""
from colorama import init as colorama_init
from colorama import Fore, Style

from pprint import pprint
from rdflib import URIRef
from collections import defaultdict
import dedupe
from .graph import Graph
from .namespaces import BRICK
from dedupe._typing import (
    Data,
    TrainingData,
    RecordDict,
    Literal,
    RecordID,
)
import sys
from dedupe.core import unique
from dedupe.canonical import getCanonicalRep
from typing import List, Tuple, Dict, Set, Any
import itertools

colorama_init()
DEBUG = False


def _unpack_linked_records(linked_records):
    s = set()
    for (e1, e2), _ in linked_records:
        s.add(e1)
        s.add(e2)
    return s


def unify_entities(G, e1, e2):
    """
    Replaces all instances of e2 with e1 in graph G
    """
    print(Style.BRIGHT + Fore.CYAN + f"Unifying {e1} and {e2}" + Style.RESET_ALL)
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


def _merge_features(fields, g1_features, g2_features):
    while True:
        if len(g1_features) == len(g2_features) == 1:
            linked_records = (
                (list(g1_features.keys())[0], list(g2_features.keys())[0]),
                1.0,
            )
            g1_features = []
            g2_features = []
            break

        linker = dedupe.RecordLink(fields)
        linker.prepare_training(g1_features, g2_features)
        confirmed_matches = console_label(linker)
        linker.train()
        linked_records = linker.join(
            g1_features, g2_features, 0.0, constraint="one-to-one"
        )

        # remove records from linked_records that are in confirmed_matches
        for (e1, e2) in confirmed_matches:
            idx = 0
            while idx < len(linked_records):
                pair = linked_records[idx]
                for (pair, _) in linked_records:
                    if e1 in pair or e2 in pair:
                        linked_records.pop(idx)
                        break
                idx += 1

        # replace linked record scores with 1.0 if the user explicitly
        # marked them as equivalent. Then fill in other user-marked pairs
        # of linked records at the end
        idx = 0
        while idx < len(confirmed_matches):
            pair = confirmed_matches[idx]
            for lidx, (lpair, _) in enumerate(linked_records):
                if pair == lpair:
                    linked_records[lidx] = (pair, 1.0)
                    confirmed_matches.pop(idx)
                    idx -= 1  # cancel out the increment
                    break
            idx += 1
        linked_records.extend([(pair, 1.0) for pair in confirmed_matches])

        print(
            Style.BRIGHT + Fore.YELLOW + "Is this matching correct?" + Style.RESET_ALL
        )
        for (e1, e2), similarity in linked_records:
            for field in unique(field["field"] for field in fields):
                g1_val = g1_features[e1][field]
                g2_val = g2_features[e2][field]
                print(f"{g1_val:<50} | {g2_val:<50}")
            print(f"Similarity: {similarity}")
            print("-" * 20)
        ans = input(Fore.YELLOW + "[y/n]? " + Style.RESET_ALL)
        if ans.lower() == "y":
            print(
                Fore.GREEN
                + "All correct! Moving on to any stragglers"
                + Style.RESET_ALL
            )
            break
        else:
            print(Fore.RED + "Re-labeling..." + Style.RESET_ALL)
    linked_entities = _unpack_linked_records(linked_records)
    if len(linked_entities) != len(g1_features) or len(linked_entities) != len(
        g2_features
    ):
        leftover_g1 = set(g1_features.keys()).difference(linked_entities)
        leftover_g2 = set(g2_features.keys()).difference(linked_entities)
        leftover_g1 = {k: v for (k, v) in g1_features.items() if k in leftover_g1}
        leftover_g2 = {k: v for (k, v) in g2_features.items() if k in leftover_g2}
    return linked_records, leftover_g1, leftover_g2


def merge_type_cluster(g1, g2, namespace, similarity_threshold=0.9, merge_types=None):
    merge_types = list(map(str, get_common_types(g1, g2, namespace)))
    _g1 = Graph().load_file("Brick.ttl").from_triples(g1.triples((None, None, None)))
    _g1.expand("brick")

    _g2 = Graph().load_file("Brick.ttl").from_triples(g2.triples((None, None, None)))
    _g2.expand("brick")
    clusters = cluster_by_type(_g1, _g2, namespace)

    G = g1 + g2

    linked = set()
    for etype, cluster in clusters.items():
        if merge_types and etype not in merge_types:
            continue
        print(
            Style.BRIGHT
            + Fore.YELLOW
            + f"Handling clusters for {etype}"
            + Style.RESET_ALL
        )
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
            {"field": "uri", "type": "String"},
            # {"field": "type", "type": "String"},
            {"field": "label", "type": "String"},
        ]
        while True:
            linked_records, leftover_g1, leftover_g2 = _merge_features(
                fields, g1_features, g2_features
            )
            for link in linked_records:
                (e1, e2), similarity = link
                if similarity < similarity_threshold:
                    print(
                        Fore.RED
                        + f"cannot merge {e1}, {e2} due to similarity threshold {similarity} < {similarity_threshold}"
                        + Style.RESET_ALL
                    )
                    continue
                linked.add(e1)
                linked.add(e2)
                unify_entities(G, e1, e2)
            if leftover_g1 and leftover_g2 and len(leftover_g1) and len(leftover_g2):
                print(
                    Style.BRIGHT
                    + Fore.YELLOW
                    + "More entities left to merge"
                    + Style.RESET_ALL
                )
                g1_features = leftover_g1
                g2_features = leftover_g2
                continue
            break
    return G


# def merge_record_linkage(g1, g2, namespace):
#     g1_features = get_entity_feature_vectors(g1, namespace)
#     g2_features = get_entity_feature_vectors(g2, namespace)
#
#     flatten_features(g1_features)
#     flatten_features(g2_features)
#
#     fields = [
#         {"field": "uri", "type": "String"},
#         {"field": "type", "type": "String"},
#         {"field": "label", "type": "String"},
#     ]
#     linker = dedupe.RecordLink(fields)
#
#     linker.prepare_training(g2_features, g1_features)
#     dedupe.console_label(linker)
#     linker.train()
#     linked_records = linker.join(g1_features, g2_features, 0.0, constraint="one-to-one")


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


# using code from dedupe.io
def console_label(deduper: dedupe.api.ActiveMatching) -> None:  # noqa: C901
    """
    Train a matcher instance (Dedupe, RecordLink, or Gazetteer) from the command line.
    Example

    .. code:: python

       > deduper = dedupe.Dedupe(variables)
       > deduper.prepare_training(data)
       > dedupe.console_label(deduper)
    """

    confirmed_matches = []

    finished = False
    use_previous = False
    fields = unique(field.field for field in deduper.data_model.primary_fields)

    buffer_len = 1  # Max number of previous operations
    examples_buffer: List[Tuple[Any, Literal["match", "distinct", "uncertain"]]] = []
    uncertain_pairs: List[Any] = []

    # don't re-use items that are confirmed with a mapping
    mapped_items = set()

    while not finished:
        if use_previous:
            record_pair, _ = examples_buffer.pop(0)
            use_previous = False
        else:
            try:
                if not uncertain_pairs:
                    uncertain_pairs = deduper.uncertain_pairs()
                while True:
                    record_pair = uncertain_pairs.pop()
                    if (
                        len(
                            set([x["uri"] for x in record_pair]).intersection(
                                mapped_items
                            )
                        )
                        > 0
                    ):
                        examples_buffer.insert(0, (record_pair, "distinct"))
                        # TODO: do i need to process these?
                    else:
                        break
            except IndexError:
                break

        n_match = len(deduper.training_pairs["match"]) + sum(
            label == "match" for _, label in examples_buffer
        )
        n_distinct = len(deduper.training_pairs["distinct"]) + sum(
            label == "distinct" for _, label in examples_buffer
        )

        for pair in record_pair:
            for field in fields:
                line = "%s : %s" % (field, pair[field])
                print(line, file=sys.stderr)
            print(file=sys.stderr)

        print(
            "{0}/10 positive, {1}/10 negative".format(n_match, n_distinct),
            file=sys.stderr,
        )
        print(
            Fore.YELLOW + "Do these records refer to the same thing?" + Style.RESET_ALL,
            file=sys.stderr,
        )

        valid_response = False
        user_input = ""
        while not valid_response:
            if examples_buffer:
                prompt = "(y)es / (n)o / (u)nsure / (f)inished / (p)revious"
                valid_responses = {"y", "n", "u", "f", "p"}
            else:
                prompt = "(y)es / (n)o / (u)nsure / (f)inished"
                valid_responses = {"y", "n", "u", "f"}

            print(Fore.YELLOW + prompt + Style.RESET_ALL, file=sys.stderr)
            user_input = input()
            if user_input in valid_responses:
                valid_response = True

        if user_input == "y":
            examples_buffer.insert(0, (record_pair, "match"))
            mapped_items.add(record_pair[0]["uri"])
            mapped_items.add(record_pair[1]["uri"])
            confirmed_matches.append((record_pair[0]["uri"], record_pair[1]["uri"]))
            # deduper.mark_pairs({'match': record_pair})
        elif user_input == "n":
            examples_buffer.insert(0, (record_pair, "distinct"))
        elif user_input == "u":
            examples_buffer.insert(0, (record_pair, "uncertain"))
        elif user_input == "f":
            print(Fore.GREEN + "Finished labeling" + Style.RESET_ALL, file=sys.stderr)
            finished = True
        elif user_input == "p":
            use_previous = True
            uncertain_pairs.append(record_pair)

        if len(examples_buffer) > buffer_len:
            record_pair, label = examples_buffer.pop()
            if label in {"distinct", "match"}:

                examples: TrainingData
                examples = {"distinct": [], "match": []}
                examples[label].append(record_pair)  # type: ignore
                deduper.mark_pairs(examples)

    for record_pair, label in examples_buffer:
        if label in ["distinct", "match"]:

            examples: TrainingData
            examples = {"distinct": [], "match": []}
            examples[label].append(record_pair)  # type: ignore
            deduper.mark_pairs(examples)
    return confirmed_matches
