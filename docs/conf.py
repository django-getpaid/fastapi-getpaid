"""Sphinx configuration for fastapi-getpaid docs."""

project = "fastapi-getpaid"
copyright = "2026, Dominik Kozaczko"
author = "Dominik Kozaczko"
version = "0.1.0"
release = "0.1.0"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build"]

html_theme = "furo"

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "fastapi": ("https://fastapi.tiangolo.com", None),
}
