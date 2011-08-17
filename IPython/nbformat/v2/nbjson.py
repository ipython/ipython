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

from base64 import encodestring
from .nbbase import from_dict
from .rwbase import NotebookReader, NotebookWriter, base64_decode
import json

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class BytesEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return unicode(encodestring(bytes))
        return json.JSONEncoder.default(self, obj)


class JSONReader(NotebookReader):

    def reads(self, s, **kwargs):
        nb = json.loads(s, **kwargs)
        nb = self.to_notebook(nb, **kwargs)
        return nb

    def to_notebook(self, d, **kwargs):
        return base64_decode(from_dict(d))


class JSONWriter(NotebookWriter):

    def writes(self, nb, **kwargs):
        kwargs['cls'] = BytesEncoder
        kwargs['indent'] = 4
        return json.dumps(nb, **kwargs)


_reader = JSONReader()
_writer = JSONWriter()

reads = _reader.reads
read = _reader.read
to_notebook = _reader.to_notebook
write = _writer.write
writes = _writer.writes

