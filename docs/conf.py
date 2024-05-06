# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# Terminal shortcuts to rebuild the documentation:  
# (cd /Users/work/Desktop/Controls\ Tests; sphinx-apidoc -o docs pyopticon --separate; cd docs; make html)

# Imports
import sys, os
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pyopticon'
copyright = '2023, Richard Randall'
author = 'Richard Randall'
release = '0.2.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.autosummary',
              'sphinx_rtd_theme']
autodoc_member_order='bysource'

autodoc_default_flags=['members']
autosummary_generate=True

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Suppress some warnings
# suppress_warnings = ['toc','autoapi']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
