"""
The `main` module provides the CLI tool.
"""

from pathlib import Path
from warnings import warn

try:
    import typer

    from brickschema.brickify.src.handlers.Handler.Handler import Handler
    from brickschema.brickify.src.handlers.Handler.HaystackHandler.HaystackHandler import (
        HaystackHandler,
    )
    from brickschema.brickify.src.handlers.Handler.RACHandler.RACHandler import (
        RACHandler,
    )
    from brickschema.brickify.src.handlers.Handler.TableHandler import TableHandler
    from brickschema.brickify.util import minify_graph
except ImportError:
    warn(
        "brickschema needs to be installed with the 'brickify' option:\n\n\tpip install brickschema[brickify]"
    )
    import sys

    sys.exit(1)

app = typer.Typer()


@app.command(no_args_is_help=True)
def convert(
    source: str = typer.Argument(..., help="Path/URL to the source file"),
    input_type: str = typer.Option(
        help="Supported input types: rac, table, rdf, haystack-v4", default=None
    ),
    brick: Path = typer.Option(help="Brick.ttl", default=None),
    config: Path = typer.Option(help="Custom configuration file", default=None),
    output: Path = typer.Option(help="Path to the output file", default=None),
    serialization_format: str = typer.Option(
        help="Supported serialization formats: turtle, xml, n3, nt, pretty-xml, trix, trig and nquads",
        default="turtle",
    ),
    minify: bool = typer.Option(help="Remove inferable triples", default=False),
    input_format: str = typer.Option(
        help="Supported input formats: xls, csv, tsv, url, turtle, xml, n3, nt, pretty-xml, trix, trig and nquads",
        default="turtle",
    ),
    building_prefix: str = typer.Option(
        help="Prefix for the building namespace", default="bldg"
    ),
    building_namespace: str = typer.Option(
        help="The building namespace", default="https://example.com/bldg#"
    ),
    site_prefix: str = typer.Option(
        help="Prefix for the site namespace", default="site"
    ),
    site_namespace: str = typer.Option(
        help="The site namespace", default="https://example.com/site#"
    ),
):
    """
    The CLI tool uses this function to convert an input file to a Brick graph
    based on the file type and template.

    :param source: Path/URL to the source file
    :param input_type: Input file type. Supported input types: rac, table, rdf, haystack-v4
    :param brick: Path to Brick.ttl (used for minification)
    :param config: Path to custom configuration file
    :param output: Path to the output file
    :param serialization_format: Output graph format. Supported serialization formats: (turtle), xml, n3, nt, pretty-xml, trix, trig and nquads
    :param minify: Remove inferable triples?
    :param input_format: Supported input formats: xls, csv, tsv, url, turtle, xml, n3, nt, pretty-xml, trix, trig and nquads
    :param building_prefix: Prefix for the building namespace
    :param building_namespace: The building namespace
    :param site_prefix: Prefix for the site namespace
    :param site_namespace: The site namespace
    """
    if input_type in ["rac"]:
        handler = RACHandler
    elif input_type in ["haystack", "haystack-v4"]:
        handler = HaystackHandler
    elif input_type in ["table", "csv", "tsv"]:
        if input_type == "tsv":
            input_format = "tsv"
        handler = TableHandler
    elif input_type in [None, "rdf", "graph"]:
        handler = Handler
    else:
        message_start = typer.style("[Error] Input type: ", fg=typer.colors.RED)
        filename = typer.style(f"{input_type}", fg=typer.colors.RED, bold=True)
        message_end = typer.style(" not supported!", fg=typer.colors.RED)
        typer.echo(message_start + filename + message_end)
        raise typer.Exit(code=1)

    if handler:
        graph = handler(
            source=source,
            input_format=input_format,
            config_file=config,
        ).convert(building_prefix, building_namespace, site_prefix, site_namespace)

    minify_confirmed = None
    if minify is None:
        minify_confirmed = typer.confirm(
            "Do you want to remove inferable triples?", default=True
        )
    if minify or minify_confirmed:
        minify_graph(graph, brick)
    if not output:
        if source.startswith("http"):
            output = Path(source).name + ".brick.ttl"
        else:
            output = Path(source + ".brick.ttl")
    graph.serialize(destination=str(output), format=serialization_format)


if __name__ == "__main__":
    app()
