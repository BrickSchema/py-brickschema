# Brick Ontology Python package

![Build](https://github.com/BrickSchema/py-brickschema/workflows/Build/badge.svg)
[![Documentation Status](https://readthedocs.org/projects/brickschema/badge/?version=latest)](https://brickschema.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/brickschema.svg)](https://badge.fury.io/py/brickschema)

Documentation available at [readthedocs](https://brickschema.readthedocs.io/en/latest/)

## Installation

The `brickschema` package requires Python >= 3.11. It can be installed with `pip`:

```
pip install brickschema
```

`brickschema` ships two OWL 2 RL reasoners, both installed by default:

- [reasonable](https://reasonable.gtf.fyi) is a fast OWL 2 RL reasoner written in
  Rust. It is the default backend.
- [OWLRL](https://pypi.org/project/owlrl/) is a pure-Python implementation. It
  delivers correct results but performs poorly on large or complex ontologies
  (we have observed minutes to hours).

Pick one explicitly with the `backend` argument to `expand`:

```python
g.expand("owlrl")                      # reasonable (default)
g.expand("owlrl", backend="owlrl")     # pure-Python
```

## Quickstart

The main `Graph` object is just a subclass of the excellent [RDFlib Graph](https://rdflib.readthedocs.io/en/stable/) library, so all features on `rdflib.Graph` will also work here.

Brief overview of the main features of the `brickschema` package:

```python
import brickschema

# creates a new rdflib.Graph with a recent version of the Brick ontology
# preloaded.
g = brickschema.Graph(load_brick=True)
# OR use the absolute latest Brick:
# g = brickschema.Graph(load_brick_nightly=True)
# OR create from an existing model
# g = brickschema.Graph(load_brick=True).from_haystack(...)

# load in data files from your file system
g.load_file("mbuilding.ttl")
# ...or by URL (using rdflib)
g.parse("https://brickschema.org/ttl/soda_brick.ttl", format="ttl")

# perform reasoning on the graph (edits in-place)
g.expand(profile="owlrl")
g.compile() # applies SHACL-AF rules; infers Brick classes from Brick tags

# validate your Brick graph against built-in shapes (or add your own)
valid, _, resultsText = g.validate()
if not valid:
    print("Graph is not valid!")
    print(resultsText)

# perform SPARQL queries on the graph
res = g.query("""SELECT ?afs ?afsp ?vav WHERE  {
    ?afs    a       brick:Air_Flow_Sensor .
    ?afsp   a       brick:Air_Flow_Setpoint .
    ?afs    brick:isPointOf ?vav .
    ?afsp   brick:isPointOf ?vav .
    ?vav    a   brick:VAV
}""")
for row in res:
    print(row)

# start a blocking web server with an interface for performing
# reasoning + querying functions
g.serve("localhost:8080")
# now visit in http://localhost:8080
```

## Features

`brickschema` supports a number of optional features:

- `[all]`: install all features below
- `[brickify]`: install the `brickify` command for converting metadata from existing sources
- `[web]`: allow serving of Brick models over HTTP + web interface
- `[merge]`: initial support for merging Brick models with different identifiers together
- `[persistence]`: support for saving and loading Brick models to/from disk
- `[orm]`: SQLAlchemy ORM over a Brick model
- `[networkx]`: export a Brick model as a NetworkX digraph
- `[bacnet]`: scan a BACnet network into a Brick model
- `[topquadrant]`: use the TopQuadrant SHACL engine

The `shifty` and `pyshacl` SHACL engines and both OWL 2 RL reasoners
(`reasonable` and `owlrl`) are installed by default, so no extra is needed for
validation, `compile()` or `expand()`.

### Inference

`brickschema` makes it easier to employ reasoning on your graphs. Simply call the `expand` method on the Graph object with one of the following profiles:
- `"rdfs"`: RDFS reasoning
- `"owlrl"`: OWL-RL reasoning (using 1 of 3 implementations below)
- `"vbis"`: add VBIS tags to Brick entities

SHACL-AF rules (which is how Brick infers classes from tags, among other
things) are applied with `compile()` rather than `expand()`:

```python
g.compile()                      # uses the default engine
g.compile(engine="pyshacl")      # or name one explicitly
```


```python
from brickschema import Graph

g = Graph(load_brick=True)
g.load_file("test.ttl")
g.expand(profile="owlrl")
print(f"Inferred graph has {len(g)} triples")
```


For the `owlrl` profile the package defaults to the fastest available
implementation, `reasonable`.
- OWLRL (default, native Python implementation): `pip install brickschema`

To use a specific reasoner, specify `"reasonable"` or `"owlrl"` as the value for the `backend` argument to `graph.expand`.

### Haystack Translation

`brickschema` can produce a Brick model from a JSON export of a Haystack model.
Then you can use this package as follows:

```python
import json
from brickschema import Graph
model = json.load(open("haystack-export.json"))
g = Graph(load_brick=True).from_haystack("http://project-haystack.org/carytown#", model)
points = g.query("""SELECT ?point ?type WHERE {
    ?point rdf:type/rdfs:subClassOf* brick:Point .
    ?point rdf:type ?type
}""")
print(points)
```

### VBIS Translation

`brickschema` can add [VBIS](https://vbis.com.au/) tags to a Brick model easily

```python
from brickschema import Graph
g = Graph(load_brick=True)
g.load_file("mybuilding.ttl")
g.expand(profile="vbis")

vbis_tags = g.query("""SELECT ?equip ?vbistag WHERE {
    ?equip  <https://brickschema.org/schema/1.1/Brick/alignments/vbis#hasVBISTag> ?vbistag
}""")
```

### Web-based Interaction

`brickschema` now supports interacting with a Graph object in a web browser. Executing `g.serve(<http address>)` on a graph object from your Python script or interpreter will start a webserver listening (by default) at http://localhost:8080 . This uses [Yasgui](https://yasgui.triply.cc/) to provide a simple web interface supporting SPARQL queries and inference.

To use this feature, install `brickschema` with the `web` feature enabled:

```
pip install brickschema[web]
```

### Brick model validation

`validate()` checks a model against the Brick shapes bundled in the graph plus
any shapes you supply. It does not modify the graph.

```python
from brickschema import Graph

g = Graph(load_brick=True)
g.load_file('myBuilding.ttl')
valid, _, _ = g.validate()
print(f"Graph is valid? {valid}")

# validating using externally-defined shapes
external = Graph()
external.load_file("other_shapes.ttl")
valid, _, report = g.validate(extra_graphs=[external])
print(f"Graph is valid? {valid}")
```

### SHACL engines

Both `validate()` and `compile()` are backed by a pluggable SHACL engine,
selected with the `engine=` keyword. When you do not name one, the first
installed engine from this list is used:

| engine | package | notes |
| --- | --- | --- |
| `"shifty"` | `pyshifty` (installed by default) | default; Rust SHACL/SHACL-AF engine, runs rules to a fixed point |
| `"topquadrant"` | `brickschema[topquadrant]` | TopQuadrant's Java implementation |
| `"pyshacl"` | `pyshacl` (installed by default) | pure-Python reference implementation |

```python
valid, _, report = g.validate(engine="pyshacl")
g.compile(engine="shifty")
```

`min_iterations` and `max_iterations` bound how many rule passes are made; they
apply to the `pyshacl` and `topquadrant` engines only, since `shifty` always
runs to a fixed point.

## `Brickify`

To use `brickify`, install `brickschema` with the `[brickify]` feature enabled:

```
pip install brickschema[brickify]
```

**Usage**:

```console
$ brickify [OPTIONS] SOURCE
```

**Arguments**:

* `SOURCE`: Path/URL to the source file  [required]

**Options**:

* `--input-type TEXT`: Supported input types: rac, table, rdf, haystack-v4
* `--brick PATH`: Brick.ttl
* `--config PATH`: Custom configuration file
* `--output PATH`: Path to the output file
* `--serialization-format TEXT`: Supported serialization formats: turtle, xml, n3, nt, pretty-xml, trix, trig and nquads  [default: turtle]
* `--minify / --no-minify`: Remove inferable triples  [default: False]
* `--input-format TEXT`: Supported input formats: xls, csv, tsv, url, turtle, xml, n3, nt, pretty-xml, trix, trig and nquads  [default: turtle]
* `--building-prefix TEXT`: Prefix for the building namespace  [default: bldg]
* `--building-namespace TEXT`: The building namespace  [default: https://example.com/bldg#]
* `--site-prefix TEXT`: Prefix for the site namespace  [default: site]
* `--site-namespace TEXT`: The site namespace  [default: https://example.com/site#]
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

Usage examples: [brickify](tests/data/brickify).

## Development

Brick requires Python >= 3.11. We use [pre-commit hooks](https://pre-commit.com/) to automatically run code formatters and style checkers when you commit.

Use [uv](https://docs.astral.sh/uv/) to manage packaging and dependencies. After installing uv, create the environment and install all dependencies with:

```bash
uv sync --all-extras --dev   # or: make sync
```

`uv run <command>` executes a command inside that environment, so there is no
separate activation step:

```bash
uv run python -c "import brickschema"
```

On first setup, make sure to install the pre-commit hooks for running the formatting and linting tools:

```bash
uv run pre-commit install
```

Run tests to make sure the build is not broken:

```bash
make test                      # 4 parallel workers by default
make test PYTEST_ARGS=""       # serial
```

Build the distribution artifacts with:

```bash
make build                     # uv build
```

`uv.lock` is committed and is the source of truth for the development
environment. If you change a dependency in `pyproject.toml`, refresh it with:

```bash
make lock                      # uv lock
```

The `uv-lock` pre-commit hook does this automatically, and CI runs
`uv sync --locked`, which fails if `uv.lock` and `pyproject.toml` disagree.

### Docs

Docs are written in reStructured Text. Add any packages the docs need to the `docs` dependency group in `pyproject.toml`
