from rdflib import Graph
from typer.testing import CliRunner

from brickschema.brickify.main import app
from brickschema.brickify.main import convert
from brickschema.namespaces import BRICK

runner = CliRunner()


def test_rac():
    result = runner.invoke(
        app, ["tests/data/brickify/RAC/rac.xls", "--input-type", "rac"], input="\n"
    )
    print(result.stdout)
    assert result.exit_code == 0


def test_haystack_ttl():
    result = runner.invoke(
        app,
        [
            "https://project-haystack.org/example/download/charlie.ttl",
            "--input-type",
            "haystack-v4",
            "--output",
            "tests/data/brickify/haystack-v4/charlie.ttl.brick.ttl",
        ],
    )
    assert result.exit_code == 0, result.stdout


def test_jinja2():
    result = runner.invoke(
        app,
        [
            "tests/data/brickify/jinja2/sheet.csv",
            "--input-type",
            "csv",
            "--config",
            "tests/data/brickify/jinja2/template.yml",
        ],
    )
    print(result.stdout)
    assert result.exit_code == 0


def test_rdf():
    result = runner.invoke(
        app,
        [
            "tests/data/brickify/rdf/input.ttl",
            "--input-type",
            "rdf",
            "--config",
            "tests/data/brickify/rdf/template.yml",
        ],
    )
    print(result.stdout)
    assert result.exit_code == 0


def test_tsv():
    result = runner.invoke(
        app,
        [
            "tests/data/brickify/tsv/sheet.tsv",
            "--input-type",
            "tsv",
            "--config",
            "tests/data/brickify/tsv/template.yml",
        ],
    )
    print(result.stdout)
    assert result.exit_code == 0
