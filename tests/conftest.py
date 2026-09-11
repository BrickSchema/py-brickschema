import importlib.util

import pytest
from ontoenv import OntoEnv
import brickschema
from brickschema import shacl
from rdflib import RDF, RDFS, BRICK, OWL, Namespace

QUDT = Namespace("http://qudt.org/schema/qudt/")

# using code from https://docs.pytest.org/en/latest/example/simple.html


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


#: backend name -> module that has to be importable for it to work
_OWLRL_BACKEND_MODULE = {
    "owlrl": "owlrl",
    "allegrograph": "docker",
    "reasonable": "reasonable",
}


def _docker_is_usable():
    """
    The allegrograph backend runs the reasoner in a container, so having the
    'docker' package installed is not enough -- under `uv sync --all-extras`
    it always is. The daemon has to be reachable too.
    """
    try:
        import docker

        docker.from_env(version="auto").ping()
    except Exception:
        return False
    return True


@pytest.fixture(params=list(_OWLRL_BACKEND_MODULE))
def owlrl_inference_backend(request):
    """
    Parametrizes tests over the OWL-RL backends, skipping any whose optional
    dependency is unavailable.
    """
    module = _OWLRL_BACKEND_MODULE[request.param]
    if importlib.util.find_spec(module) is None:
        pytest.skip(f"{module} not installed; skipping {request.param} backend")
    if request.param == "allegrograph" and not _docker_is_usable():
        pytest.skip("docker daemon not reachable; skipping allegrograph backend")
    return request.param


@pytest.fixture(scope="session")
def brick_with_imports():
    env = OntoEnv(strict=False, offline=False, temporary=True)
    # TODO: need to add rdflib graph to the environment directly
    g = brickschema.Graph(load_brick=True)
    g.bind("qudt", QUDT)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("brick", BRICK)
    env.import_dependencies(g, fetch_missing=True, recursion_depth=1)
    return g


@pytest.fixture(params=list(shacl.ENGINE_PREFERENCE))
def shacl_engine(request):
    """
    Parametrizes tests over every SHACL engine, skipping the ones whose
    optional dependency is not installed.
    """
    if not shacl.is_available(request.param):
        pytest.skip(f"{request.param} engine not installed")
    return request.param
