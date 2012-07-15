"""Code for converting notebooks to and from the v2 format.

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
    new_code_cell, new_text_cell, new_worksheet, new_notebook, new_output,
    nbformat, nbformat_minor
)

from IPython.nbformat import v2

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def convert_to_this_nbformat(nb, orig_version=2, orig_minor=0):
    """Convert a notebook to the v3 format.

    Parameters
    ----------
    nb : NotebookNode
        The Python representation of the notebook to convert.
    orig_version : int
        The original version of the notebook to convert.
    orig_minor : int
        The original minor version of the notebook to convert (only relevant for v >= 3).
    """
    if orig_version == 1:
        nb = v2.convert_to_this_nbformat(nb)
        orig_version = 2
    if orig_version == 2:
        # Mark the original nbformat so consumers know it has been converted.
        nb.nbformat = nbformat
        nb.nbformat_minor = nbformat_minor
        
        nb.orig_nbformat = 2
        return nb
    elif orig_version == 3:
        if orig_minor != nbformat_minor:
            nb.orig_nbformat_minor = orig_minor
        nb.nbformat_minor = nbformat_minor
        return nb
    else:
        raise ValueError('Cannot convert a notebook from v%s to v3' % orig_version)

