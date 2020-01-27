import sys
sys.path.append('../')

import brickschema

version = brickschema.__version__
master_doc = 'docs/contents'

extensions = [
    # 'sphinx.ext.autodoc',
    'readthedocs_ext.readthedocs',
    'sphinx.ext.napoleon',
]

napoleon_google_docstring = True

exclude_patterns = ["conftest.py", 'README.md']
