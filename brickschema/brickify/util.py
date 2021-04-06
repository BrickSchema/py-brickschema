import json
import re
from pathlib import Path
from typing import Optional, Dict

import click_spinner
import typer
import yaml
from rdflib import Namespace, OWL, RDF, RDFS, Graph
from xlrd import open_workbook


def cleaned_value(value, replace_dict: Optional[Dict] = {}):
    if type(value) == float:
        return int(value) if str(value)[-2:] == ".0" else value
    if type(value) == list:
        return [cleaned_value(item, replace_dict) for item in value]
    clean_value = value
    if type(value) == str:
        try:
            if "." in value:
                return float(value)
            return int(value)
        except:
            pass
        if value in ["TRUE", "true", "True", "on", "ON"]:
            return True
        if value in ["FALSE", "false", "False", "off", "OFF"]:
            return False
        for replacement in replace_dict.items():
            clean_value = re.sub(*replacement, clean_value)
        return clean_value.strip()
    return clean_value


def get_workbook(filename: Path):
    if not filename.is_file():
        message_start = typer.style(f"[Error] Input file: ", fg=typer.colors.RED)
        filename = typer.style(f"{filename}", fg=typer.colors.RED, bold=True)
        message_end = typer.style(f" does not exist!", fg=typer.colors.RED)
        typer.echo(message_start + filename + message_end)
        raise typer.Exit(code=1)
    else:
        try:
            workbook = open_workbook(filename=filename)
        except Exception:
            message_start = typer.style(f"[Error] Input file", fg=typer.colors.RED)
            filename = typer.style(f"{filename}", fg=typer.colors.RED, bold=True)
            message_end = typer.style(
                f" has an unsupported format!", fg=typer.colors.RED
            )
            typer.echo(message_start + filename + message_end)
            raise typer.Exit(code=1)
        return workbook


def find_header_row(sheet, header_start):
    row_number = 0
    for row in sheet.get_rows():
        if header_start in str(row[0]):
            return row_number
        row_number += 1
    return None


def is_title_row(row):
    return is_empty_row(row[1:])


def is_empty_row(row):
    return not any(row)


def is_not_data(row):
    return is_empty_row(row[:2])


def ignore_row(row):
    return is_title_row(row) or is_not_data(row) or is_empty_row(row)


def not_important(row, required_fields):
    return all([value for index, value in enumerate(row) if index in required_fields])


def get_required(header):
    return [
        index for index, value in enumerate(header) if "(required)" in value.lower()
    ]


def bind_namespaces(graph, namespace_prefixes):
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("owl", OWL)
    for prefix, namespace in namespace_prefixes.items():
        graph.bind(prefix, Namespace(namespace))


def minify_graph(graph, brick_file):
    original = len(graph)
    brick = Graph()
    if not brick_file:
        typer.echo(
            typer.style(
                f"[INFO] Loading the latest nightly release of brick",
                fg=typer.colors.YELLOW,
            )
        )
        with click_spinner.spinner():
            brick.load(
                "https://github.com/BrickSchema/Brick/releases/download/nightly/Brick.ttl",
                format="turtle",
            )
    else:
        brick.load(str(brick_file), format="turtle")
    graph += brick
    graph.update(
        """
    DELETE { 
        ?instance a ?type .
    }
    WHERE {
        ?instance a ?type .
        ?instance a ?subtype .
        ?subtype (rdfs:subClassOf|owl:equivalentClass)+ ?type .
    }
    """
    )
    graph -= brick
    minified = len(graph)
    typer.echo(
        typer.style(
            f"[INFO] Inferable triples removed: {original - minified} ",
            fg=typer.colors.GREEN,
        )
    )
    typer.echo(
        typer.style(
            f"[INFO] Total triples generated: {minified}", fg=typer.colors.GREEN,
        )
    )


def load_config(fp, filename):
    filename = str(filename)
    if ".json" in filename:
        return json.load(fp)
    if ".yml" in filename:
        return yaml.load(fp, Loader=yaml.FullLoader)
