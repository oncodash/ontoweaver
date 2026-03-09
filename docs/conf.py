def get_version_from_pyproject():
    from pathlib import Path
    import toml

    version = "unknown"
    # adopt path to your pyproject.toml
    pyproject_toml_file = Path("../pyproject.toml")
    print(pyproject_toml_file)
    if pyproject_toml_file.exists() and pyproject_toml_file.is_file():
        data = toml.load(pyproject_toml_file)
        # check project.version
        if "project" in data and "version" in data["project"]:
            version = data["project"]["version"]
        else:
            raise RuntimeError("No version tag found")
    else:
        raise RuntimeError("pyproject.toml not found")
    return version

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'OntoWeaver'
author = 'Johann Dreo, Marko Baric, Claire Laudy, Matthieu Najm, Benno Schwikowski'
release = get_version_from_pyproject()

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
import os
import sys
sys.path.insert(0, os.path.abspath('../src/'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.autosummary',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.graphviz',
]

autosummary_generate = True
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'undoc-members': True,
}

autoclass_content = 'both'

templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "biocypher-log/"]

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = [
    "css/custom.css",
]

# Adds a logo to the navbar.
html_logo = 'OntoWeaver_logo__big.svg'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'

html_theme_options = {
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    'vcs_pageview_mode': 'view',
    'version_selector': True,
    'navigation_depth': 3,
}

html_context = {
    "display_github": True, # Integrate GitHub
    "github_user": "oncodash", # Username
    "github_repo": "ontoweaver", # Repo name
    "github_version": "main", # Version
    "conf_py_path": "/docs/", # Path in the checkout to the docs root
}

html_show_sphinx = False
project_copyright = f"%Y: Johann Dreo, Marko Baric, Matthieu Najm, Claire Laudy — license CC-BY-SA⁴. Documentation for OntoWeaver version {get_version_from_pyproject()}"

