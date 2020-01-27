import sys
sys.path.append('../')

import brickschema

version = brickschema.__version__

master_doc = 'index'

extensions = [
    # 'sphinx.ext.autodoc',
    'readthedocs_ext.readthedocs',
    'sphinx.ext.napoleon',
    # 'recommonmark'
]

napoleon_google_docstring = True

source_suffix = {
    '.rst': 'restructuredtext',
    # '.md': 'markdown',
}

exclude_patterns = ["conftest.py", 'README.md']

github_doc_root = 'https://github.com/Brickschema/py-brickschema/tree/master/doc/'

# def setup(app):
#     app.add_config_value('recommonmark_config', {
#             'url_resolver': lambda url: github_doc_root + url,
#             # 'auto_toc_tree_section': 'Contents',
#             'enable_eval_rst': True,
#             'enable_inline_math': True,
#             'enable_auto_toc_tree': True,
#             }, True)
    # app.add_transform(AutoStructify)
#     app.connect('autodoc-process-docstring', docstring)
#
# # def docstring(app, what, name, obj, options, lines):
# #     md  = '\n'.join(lines)
# #     rst = m2r.convert(md)
# #     lines.clear()
#     for line in rst.splitlines():
#         lines.append(line)
