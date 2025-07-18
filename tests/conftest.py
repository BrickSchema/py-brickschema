import pytest
from ontoenv import OntoEnv, Config
import brickschema
from rdflib import RDF, RDFS, BRICK, OWL, Namespace

QUDT = Namespace("http://qudt.org/schema/qudt/")

# using code from https://docs.pytest.org/en/latest/example/simple.html


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


def pytest_generate_tests(metafunc):
    """
    Generates Brick tests for a variety of contexts
    """

    # validates that example files pass validation
    if "inference_backend" in metafunc.fixturenames:
        metafunc.parametrize("inference_backend", ["owlrl", "allegro", "reasonable"])


@pytest.fixture()
def brick_with_imports():
    cfg = Config([], strict=False, offline=False, temporary=True)
    env = OntoEnv(cfg)
    # TODO: need to add rdflib graph to the environment directly
    g = brickschema.Graph(load_brick=True)
    g.bind("qudt", QUDT)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("brick", BRICK)
    imported = env.import_dependencies(g, fetch_missing=True, recursion_depth=1)
    print(f"Imported {len(imported)} dependencies into the Brick graph.: {imported}")
    g.serialize("/tmp/brick_with_imports.ttl", format="turtle")
    return g
