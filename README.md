# Brick Ontology Python package

[![Build Status](https://travis-ci.org/BrickSchema/py-brickschema.svg?branch=master)](https://travis-ci.org/BrickSchema/py-brickschema)
[![Documentation Status](https://readthedocs.org/projects/brickschema/badge/?version=latest)](https://brickschema.readthedocs.io/en/latest/?badge=latest)

Documentation available at [readthedocs](https://brickschema.readthedocs.io/en/latest/)

## Installation

The `brickschema` package requires Python >= 3.6. It can be installed with `pip`:

```
pip install brickschema
```

The `brickschema` package offers several installation configuration options for reasoning.
The default bundled [OWLRL](https://pypi.org/project/owlrl/) reasoner delivers correct results, but exhibits poor performance on large or complex ontologies (we have observed minutes to hours) due to its bruteforce implementation.

The [Allegro reasoner](https://franz.com/agraph/support/documentation/current/materializer.html) has better performance and implements enough of the OWLRL profile to be useful. We execute Allegrograph in a Docker container, which requires the `docker` package. To install support for the Allegrograph reasoner, use

```
pip install brickschema[allegro]
```

The [reasonable Reasoner](https://github.com/gtfierro/reasonable) offers even better performance than the Allegro reasoner, but is currently only packaged for Linux platforms. (_Note: no fundamental limitations here, just some packaging complexity due to cross-compiling the `.so`_). To install support for the reasonable Reasoner, use

```
pip install brickschema[reasonable]
```

## Features

### OWLRL Inference

`brickschema` makes it easier to employ OWLRL reasoning on your graphs. The package will automatically use the fastest available reasoning implementation for your system:

- `reasonable` (fastest, Linux-only for now): `pip install brickschema[reasonable]`
- `Allegro` (next-fastest, requires Docker): `pip install brickschema[allegro]`
- OWLRL (default, native Python implementation): `pip install brickschema`

To use OWL inference, import the `OWLRLInferenceSession` class (this automatically chooses the fastest reasoner; check out the [inference module documentation](https://brickschema.readthedocs.io/en/latest/source/brickschema.html#module-brickschema.inference) for how to use a specific reasoner). Create a `brickschema.Graph` with your ontology rules and instances loaded in and apply the reasoner's session to it:

```python
from brickschema.graph import Graph
from brickschema.namespaces import BRICK
from brickschema.inference import OWLRLInferenceSession

g = Graph(load_brick=True)
g.load_file("test.ttl")

sess = OWLRLInferenceSession()
inferred_graph = sess.expand(g)
print(f"Inferred graph has {len(inferred_graph)} triples")
```


### Haystack Inference

Requires a JSON export of a Haystack model.
First, export your Haystack model as JSON; we are using the public reference model `carytown.json`.
Then you can use this package as follows:

```python
import json
from brickschema.inference import HaystackInferenceSession
haysess = HaystackInferenceSession("http://project-haystack.org/carytown#")
model = json.load(open('carytown.json'))
model = haysess.infer_model(model)
print(len(model))

points = model.query("""SELECT ?point ?type WHERE {
    ?point rdf:type/rdfs:subClassOf* brick:Point .
    ?point rdf:type ?type
}""")
print(points)
```

### SQL ORM

```python
from brickschema.graph import Graph
from brickschema.namespaces import BRICK
from brickschema.orm import SQLORM, Location, Equipment, Point

# loads in default Brick ontology
g = Graph(load_brick=True)
# load in our model
g.load_file("test.ttl")
# put the ORM in a SQLite database file called "brick_test.db"
orm = SQLORM(g, connection_string="sqlite:///brick_test.db")

# get the points for each equipment
for equip in orm.session.query(Equipment):
    print(f"Equpiment {equip.name} is a {equip.type} with {len(equip.points)} points")
    for point in equip.points:
        print(f"    Point {point.name} has type {point.type}")
# filter for a given name or type
hvac_zones = orm.session.query(Location)\
                        .filter(Location.type==BRICK.HVAC_Zone)\
                        .all()
print(f"Model has {len(hvac_zones)} HVAC Zones")
```

## Validate with Shape Constraint Language

The module utilizes the [pySHACL](https://github.com/RDFLib/pySHACL) package to validate a building ontology
against the Brick Schema, its default constraints (shapes) and user provided shapes.

```python
from brickschema.validate import Validator
from rdflib import Graph

dataG = Graph()
dataG.parse('myBuilding.ttl', format='turtle')
shapeG = Graph()
shapeG.parse('extraShapes.ttl', format='turtle')
v = Validator()
result = v.validate(dataG, shacl_graphs=[shapeG])
print(result.textOutput)
```

* `result.conforms`:  If True, result.textOutput is `Validation Report\nConforms: True`.
* `result.textOutput`: Text output of `pyshacl.validate()`, appended with extra info that provides offender hint for each violation to help the user locate the particular violation in the data graph.  See [readthedocs](https://brickschema.readthedocs.io/en/latest/) for sample output.
* `result.violationGraphs`: List of violations, each presented as a graph.

The module provides a command
`brick_validate` similar to the `pyshacl` command.  The following command is functionally
equivalent to the code above.
```bash
brick_validate myBuilding.ttl -s extraShapes.ttl
```

## Development

Brick requires Python >= 3.6. We use [pre-commit hooks](https://pre-commit.com/) to automatically run code formatters and style checkers when you commit.

Use [Poetry](https://python-poetry.org/docs/) to manage packaging and dependencies. After installing poetry, install dependencies with:

```bash
# -D flag installs development dependencies
poetry install -D
```

Enter the development environment with the following command (this is analogous to activating a virtual environment.

```bash
poetry shell
```

On first setup, make sure to install the pre-commit hooks for running the formatting and linting tools:

```bash
# from within the environment; e.g. after running 'poetry shell'
pre-commit install
```

Run tests to make sure build is not broken

```bash
# from within the environment; e.g. after running 'poetry shell'
make test
```

### Docs

Docs are written in reStructured Text. Make sure that you add your package requirements to `docs/requirements.txt`
