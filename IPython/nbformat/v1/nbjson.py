"""Read and write notebooks in JSON format."""

from base64 import encodestring
from .rwbase import NotebookReader, NotebookWriter
from .nbbase import from_dict
import json


class JSONReader(NotebookReader):

    def reads(self, s, **kwargs):
        nb = json.loads(s, **kwargs)
        return self.to_notebook(nb, **kwargs)

    def to_notebook(self, d, **kwargs):
        """Convert from a raw JSON dict to a nested NotebookNode structure."""
        return from_dict(d)


class JSONWriter(NotebookWriter):

    def writes(self, nb, **kwargs):
        kwargs['indent'] = 4
        return json.dumps(nb, **kwargs)


_reader = JSONReader()
_writer = JSONWriter()

reads = _reader.reads
read = _reader.read
to_notebook = _reader.to_notebook
write = _writer.write
writes = _writer.writes

