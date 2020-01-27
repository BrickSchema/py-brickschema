#!/usr/bin/env python

import brickschema
import shutil

sess = brickschema.inference.TagInferenceSession(rebuild_tag_lookup=True)
shutil.copyfile('taglookup.pickle', 'brickschema/ontologies/taglookup.pickle')
