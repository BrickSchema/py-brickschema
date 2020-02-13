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

## Haystack Inference

Requires a JSON export of a Haystack model
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

## SQL ORM

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
