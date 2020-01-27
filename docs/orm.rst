Brick ORM
=========

Currently, the ORM models Locations, Points and Equipment and the
basic relationships between them.

Please see the `SQLAlchemy docs`_ for detailed information on how to interact with the ORM. use the
``orm.session`` instance variable to interact with the ORM connection.

See `querying docs`_ for how to use the SQLalchemy querying mechanisms

.. _`SQLAlchemy docs`: https://docs.sqlalchemy.org/en/13/
.. _`querying docs`: https://docs.sqlalchemy.org/en/13/orm/tutorial.html#querying

Example
~~~~~~~

.. code-block:: python

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
