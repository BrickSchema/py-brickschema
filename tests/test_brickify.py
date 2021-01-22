from brickschema.brickify.main import convert
from rdflib import Graph
from brickschema.namespaces import BRICK
from typer.testing import CliRunner
from brickschema.brickify.main import app

runner = CliRunner()


def test_rac():
    result = runner.invoke(app, ["data/brickify/RAC/rac.xls", "--input-type", "rac"], input="\n")
    print(result.stdout)
    assert result.exit_code == 0


def test_haystack_ttl():
    result = runner.invoke(app, ["https://project-haystack.dev/example/download/charlie.ttl", "--input-type", "haystack-v4"])
    print(result.stdout)
    assert result.exit_code == 0


def test_jinja2():
    result = runner.invoke(app, ["data/brickify/jinja2/sheet.csv", "--input-type", "csv", "--config", "data/brickify/jinja2/template.yml"])
    print(result.stdout)
    assert result.exit_code == 0

