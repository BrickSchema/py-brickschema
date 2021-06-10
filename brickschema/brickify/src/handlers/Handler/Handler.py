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
        """
        Handler class responsible for performing end to end conversion
        (including ingestion, translation, and clean up).

        :param source: A filepath/URL
        :param input_format: Input format of the file
        :param module_path: Path to default template files in the package ([<dot-separate-module-path>, <template-filename>])
        :param config_file: Custom conversion configuration file
        """
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
                typer.style(
                    "[ERROR] No configuration specified!",
                    fg=typer.colors.RED,
                )
            )

    def update_namespaces(
        self,
        building_prefix=None,
        building_namespace=None,
        site_prefix=None,
        site_namespace=None,
    ):
        """
        Updates prefixes and namespaces from the templates for the site and the building before conversion.

        :param building_prefix: Building prefix (default: bldg)
        :param building_namespace: Building namespace (default: https://example.com/bldg#)
        :param site_prefix: Site prefix (default: site)
        :param site_namespace: Site namespace (default: https://example.com/site#)
        """
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
        """
        Ingests the data from files to the memory. The default option
        for the base handler is to parse a source graph in the specified input format
        to self.graph.
        """
        self.graph.parse(self.source, format=rdflib.util.guess_format(self.source))

    def translate(self):
        """
        Performs SPARQL based operations sequentially over the output graph.
        """
        if not self.config["operations"]:
            return
        with progressbar(self.config["operations"]) as operations:
            for operation in operations:
                if "data" in operation:
                    query = f"INSERT DATA {{{{ {operation['data']} }}}}"
                elif "query" in operation:
                    query = operation["query"]
                if not query:
                    continue
                query = query.format_map({})
                try:
                    self.graph.update(query)
                except Exception as e:
                    print(e)
                    print(query)

    def infer(self):
        """
        In the implementations of specific handlers, this method would be overridden to perform and append data to the output graph
        based on additional inference.
        """
        pass

    def clean_up(self):
        """
        In the implementations of specific handlers, this method would be overridden to clean the graphs, remove intermediate data, etc.
        """
        pass

    def convert(self, building_prefix, building_namespace, site_prefix, site_namespace):
        """
        Performs the conversion based on the base conversion sequence. By default, it updates the namespaces,
        ingests the data, translates the data to brick primarily using SPARQL based operations, performs and adds data
        from additional inferences, cleans up the output graph.


        :param building_prefix: Building prefix (default: bldg)
        :param building_namespace: Building namespace (default: https://example.com/bldg#)
        :param site_prefix: Site prefix (default: site)
        :param site_namespace: Site namespace (default: https://example.com/site#)
        :returns: A Brick graph (rdflib.Graph)
        """
        self.update_namespaces(
            building_prefix, building_namespace, site_prefix, site_namespace
        )
        self.ingest_data()
        self.translate()
        self.infer()
        self.clean_up()
        return self.graph
