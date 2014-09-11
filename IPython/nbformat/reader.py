"""API for reading notebooks.

Authors:

* Jonathan Frederic
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import json

from . import v1
from . import v2
from . import v3

versions = {
    1: v1,
    2: v2,
    3: v3,
    }

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class NotJSONError(ValueError):
    pass

def parse_json(s, **kwargs):
    """Parse a JSON string into a dict."""
    try:
        nb_dict = json.loads(s, **kwargs)
    except ValueError:
        # Limit the error message to 80 characters.  Display whatever JSON will fit.
        raise NotJSONError(("Notebook does not appear to be JSON: %r" % s)[:77] + "...")
    return nb_dict

# High level API

def get_version(nb):
    """Get the version of a notebook.

    Parameters
    ----------
    nb : dict
        NotebookNode or dict containing notebook data.

    Returns
    -------
    Tuple containing major (int) and minor (int) version numbers
    """
    major = nb.get('nbformat', 1)
    minor = nb.get('nbformat_minor', 0)
    return (major, minor)


def reads(s, **kwargs):
    """Read a notebook from a json string and return the 
    NotebookNode object.

    This function properly reads notebooks of any version.  No version 
    conversion is performed.

    Parameters
    ----------
    s : unicode
        The raw unicode string to read the notebook from.

    Returns
    -------
    nb : NotebookNode
        The notebook that was read.
    """
    from .current import NBFormatError

    nb_dict = parse_json(s, **kwargs)
    (major, minor) = get_version(nb_dict)
    if major in versions:
        return versions[major].to_notebook_json(nb_dict, minor=minor)
    else:
        raise NBFormatError('Unsupported nbformat version %s' % major)


def read(fp, **kwargs):
    """Read a notebook from a file and return the NotebookNode object.

    This function properly reads notebooks of any version.  No version 
    conversion is performed.

    Parameters
    ----------
    fp : file
        Any file-like object with a read method.

    Returns
    -------
    nb : NotebookNode
        The notebook that was read.
    """
    return reads(fp.read(), **kwargs)
