#!/usr/bin/env python

import brickschema
import sys

if len(sys.argv) > 1:
    brick_file = sys.argv[1]
else:
    brick_file = None

sess = brickschema.inference.TagInferenceSession(
    rebuild_tag_lookup=True, brick_file=brick_file
)
sess.save_tag_lookup("brickschema/ontologies/1.5/taglookup.pickle")
