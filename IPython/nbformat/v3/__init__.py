"""The main API for the v3 notebook format.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from .nbbase import (
    NotebookNode,
    new_code_cell, new_text_cell, new_notebook, new_output, new_worksheet,
    new_metadata, new_author, new_heading_cell, nbformat, nbformat_minor
)

from .nbjson import reads as reads_json, writes as writes_json
from .nbjson import reads as read_json, writes as write_json
from .nbjson import to_notebook as to_notebook_json

from .nbpy import reads as reads_py, writes as writes_py
from .nbpy import reads as read_py, writes as write_py
from .nbpy import to_notebook as to_notebook_py

from .convert import downgrade, upgrade

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def parse_filename(fname):
    """Parse a notebook filename.

    This function takes a notebook filename and returns the notebook
    format (json/py) and the notebook name. This logic can be
    summarized as follows:

    * notebook.ipynb -> (notebook.ipynb, notebook, json)
    * notebook.json  -> (notebook.json, notebook, json)
    * notebook.py    -> (notebook.py, notebook, py)
    * notebook       -> (notebook.ipynb, notebook, json)

    Parameters
    ----------
    fname : unicode
        The notebook filename. The filename can use a specific filename
        extention (.ipynb, .json, .py) or none, in which case .ipynb will
        be assumed.

    Returns
    -------
    (fname, name, format) : (unicode, unicode, unicode)
        The filename, notebook name and format.
    """
    if fname.endswith(u'.ipynb'):
        format = u'json'
    elif fname.endswith(u'.json'):
        format = u'json'
    elif fname.endswith(u'.py'):
        format = u'py'
    else:
        fname = fname + u'.ipynb'
        format = u'json'
    name = fname.split('.')[0]
    return fname, name, format

