"""
Internal dispatch layer for the SHACL engines that back
:meth:`brickschema.graph.BrickBase.compile` and
:meth:`brickschema.graph.BrickBase.validate`.

Three engines are supported:

- ``shifty``: the default. A Rust SHACL/SHACL-AF implementation exposed by the
  ``pyshifty`` package. Runs rules to a fixed point internally, so the
  ``min_iterations``/``max_iterations`` knobs do not apply to it.
- ``topquadrant``: TopQuadrant's Java implementation, via ``brick-tq-shacl``.
- ``pyshacl``: the pure-Python implementation. Always available, since
  ``pyshacl`` is a hard dependency.

Every engine is normalized behind :func:`infer` and :func:`validate` so that
callers do not have to care which one they got:

- :func:`infer` returns *only the newly inferred triples* as a plain
  ``rdflib.Graph``. It never mutates its inputs.
- :func:`validate` returns the ``(conforms, results_graph, results_text)``
  triple that pyshacl established as the de-facto interface.
"""
import importlib.util
import logging
from typing import List, Optional, Tuple

import rdflib

logger = logging.getLogger(__name__)

#: Engines in the order they are picked when the caller does not name one.
ENGINE_PREFERENCE = ("shifty", "topquadrant", "pyshacl")

#: Import name that has to be present for an engine to be usable.
_ENGINE_MODULE = {
    "shifty": "shifty",
    "topquadrant": "brick_tq_shacl",
    "pyshacl": "pyshacl",
}

#: what to pip install to get each engine, for error messages.
_ENGINE_EXTRA = {
    "shifty": "pyshifty",
    "topquadrant": "brickschema[topquadrant]",
    "pyshacl": "pyshacl",
}


def is_available(engine: str) -> bool:
    """Returns True if the named engine's backing package can be imported."""
    module = _ENGINE_MODULE.get(engine)
    if module is None:
        return False
    return importlib.util.find_spec(module) is not None


def available_engines() -> List[str]:
    """Returns the installed engines, in preference order."""
    return [e for e in ENGINE_PREFERENCE if is_available(e)]


def resolve(engine: Optional[str]) -> str:
    """
    Turns the caller's ``engine`` argument into the name of an engine that is
    actually installed.

    Passing ``None`` selects the first installed engine in
    :data:`ENGINE_PREFERENCE` (shifty, then topquadrant, then pyshacl).
    Naming an engine explicitly is honored, and is an error if that engine is
    unknown or not installed -- silently substituting a different engine would
    hide the fact that the caller did not get the semantics they asked for.

    Args:
        engine (str or None): requested engine name

    Returns:
        engine (str): name of an installed engine

    Raises:
        ValueError: if ``engine`` is not a known engine name
        ImportError: if ``engine`` is known but not installed
    """
    if engine is None:
        for candidate in ENGINE_PREFERENCE:
            if is_available(candidate):
                return candidate
        # pyshacl is a hard dependency, so this should be unreachable
        raise ImportError(
            "No SHACL engine is installed. Install one with "
            f"'pip install {_ENGINE_EXTRA['shifty']}'."
        )

    if engine not in _ENGINE_MODULE:
        raise ValueError(
            f"Unknown SHACL engine {engine!r}. "
            f"Choose one of {', '.join(ENGINE_PREFERENCE)}."
        )
    if not is_available(engine):
        raise ImportError(
            f"SHACL engine {engine!r} requires the {_ENGINE_MODULE[engine]} "
            f"package. Install it with 'pip install {_ENGINE_EXTRA[engine]}'."
        )
    return engine


def _as_graph(graph: rdflib.Graph) -> rdflib.Graph:
    """
    Copies the triples of ``graph`` into a plain ``rdflib.Graph``.

    The engines take a single graph of triples. Passing them a ``Dataset`` or
    ``ConjunctiveGraph`` (which ``GraphCollection`` and
    ``VersionedGraphCollection`` are) is not well defined, and ``Graph``
    subclasses can carry ``__init__`` requirements that ``skolemize()`` and
    friends do not know how to satisfy. Flattening first sidesteps both.
    """
    flat = rdflib.Graph()
    for triple in graph.triples((None, None, None)):
        flat.add(triple)
    for prefix, namespace in graph.namespaces():
        flat.bind(prefix, namespace)
    return flat


def infer(
    data_graph: rdflib.Graph,
    ontologies: Optional[rdflib.Graph] = None,
    engine: Optional[str] = None,
    min_iterations: int = 1,
    max_iterations: int = 10,
) -> rdflib.Graph:
    """
    Applies SHACL-AF rules and returns *only the triples they inferred*.

    Neither ``data_graph`` nor ``ontologies`` is modified.

    Args:
        data_graph (rdflib.Graph): the graph to run rules over
        ontologies (rdflib.Graph): extra ontology/shape definitions. May be
            None or empty, in which case the shapes are expected to live in
            ``data_graph``.
        engine (str): which engine to use; see :func:`resolve`
        min_iterations (int): minimum rule passes; pyshacl and topquadrant only
        max_iterations (int): maximum rule passes; pyshacl and topquadrant only

    Returns:
        inferred (rdflib.Graph): the newly inferred triples
    """
    engine = resolve(engine)
    data = _as_graph(data_graph)
    onts = _as_graph(ontologies) if ontologies is not None else rdflib.Graph()

    if engine == "shifty":
        return _shifty_infer(data, onts)
    if engine == "topquadrant":
        return _topquadrant_infer(data, onts, min_iterations, max_iterations)
    return _pyshacl_infer(data, onts, min_iterations, max_iterations)


def _shifty_infer(data: rdflib.Graph, onts: rdflib.Graph) -> rdflib.Graph:
    import shifty

    # shifty round-trips its result through N-Triples, which mints fresh labels
    # for every blank node. Diffing that result against the input would report
    # every blank-node triple in the input as "new", so `compile` would graft a
    # relabeled duplicate of each one into the graph on every call -- and the
    # Brick ontology is full of blank nodes (every `sh:rule [ ... ]`).
    # Skolemizing first gives the blank nodes stable IRIs that survive the
    # round-trip, so the diff below sees only genuinely new triples.
    skolemized = data.skolemize()
    result = shifty.infer(skolemized, onts if len(onts) else None)
    for message in result.diagnostics:
        logger.warning("shifty: %s", message)
    return result.graph().de_skolemize() - data


def _topquadrant_infer(
    data: rdflib.Graph,
    onts: rdflib.Graph,
    min_iterations: int,
    max_iterations: int,
) -> rdflib.Graph:
    from brick_tq_shacl import infer as tq_infer

    result = tq_infer(
        data, onts, min_iterations=min_iterations, max_iterations=max_iterations
    )
    return result - data - onts


def _pyshacl_infer(
    data: rdflib.Graph,
    onts: rdflib.Graph,
    min_iterations: int,
    max_iterations: int,
) -> rdflib.Graph:
    import pyshacl

    max_iterations = max(max_iterations, min_iterations)
    # pyshacl has no rules-only entry point: it applies sh:rule as a side
    # effect of validating with advanced=True and inplace=True, and it only
    # does one pass per call, so drive it to a fixed point here.
    skolemized = data.skolemize()
    combined = skolemized + onts
    for i in range(max_iterations):
        old_size = len(combined)
        conforms, _, report = pyshacl.validate(
            data_graph=combined,
            advanced=True,
            allow_warnings=True,
            abort_on_first=True,
            inplace=True,
        )
        if not conforms:
            logger.debug("pyshacl reported violations while applying rules:\n%s", report)
        if (i + 1) >= min_iterations and len(combined) == old_size:
            break
    return (combined - skolemized - onts).de_skolemize()


def validate(
    data_graph: rdflib.Graph,
    shapes: Optional[rdflib.Graph] = None,
    engine: Optional[str] = None,
    min_iterations: int = 1,
    max_iterations: int = 10,
) -> Tuple[bool, rdflib.Graph, str]:
    """
    Validates ``data_graph`` against ``shapes`` plus any shapes embedded in the
    data graph itself. Neither graph is modified.

    Args:
        data_graph (rdflib.Graph): the graph to validate
        shapes (rdflib.Graph): extra shape/ontology definitions; may be None
        engine (str): which engine to use; see :func:`resolve`
        min_iterations (int): minimum rule passes; pyshacl and topquadrant only
        max_iterations (int): maximum rule passes; pyshacl and topquadrant only

    Returns:
        (conforms, results_graph, results_text)
    """
    engine = resolve(engine)
    data = _as_graph(data_graph)
    shapes = _as_graph(shapes) if shapes is not None else rdflib.Graph()

    if engine == "shifty":
        import shifty

        # Brick ships shapes whose severity is sh:Warning and which are
        # expected to fire on valid models, so only violations count against
        # conformance. This is the counterpart of pyshacl's allow_warnings.
        return shifty.validate(
            data,
            shapes if len(shapes) else None,
            minimum_severity="violation",
        )

    if engine == "topquadrant":
        from brick_tq_shacl import validate as tq_validate

        return tq_validate(
            data,
            shapes,
            min_iterations=min_iterations,
            max_iterations=max_iterations,
        )

    import pyshacl

    # pyshacl does not chain sh:rule into validation the way shifty and
    # topquadrant do, so apply the rules first to put it on equal footing.
    combined = data + shapes
    combined += _pyshacl_infer(data, shapes, min_iterations, max_iterations)
    return pyshacl.validate(
        combined.skolemize(),
        advanced=True,
        abort_on_first=True,
        allow_warnings=True,
    )
