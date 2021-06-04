from pathlib import Path
from typing import Optional, List

import typer
from tabulate import tabulate

from brickschema.brickify.src.handlers.Handler.TableHandler import TableHandler
from brickschema.brickify.util import (
    get_workbook,
    find_header_row,
    cleaned_value,
    ignore_row,
)


class RACHandler(TableHandler):
    def __init__(
        self,
        source,
        input_format: Optional[str] = "xls",
        config_file: Optional[str] = None,
    ):
        """
        RACHandler is a TableHandler designed to work on Excel Workbooks (only overrides the ingestion method).
        The default template works with MetaSys RAC schedules.

        :param source: A filepath
        :param input_format: Input format (.xls)
        :param config_file: Custom conversion configuration file
        """
        module_path = (
            [
                "brickschema.brickify.src.handlers.Handler.RACHandler.conversions",
                "rac.yml",
            ]
            if not config_file
            else []
        )
        super().__init__(
            source=source,
            input_format=input_format,
            module_path=module_path,
            config_file=config_file,
        )

    def ingest_data(self):
        """
        Splits the workbook data into multiple sheets and stores the rows in a key-value based
        data model where the key is the cell's column header, and the value is the cell's cleaned value.
        """
        workbook = get_workbook(Path(self.source))
        sheets = workbook.sheets()
        table = [(index, sheet.name) for index, sheet in enumerate(sheets)]
        typer.echo(
            tabulate(table, headers=["Sheet ID", "Sheet Name"], tablefmt="pretty")
        )
        sheet_ids = typer.prompt(text="Enter the Sheet IDs", default="all")
        if sheet_ids == "all":
            sheet_ids = range(len(sheets))
        else:
            sheet_ids = [int(sheet_id.strip()) for sheet_id in sheet_ids.split(",")]
            invalid_sheet_ids = [
                str(sheet_id)
                for sheet_id in sheet_ids
                if sheet_id not in range(len(sheets))
            ]
            if invalid_sheet_ids:
                typer.echo(
                    typer.style(
                        f"[INFO] Skipping invalid sheet IDs: {', '.join(invalid_sheet_ids)}",
                        fg=typer.colors.YELLOW,
                    )
                )

        for index, sheet in enumerate(sheets):
            if index not in sheet_ids:
                continue
            header_row = find_header_row(
                sheet=sheet, header_start=self.config["header_start"]
            )
            if not header_row:
                continue
            header = sheet.row_values(header_row)
            header = cleaned_value(
                value=header, replace_dict=self.config["replace_dict"]["headers"]
            )
            header_dict = {idx: value for idx, value in enumerate(header)}
            for row_number in range(header_row + 1, sheet.nrows):
                row = sheet.row_values(row_number)
                if ignore_row(row):
                    continue
                else:
                    row_object = {
                        header_dict[key]: value for key, value in enumerate(row)
                    }
                    update_dict = {}
                    for key, value in row_object.items():
                        if "/" in key:
                            keys = key.split("/")
                            values = value.split("/")
                            for idx, k in enumerate(keys):
                                if len(values) > idx:
                                    update_dict[k] = values[idx]
                                else:
                                    update_dict[k] = None
                    row_object = {**row_object, **update_dict}
                    if row_object:
                        row_object = {
                            key: cleaned_value(
                                value,
                                replace_dict=self.config["replace_dict"]["values"],
                            )
                            for key, value in row_object.items()
                        }
                        self.data.append(row_object)
