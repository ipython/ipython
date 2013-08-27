"""Read and write notebooks in JSON format.

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

import copy
import json

from .nbbase import from_dict
from .rwbase import (
    NotebookReader, NotebookWriter, restore_bytes, rejoin_lines, split_lines
)

from IPython.utils import py3compat

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class BytesEncoder(json.JSONEncoder):
    """A JSON encoder that accepts b64 (and other *ascii*) bytestrings."""
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode('ascii')
        return json.JSONEncoder.default(self, obj)


class JSONReader(NotebookReader):

    def reads(self, s, **kwargs):
        nb = json.loads(s, **kwargs)
        nb = self.to_notebook(nb, **kwargs)
        return nb

    def to_notebook(self, d, **kwargs):
        return restore_bytes(rejoin_lines(from_dict(d)))


class JSONWriter(NotebookWriter):
    
    def _pre_write(self, nb, kwargs):
        """prepare the notebook structure to be json-ifyed

        In memory and json structure have some differences,
        this make the in-memory -> json transform.

        """
        kwargs['cls'] = BytesEncoder
        kwargs['indent'] = 1
        kwargs['sort_keys'] = True
        kwargs['separators'] = (',',': ')
        if kwargs.pop('split_lines', True):
            nb = split_lines(copy.deepcopy(nb))
        return nb,kwargs

    def writes(self, nb, **kwargs):
        kwargs['cls'] = BytesEncoder
        kwargs['indent'] = 1
        kwargs['sort_keys'] = True
        kwargs['separators'] = (',',': ')
        if kwargs.pop('split_lines', True):
            nb = split_lines(copy.deepcopy(nb))
        return py3compat.str_to_unicode(json.dumps(nb, **kwargs), 'utf-8')

    def to_json_stream(self, nb, **kwargs):
        nb,kwargs = self._pre_write(nb, kwargs)
        return json.dump(nb, **kwargs)

def to_dict(nb):
    """ return a clean dict copy of the notebook

    reverse changes done by files-> in memory loading
    and promote the NotebookNode back to dict
    """

    return dict(split_lines(copy.deepcopy(nb)))
    

_reader = JSONReader()
_writer = JSONWriter()

reads = _reader.reads
read = _reader.read
to_notebook = _reader.to_notebook
write = _writer.write
writes = _writer.writes
to_json_stream = _writer.to_json_stream
to_dict = to_dict

