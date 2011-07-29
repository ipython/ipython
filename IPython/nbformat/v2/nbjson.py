"""Read and write notebooks in JSON format."""

from base64 import encodestring
from .nbbase import from_dict
from .rwbase import NotebookReader, NotebookWriter, base64_decode
import json


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

