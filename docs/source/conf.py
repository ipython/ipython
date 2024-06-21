# -*- coding: utf-8 -*-
#
# IPython documentation build configuration file.

# NOTE: This file has been edited manually from the auto-generated one from
# sphinx.  Do NOT delete and re-generate.  If any changes from sphinx are
# needed, generate a scratch one and merge by hand any new fields needed.

#
# This file is execfile()d with the current directory set to its containing dir.
#
# The contents of this file are pickled, so don't put values in the namespace
# that aren't pickleable (module imports are okay, they're removed automatically).
#
# All configuration values have a default value; values that are commented out
# serve to show the default value.


import sys, os
from pathlib import Path
from there import print

from sphinx_toml import load_into_locals

load_into_locals(locals())

if sys.version_info > (3, 11):
    import tomllib
else:
    import tomli as tomllib

with open("./sphinx.toml", "rb") as f:
    config = tomllib.load(f)

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
import sphinx_rtd_theme

# Allow Python scripts to change behaviour during sphinx run
os.environ["IN_SPHINX_RUN"] = "True"

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

# Options for HTML output
# -----------------------
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]



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

import logging


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

import sphinx.util

logger = sphinx.util.logging.getLogger("sphinx.domains.std").logger
logger.addFilter(ct_filter)


def setup(app):
    app.add_css_file("theme_overrides.css")


# Cleanup
# -------
# delete release info to avoid pickling errors from sphinx

del iprelease

print(intersphinx_mapping)
