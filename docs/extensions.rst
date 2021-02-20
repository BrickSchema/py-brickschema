Extensions and Alignments
=========================

The module makes it simple to list and load in extensions to the Brick schema, in addition to the alignments between Brick and other ontologies. These extensions are distributed as Turtle files on the `Brick GitHub repository`_, but they are also pre-loaded into the `brickschema` module.

.. _`Brick GitHub repository`: https://github.com/BrickSchema/Brick/

Listing and Loading Extensions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Extensions provide additional class definitions, rules and other augmentations to the Brick ontology.

.. code-block:: python

  from brickschema import Graph

  g = Graph()
  # returns a list of extensions
  g.get_extensions()
  # => ['shacl_tag_inference']

  # loads the contents of the extension into the graph
  g.load_extension('shacl_tag_inference')
  # with this particular extension, you can now infer Brick
  # classes from the tags associated with entities
  g.expand("shacl")


Listing and Loading Alignments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Alignments define the nature of Brick's relationship to other RDF-based ontologies. For example, the Building Topology Ontology defines several location classes that are similar to Brick's; the alignment between BOT and Brick allows graphs defined in one language to be understood in the other.

Several Brick alignments are packaged with the `brickschema` module. These can be listed and dynamically loaded into a graph

.. code-block:: python

  from brickschema import Graph

  g = Graph()
  # returns a list of alignments
  g.get_alignments()
  # => ['VBIS', 'REC', 'BOT']

  # loads the contents of the alignment file into the graph
  g.load_alignment('BOT')
  # good idea to run a reasoner after loading in the extension
  # so that the implied information is filled out
  g.expand("owlrl")
