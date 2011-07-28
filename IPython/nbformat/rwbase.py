from base64 import encodestring, decodestring


def base64_decode(nb):
    """Base64 encode all bytes objects in the notebook."""
    for ws in nb['worksheets']:
        for cell in ws['cells']:
            if cell['cell_type'] == 'code':
                if cell.get('image/png',''):
                    cell['image/png'] = bytes(decodestring(cell['image/png']))
    return nb


def base64_encode(nb):
    """Base64 decode all binary objects in the notebook."""
    for ws in nb['worksheets']:
        for cell in ws['cells']:
            if cell['cell_type'] == 'code':
                if cell.get('image/png',''):
                    cell['image/png'] = unicode(encodestring(cell['image/png']))
    return nb


class NotebookReader(object):

    def reads(self, s, **kwargs):
        """Read a notebook from a string."""
        raise NotImplementedError("loads must be implemented in a subclass")

    def read(self, fp, **kwargs):
        """Read a notebook from a file like object"""
        return self.loads(fp.read(), **kwargs)


class NotebookWriter(object):

    def writes(self, nb, **kwargs):
        """Write a notebook to a string."""
        raise NotImplementedError("loads must be implemented in a subclass")

    def write(self, nb, fp, **kwargs):
        """Write a notebook to a file like object"""
        return fp.write(self.dumps(nb,**kwargs))



