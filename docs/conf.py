# This will fail if ossapi's dependencies aren't installed.
# Which shouldn't be an issue because the only people running ``make html``
# (building the docs) are people with ossapi properly installed, hopefully.
from ossapi import __version__

project = "ossapi"
author = "Liam DeVoe"
release = "v" + __version__
version = "v" + __version__
master_doc = "index"

# show eg ProfilePage instead of ossapi.enums.ProfilePage on appendix page
add_module_names = False
nitpicky = True
autodoc_typehints = "description"
# disable alphabetical ordering
autodoc_member_order = "bysource"

html_show_copyright = False
html_show_sphinx = False

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "slider": ("https://llllllllll.github.io/slider/", None),
    "circleguard": ("https://circleguard.github.io/circlecore/", None),
}

html_theme = "furo"

# custom css to disable furo's fancy scrolling behavior, see
# https://github.com/pradyunsg/furo/discussions/384#discussioncomment-2249243
html_css_files = ["custom.css"]
html_static_path = ["_static"]


# linebreak workaround documented here
# https://stackoverflow.com/a/9664844/12164878

rst_prolog = """
.. |br| raw:: html

   <br />
"""
