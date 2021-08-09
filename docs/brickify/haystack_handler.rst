Haystack Handler
-----------------

The Haystack handler downloads Haystack files and converts them to Brick. It is invoked by using the ``--input-type haystack`` on the command line.
The input file is a filepath or a URL where the Haystack TTL file can be found. 

The conversion is carried out by the ``HaystackRDFInferenceSession`` method in this Python package.