import csv
import re
import traceback
from pathlib import Path
from typing import Optional, List

from jinja2 import Template
from typer import progressbar

from brickschema.brickify.src.handlers.Handler.Handler import Handler
from brickschema.brickify.util import cleaned_value


class TableHandler(Handler):
    def __init__(
        self,
        source,
        input_format: Optional[str] = "csv",
        module_path: Optional[List[str]] = None,
        config_file: Optional[Path] = None,
    ):
        """
        A handler designed specifically to deal with tabular data (overrides ingestion and translations methods only).

        :param source: A filepath
        :param input_format: Input format of the file (supports csv, tsv by default)
        :param module_path: Path to default template files in the package ([<dot-separate-module-path>, <template-filename>])
        :param config_file: Custom conversion configuration file
        """
        super().__init__(
            source=source,
            input_format=input_format,
            module_path=module_path,
            config_file=config_file,
        )
        self.data = []
        self.dialect = "excel"
        if input_format == "tsv":
            self.dialect = "excel-tab"

    def ingest_data(self):
        """
        Ingests tabular data into a key-value based data model where the key is the column header, and value is
        the cleaned cell value.
        """
        with open(self.source, newline="") as csv_file:
            reader = csv.DictReader(csv_file, dialect=self.dialect)
            for row in reader:
                replace_dict = (
                    self.config["replace_dict"]["values"]
                    if "replace_dict" in self.config
                    and "values" in self.config["replace_dict"]
                    else {}
                )
                item = {
                    key.strip(): cleaned_value(
                        value,
                        replace_dict=replace_dict,
                    )
                    for key, value in row.items()
                }
                self.data.append(item)

    def translate(self):
        """
        Translates the ingested flattened data to triples, into the output graph.
        """
        if "macros" in self.config:
            macros = "\n".join(self.config["macros"])
        else:
            macros = ""
        with progressbar(self.data) as data:
            for item in data:
                query = None
                for operation in self.config["operations"]:
                    args_finder = re.compile(r"{([^(?!{}).*$]*?)\}")
                    if "template" in operation:
                        template_string = operation["template"]
                        if macros:
                            template_string = macros + "\n" + template_string
                        template = Template(template_string)
                        query = f"INSERT DATA {{{{ {template.render(value=item)} }}}}"
                    elif "data" in operation:
                        query = f"INSERT DATA {{{{ {operation['data']} }}}}"
                    elif "query" in operation:
                        query = operation["query"]
                    if not query:
                        continue
                    args = args_finder.findall(query)
                    args = [arg.strip() for arg in args if arg.strip()]
                    args_list = list(set([arg.strip() for arg in args])) or []
                    if "conditions" in operation:
                        try:
                            conditions = [
                                eval(condition.format_map(item))
                                for condition in operation["conditions"]
                            ]
                            conditions = cleaned_value(conditions)
                        except KeyError as e:
                            print(e)
                            traceback.print_exc()
                            conditions = [False]
                    else:
                        conditions = []
                    if all([arg in item.keys() for arg in args_list] + conditions):
                        query_str = query.format_map(item)
                        try:
                            self.graph.update(query_str)
                        except Exception as e:
                            print(e)
                            print(query_str)
                            traceback.print_exc()
                            exit(1)
