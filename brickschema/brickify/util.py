"""
The util module provides helper functions used by brickify.
"""

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
    """
    Returns a cleaned value produced by doing regex replacements and elimination
    of leading or trailing whitespaces.

    :param value: List|float|string
    :param replace_dict: Key-value pairs for regex replacements
    :returns: cleaned List|float|string
    """
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
        except ValueError:
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
    """

    :param filename: Input filepath
    :returns: An XLRD Workbook object
    """
    if not filename.is_file():
        message_start = typer.style("[Error] Input file: ", fg=typer.colors.RED)
        filename = typer.style(f"{filename}", fg=typer.colors.RED, bold=True)
        message_end = typer.style(" does not exist!", fg=typer.colors.RED)
        typer.echo(message_start + filename + message_end)
        raise typer.Exit(code=1)
    else:
        try:
            workbook = open_workbook(filename=filename)
        except Exception:
            message_start = typer.style("[Error] Input file", fg=typer.colors.RED)
            filename = typer.style(f"{filename}", fg=typer.colors.RED, bold=True)
            message_end = typer.style(
                " has an unsupported format!", fg=typer.colors.RED
            )
            typer.echo(message_start + filename + message_end)
            raise typer.Exit(code=1)
        return workbook


def find_header_row(sheet, header_start):
    """
    Finds the header row number in a sheet of an XLRD Workbook.

    :param sheet: Input sheet
    :param header_start: Header pattern (a substring of the first header)
    :return: Row number for the header row
    """
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
    """

    :param row: Input row
    :return: True
    """
    return is_empty_row(row[:2])


def ignore_row(row):
    """
    Finds out if a row should be ignored. based based on the presence of data in all the
    required table columns.

    :param row: Input row
    :return: True if the row is a title row or doesn't have data, otherwise False
    """
    return is_title_row(row) or is_not_data(row) or is_empty_row(row)


def not_important(row, required_fields):
    """
    Finds out if a row is important based based on the presence of data in all the
    required table columns.

    :param row: Input row
    :param required_fields: List of indices of required fields
    :rtype: bool
    """
    return all([value for index, value in enumerate(row) if index in required_fields])


def get_required(header):
    """
    Returns a list of column indices that contain the substring "required".

    :param header: List of column headers
    :return: List of column indices
    """
    return [
        index for index, value in enumerate(header) if "(required)" in value.lower()
    ]


def bind_namespaces(graph, namespace_prefixes: Dict[str, str]):
    """
    Binds namespace prefixes to an rdflib Graph.

    :param graph: Input graph (rdflib.Graph)
    :param namespace_prefixes: A dictionary of key-value pairs {"prefixA": "namespaceA", ...}
    """
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("owl", OWL)
    for prefix, namespace in namespace_prefixes.items():
        graph.bind(prefix, Namespace(namespace))


def minify_graph(graph, brick_file):
    """
    Compresses the output graph by removing inferable triples.

    :param graph: Input graph (rdflib.Graph)
    :param brick_file: Brick.ttl filepath/URL to use as a reference
    """
    original = len(graph)
    brick = Graph()
    if not brick_file:
        typer.echo(
            typer.style(
                "[INFO] Loading the latest nightly release of brick",
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
            f"[INFO] Total triples generated: {minified}",
            fg=typer.colors.GREEN,
        )
    )


def load_config(fp, filename: str):
    """
    Parses and returns the conversion configuration from JSON/YAML files.

    :param fp: file pointer
    :param filename: filename (used to identify which parser to use)

    :returns: dict
    """
    filename = str(filename)
    if filename.endswith(".json"):
        return json.load(fp)
    elif filename.endswith(".yml"):
        return yaml.load(fp, Loader=yaml.FullLoader)
    else:
        typer.echo(
            typer.style(
                "[WARN] '.json' and '.yml' configurations are supported.",
                fg=typer.colors.YELLOW,
            )
        )
        return {}
