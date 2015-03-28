"""Base classes and utilities for readers and writers."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from IPython.utils.py3compat import string_types, cast_unicode_py2


def rejoin_lines(nb):
    """rejoin multiline text into strings

    For reversing effects of ``split_lines(nb)``.

    This only rejoins lines that have been split, so if text objects were not split
    they will pass through unchanged.

    Used when reading JSON files that may have been passed through split_lines.
    """
    for cell in nb.cells:
        if 'source' in cell and isinstance(cell.source, list):
            cell.source = ''.join(cell.source)
        if cell.get('cell_type', None) == 'code':
            for output in cell.get('outputs', []):
                output_type = output.get('output_type', '')
                if output_type in {'execute_result', 'display_data'}:
                    for key, value in output.get('data', {}).items():
                        if key != 'application/json' and isinstance(value, list):
                            output.data[key] = ''.join(value)
                elif output_type:
                    if isinstance(output.get('text', ''), list):
                        output.text = ''.join(output.text)
    return nb

_non_text_split_mimes = {
    'application/javascript',
    'image/svg+xml',
}

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
                if output.output_type in {'execute_result', 'display_data'}:
                    for key, value in output.data.items():
                        if isinstance(value, string_types) and (
                            key.startswith('text/') or key in _non_text_split_mimes
                        ):
                            output.data[key] = value.splitlines(True)
                elif output.output_type == 'stream':
                    if isinstance(output.text, string_types):
                        output.text = output.text.splitlines(True)
    return nb


def strip_transient(nb):
    """Strip transient values that shouldn't be stored in files.

    This should be called in *both* read and write.
    """
    nb.metadata.pop('orig_nbformat', None)
    nb.metadata.pop('orig_nbformat_minor', None)
    nb.metadata.pop('signature', None)
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
        nbs = cast_unicode_py2(fp.read())
        return self.reads(nbs, **kwargs)


class NotebookWriter(object):
    """A class for writing notebooks."""

    def writes(self, nb, **kwargs):
        """Write a notebook to a string."""
        raise NotImplementedError("loads must be implemented in a subclass")

    def write(self, nb, fp, **kwargs):
        """Write a notebook to a file like object"""
        nbs = cast_unicode_py2(self.writes(nb, **kwargs))
        return fp.write(nbs)
