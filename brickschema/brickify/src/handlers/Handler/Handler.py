import re
from pathlib import Path
from typing import Optional, List

import importlib_resources
import rdflib
import typer
from typer import progressbar

from brickschema.brickify.util import bind_namespaces, load_config


class Handler:
    def __init__(
        self,
        source: Optional[str] = "input.ttl",
        input_format: Optional[str] = "turtle",
        module_path: Optional[List[str]] = None,
        config_file: Optional[Path] = None,
    ):
        self.graph = rdflib.Graph()
        self.source = source
        self.input_format = input_format
        if config_file:
            with open(config_file, "r") as config:
                self.config = load_config(config, config_file)
        elif module_path:
            config_file = module_path[-1]
            with importlib_resources.path(*module_path) as data_file:
                with open(data_file, "r") as config:
                    self.config = load_config(config, config_file)
        else:
            typer.echo(
                typer.style("[ERROR] No configuration specified!", fg=typer.colors.RED,)
            )

    def update_namespaces(
        self,
        building_prefix=None,
        building_namespace=None,
        site_prefix=None,
        site_namespace=None,
    ):
        self.config["namespace_prefixes"][building_prefix] = building_namespace
        self.config["namespace_prefixes"][site_prefix] = site_namespace
        bind_namespaces(self.graph, self.config["namespace_prefixes"])
        for operation in self.config["operations"]:
            if "query" in operation:
                operation["query"] = re.sub(
                    "bldg:", f"{building_prefix}:", operation["query"]
                )
                operation["query"] = re.sub(
                    "site:", f"{site_prefix}:", operation["query"]
                )
            if "data" in operation:
                operation["data"] = re.sub(
                    "bldg:", f"{building_prefix}:", operation["data"]
                )
                operation["data"] = re.sub(
                    "site:", f"{site_prefix}:", operation["data"]
                )
            if "template" in operation:
                operation["template"] = re.sub(
                    "bldg:", f"{building_prefix}:", operation["template"]
                )
                operation["template"] = re.sub(
                    "site:", f"{site_prefix}:", operation["template"]
                )

    def ingest_data(self):
        self.graph.parse(self.source, format=self.input_format)

    def translate(self):
        if not self.config["operations"]:
            return
        with progressbar(self.config["operations"]) as operations:
            for operation in operations:
                query = operation["query"].format_map({})
                try:
                    self.graph.update(query)
                except Exception as e:
                    print(e)
                    print(query)

    def infer(self):
        pass

    def clean_up(self):
        pass

    def convert(self, building_prefix, building_namespace, site_prefix, site_namespace):
        self.update_namespaces(
            building_prefix, building_namespace, site_prefix, site_namespace
        )
        self.ingest_data()
        self.translate()
        self.infer()
        self.clean_up()
        return self.graph
