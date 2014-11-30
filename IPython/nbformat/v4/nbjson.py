"""Read and write notebooks in JSON format."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import copy
import json

from IPython.utils import py3compat

from .nbbase import from_dict
from .rwbase import (
    NotebookReader, NotebookWriter, rejoin_lines, split_lines, strip_transient
)
from IPython.utils.traitlets import Bool


class BytesEncoder(json.JSONEncoder):
    """A JSON encoder that accepts b64 (and other *ascii*) bytestrings."""
    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode('ascii')
        return json.JSONEncoder.default(self, obj)


class JSONReader(NotebookReader):

    def reads(self, s, **kwargs):
        """Read a JSON string into a Notebook object"""
        nb = json.loads(s, **kwargs)
        nb = self.to_notebook(nb, **kwargs)
        return nb

    def to_notebook(self, d, **kwargs):
        """Convert a disk-format notebook dict to in-memory NotebookNode
        
        handles multi-line values as strings, scrubbing of transient values, etc.
        """
        nb = from_dict(d)
        nb = rejoin_lines(nb)
        nb = strip_transient(nb)
        return nb


class JSONWriter(NotebookWriter):

    ensure_ascii = Bool(True, config=True,
        help="""Whether the output file only contains ASCII characters.
        If ensure_ascii is True (the default), all non-ASCII characters
        in the output are escaped with \\uXXXX sequences. If ensure_ascii
        is False, these characters are represented using UTF-8.
        """
    )

    def writes(self, nb, **kwargs):
        """Serialize a NotebookNode object as a JSON string"""
        kwargs['cls'] = BytesEncoder
        kwargs['indent'] = 1
        kwargs['sort_keys'] = True
        kwargs['separators'] = (',',': ')
        kwargs['ensure_ascii'] = self.ensure_ascii
        # don't modify in-memory dict
        nb = copy.deepcopy(nb)
        if kwargs.pop('split_lines', True):
            nb = split_lines(nb)
        nb = strip_transient(nb)
        return py3compat.str_to_unicode(json.dumps(nb, **kwargs), 'utf-8')


_reader = JSONReader()
_writer = JSONWriter()

reads = _reader.reads
read = _reader.read
to_notebook = _reader.to_notebook
write = _writer.write
writes = _writer.writes
