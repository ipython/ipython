# IPython documentation build configuration file.

# NOTE: This file has been edited manually from the auto-generated one from
# sphinx.  Do NOT delete and re-generate.  If any changes from sphinx are
# needed, generate a scratch one and merge by hand any new fields needed.

import sys, os
from pathlib import Path

import tomllib

from sphinx_toml import load_into_locals
from intersphinx_registry import get_intersphinx_mapping
import sphinx_rtd_theme
import sphinx.util
import logging

load_into_locals(locals())
# https://read-the-docs.readthedocs.io/en/latest/faq.html
ON_RTD = os.environ.get("READTHEDOCS", None) == "True"

if ON_RTD:
    tags.add("rtd")

    # RTD doesn't use the Makefile, so re-run autogen_{things}.py here.
    for name in ("config", "api", "magics", "shortcuts"):
        fname = Path("autogen_{}.py".format(name))
        fpath = (Path(__file__).parent).joinpath("..", fname)
        with open(fpath, encoding="utf-8") as f:
            exec(
                compile(f.read(), fname, "exec"),
                {
                    "__file__": fpath,
                    "__name__": "__main__",
                },
            )

# Allow Python scripts to change behaviour during sphinx run
os.environ["IN_SPHINX_RUN"] = "True"

autodoc_type_aliases = {
    "Matcher": " IPython.core.completer.Matcher",
    "MatcherAPIv1": " IPython.core.completer.MatcherAPIv1",
}

# If your extensions are in another directory, add it here. If the directory
# is relative to the documentation root, use os.path.abspath to make it
# absolute, like shown here.
sys.path.insert(0, os.path.abspath("../sphinxext"))

# We load the ipython release info into a dict by explicit execution
iprelease = {}
exec(
    compile(
        open("../../IPython/core/release.py", encoding="utf-8").read(),
        "../../IPython/core/release.py",
        "exec",
    ),
    iprelease,
)

# General configuration
# ---------------------

# - template_path: Add any paths that contain templates here, relative to this directory.
# - master_doc: The master toctree document.
# - project
# - copyright
# - github_project_url
# - source_suffix = config["sphinx"]["source_suffix"]
# - exclude_patterns:
#       Exclude these glob-style patterns when looking for source files.
#       They are relative to the source/ directory.
# - pygments_style: The name of the Pygments (syntax highlighting) style to use.
# - default_role
# - modindex_common_prefix


intersphinx_mapping = get_intersphinx_mapping(
    packages={
        "python",
        "rpy2",
        "jupyterclient",
        "jupyter",
        "jedi",
        "traitlets",
        "ipykernel",
        "prompt_toolkit",
        "ipywidgets",
        "ipyparallel",
        "pip",
    }
)


# Options for HTML output
# -----------------------
# - html_theme
# - html_static_path
#     Add any paths that contain custom static files (such as style sheets) here,
#     relative to this directory. They are copied after the builtin static files,
#     so a file named "default.css" will overwrite the builtin "default.css".
#     Favicon needs the directory name
# - html_favicon
# - html_last_updated_fmt = config["html"]["html_last_updated_fmt"]
#     If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
#     using the given strftime format.
#     Output file base name for HTML help builder.
# - htmlhelp_basename

# Additional templates that should be rendered to pages, maps page names to
# template names.

# Options for LaTeX output
# ------------------------

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, document class [howto/manual]).
latex_documents = []


# Options for texinfo output
# --------------------------
texinfo_documents = [
    (
        master_doc,
        "ipython",
        "IPython Documentation",
        "The IPython Development Team",
        "IPython",
        "IPython Documentation",
        "Programming",
        1,
    ),
]

#########################################################################
# Custom configuration
# The default replacements for |version| and |release|, also used in various
# other places throughout the built documents.
#
# The full version, including alpha/beta/rc tags.
release = "%s" % iprelease["version"]
# Just the X.Y.Z part, no '-dev'
version = iprelease["version"].split("-", 1)[0]

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ''
# Else, today_fmt is used as the format for a strftime call.
today_fmt = "%B %d, %Y"

rst_prolog = ""


def is_stable(extra):
    for ext in {"dev", "b", "rc"}:
        if ext in extra:
            return False
    return True


if is_stable(iprelease["_version_extra"]):
    tags.add("ipystable")
    print("Adding Tag: ipystable")
else:
    tags.add("ipydev")
    print("Adding Tag: ipydev")
    rst_prolog += """
.. warning::

    This documentation covers a development version of IPython. The development
    version may differ significantly from the latest stable release.
"""

rst_prolog += """
.. important::

    This documentation covers IPython versions 6.0 and higher. Beginning with
    version 6.0, IPython stopped supporting compatibility with Python versions
    lower than 3.3 including all versions of Python 2.7.

    If you are looking for an IPython version compatible with Python 2.7,
    please use the IPython 5.x LTS release and refer to its documentation (LTS
    is the long term support release).

"""



class ConfigtraitFilter(logging.Filter):
    """
    This is a filter to remove in sphinx 3+ the error about config traits being duplicated.

    As we autogenerate configuration traits from, subclasses have lots of
    duplication and we want to silence them. Indeed we build on travis with
    warnings-as-error set to True, so those duplicate items make the build fail.
    """

    def filter(self, record):
        if (
            record.args
            and record.args[0] == "configtrait"
            and "duplicate" in record.msg
        ):
            return False
        return True


ct_filter = ConfigtraitFilter()


logger = sphinx.util.logging.getLogger("sphinx.domains.std").logger
logger.addFilter(ct_filter)


def setup(app):
    app.add_css_file("theme_overrides.css")


# Cleanup
# -------
# delete release info to avoid pickling errors from sphinx

del iprelease
