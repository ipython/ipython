"""The main module for the v1 notebook format."""

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
    new_code_cell, new_text_cell, new_notebook
)

from .nbjson import reads as reads_json, writes as writes_json
from .nbjson import reads as read_json, writes as write_json
from .nbjson import to_notebook as to_notebook_json

from .convert import convert_to_this_nbformat

