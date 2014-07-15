"""Base classes and utilities for readers and writers."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.utils import py3compat
from IPython.utils.py3compat import unicode_type, string_types

# output keys that are likely to have multiline values
_multiline_outputs = {
    'text/plain',
    'text/html',
    'image/svg+xml',
    'text/latex',
    'application/javascript',
}


# FIXME: workaround for old splitlines()
def _join_lines(lines):
    """join lines that have been written by splitlines()

    Has logic to protect against `splitlines()`, which
    should have been `splitlines(True)`
    """
    if lines and lines[0].endswith(('\n', '\r')):
        # created by splitlines(True)
        return u''.join(lines)
    else:
        # created by splitlines()
        return u'\n'.join(lines)


def rejoin_lines(nb):
    """rejoin multiline text into strings

    For reversing effects of ``split_lines(nb)``.

    This only rejoins lines that have been split, so if text objects were not split
    they will pass through unchanged.

    Used when reading JSON files that may have been passed through split_lines.
    """
    for cell in nb.cells:
        if 'source' in cell and isinstance(cell.source, list):
            cell.source = _join_lines(cell.source)
        if cell.cell_type == 'code':
            for output in cell.outputs:
                for key in _multiline_outputs:
                    item = output.get(key, None)
                    if isinstance(item, list):
                        output[key] = _join_lines(item)
    return nb


def split_lines(nb):
    """split likely multiline text into lists of strings

    For file output more friendly to line-based VCS. ``rejoin_lines(nb)`` will
    reverse the effects of ``split_lines(nb)``.

    Used when writing JSON files.
    """
    for cell in nb.cells:
        source = cell.get('source', None)
        if isinstance(source, string_types):
            cell['source'] = source.splitlines(True)

        if cell.cell_type == 'code':
            for output in cell.outputs:
                for key in _multiline_outputs:
                    item = output.get(key, None)
                    if isinstance(item, string_types):
                        output[key] = item.splitlines(True)
    return nb


def strip_transient(nb):
    """Strip transient values that shouldn't be stored in files.

    This should be called in *both* read and write.
    """
    nb.metadata.pop('orig_nbformat', None)
    nb.metadata.pop('orig_nbformat_minor', None)
    for cell in nb.cells:
        cell.metadata.pop('trusted', None)
    return nb


class NotebookReader(object):
    """A class for reading notebooks."""

    def reads(self, s, **kwargs):
        """Read a notebook from a string."""
        raise NotImplementedError("loads must be implemented in a subclass")

    def read(self, fp, **kwargs):
        """Read a notebook from a file like object"""
        nbs = fp.read()
        if not py3compat.PY3 and not isinstance(nbs, unicode_type):
            nbs = py3compat.str_to_unicode(nbs)
        return self.reads(nbs, **kwargs)


class NotebookWriter(object):
    """A class for writing notebooks."""

    def writes(self, nb, **kwargs):
        """Write a notebook to a string."""
        raise NotImplementedError("loads must be implemented in a subclass")

    def write(self, nb, fp, **kwargs):
        """Write a notebook to a file like object"""
        nbs = self.writes(nb,**kwargs)
        if not py3compat.PY3 and not isinstance(nbs, unicode_type):
            # this branch is likely only taken for JSON on Python 2
            nbs = py3compat.str_to_unicode(nbs)
        return fp.write(nbs)
