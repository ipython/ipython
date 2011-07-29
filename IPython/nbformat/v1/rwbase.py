from base64 import encodestring, decodestring


class NotebookReader(object):

    def reads(self, s, **kwargs):
        """Read a notebook from a string."""
        raise NotImplementedError("loads must be implemented in a subclass")

    def read(self, fp, **kwargs):
        """Read a notebook from a file like object"""
        return self.reads(fp.read(), **kwargs)


class NotebookWriter(object):

    def writes(self, nb, **kwargs):
        """Write a notebook to a string."""
        raise NotImplementedError("loads must be implemented in a subclass")

    def write(self, nb, fp, **kwargs):
        """Write a notebook to a file like object"""
        return fp.write(self.writes(nb,**kwargs))



