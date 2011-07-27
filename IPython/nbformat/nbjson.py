"""Read and write notebooks in JSON format."""

from base64 import encodestring
from .base import NotebookReader, NotebookWriter, base64_decode
import json


class BytesEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, bytes):
            return unicode(encodestring(bytes))
        return json.JSONEncoder.default(self, obj)


class JSONReader(NotebookReader):

    def reads(s, **kwargs):
        nb = json.loads(s, **kwargs)
        nb = base64_decode(nb)
        return nb


class JSONWriter(NotebookWriter):

    def writes(nb, **kwargs):
        kwargs['cls'] = BytesEncoder
        kwargs['indent'] = 4
        return json.dumps(nb, **kwargs)


_reader = JSONReader()
_writer = JSONWriter()

reads = _reader.reads
read = _reader.read
write = _writer.write
writes = _writer.writes

