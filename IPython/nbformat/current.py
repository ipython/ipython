"""The official API for working with notebooks in the current format version."""

from __future__ import print_function

import re

from IPython.utils.py3compat import unicode_type

from IPython.nbformat.v3 import (
    NotebookNode,
    new_code_cell, new_text_cell, new_notebook, new_output, new_worksheet,
    parse_filename, new_metadata, new_author, new_heading_cell, nbformat,
    nbformat_minor, nbformat_schema, to_notebook_json
)
from IPython.nbformat import v3 as _v_latest

from .reader import reads as reader_reads
from .reader import versions
from .convert import convert
from .validator import validate

from IPython.utils.log import get_logger

__all__ = ['NotebookNode', 'new_code_cell', 'new_text_cell', 'new_notebook',
'new_output', 'new_worksheet', 'parse_filename', 'new_metadata', 'new_author',
'new_heading_cell', 'nbformat', 'nbformat_minor', 'nbformat_schema',
'to_notebook_json', 'convert', 'validate', 'NBFormatError', 'parse_py',
'reads_json', 'writes_json', 'reads_py', 'writes_py', 'reads', 'writes', 'read',
'write']

current_nbformat = nbformat
current_nbformat_minor = nbformat_minor
current_nbformat_module = _v_latest.__name__


class NBFormatError(ValueError):
    pass


def parse_py(s, **kwargs):
    """Parse a string into a (nbformat, string) tuple."""
    nbf = current_nbformat
    nbm = current_nbformat_minor
    
    pattern = r'# <nbformat>(?P<nbformat>\d+[\.\d+]*)</nbformat>'
    m = re.search(pattern,s)
    if m is not None:
        digits = m.group('nbformat').split('.')
        nbf = int(digits[0])
        if len(digits) > 1:
            nbm = int(digits[1])

    return nbf, nbm, s


def reads_json(nbjson, **kwargs):
    """Read a JSON notebook from a string and return the NotebookNode
    object. Report if any JSON format errors are detected.

    """
    nb = reader_reads(nbjson, **kwargs)
    nb_current = convert(nb, current_nbformat)
    errors = validate(nb_current)
    if errors:
        get_logger().error(
            "Notebook JSON is invalid (%d errors detected during read)",
            len(errors))
    return nb_current


def writes_json(nb, **kwargs):
    """Take a NotebookNode object and write out a JSON string. Report if
    any JSON format errors are detected.

    """
    errors = validate(nb)
    if errors:
        get_logger().error(
            "Notebook JSON is invalid (%d errors detected during write)",
            len(errors))
    nbjson = versions[current_nbformat].writes_json(nb, **kwargs)
    return nbjson


def reads_py(s, **kwargs):
    """Read a .py notebook from a string and return the NotebookNode object."""
    nbf, nbm, s = parse_py(s, **kwargs)
    if nbf in (2, 3):
        nb = versions[nbf].to_notebook_py(s, **kwargs)
    else:
        raise NBFormatError('Unsupported PY nbformat version: %i' % nbf)
    return nb


def writes_py(nb, **kwargs):
    # nbformat 3 is the latest format that supports py
    return versions[3].writes_py(nb, **kwargs)


# High level API


def reads(s, format, **kwargs):
    """Read a notebook from a string and return the NotebookNode object.

    This function properly handles notebooks of any version. The notebook
    returned will always be in the current version's format.

    Parameters
    ----------
    s : unicode
        The raw unicode string to read the notebook from.
    format : (u'json', u'ipynb', u'py')
        The format that the string is in.

    Returns
    -------
    nb : NotebookNode
        The notebook that was read.
    """
    format = unicode_type(format)
    if format == u'json' or format == u'ipynb':
        return reads_json(s, **kwargs)
    elif format == u'py':
        return reads_py(s, **kwargs)
    else:
        raise NBFormatError('Unsupported format: %s' % format)


def writes(nb, format, **kwargs):
    """Write a notebook to a string in a given format in the current nbformat version.

    This function always writes the notebook in the current nbformat version.

    Parameters
    ----------
    nb : NotebookNode
        The notebook to write.
    format : (u'json', u'ipynb', u'py')
        The format to write the notebook in.

    Returns
    -------
    s : unicode
        The notebook string.
    """
    format = unicode_type(format)
    if format == u'json' or format == u'ipynb':
        return writes_json(nb, **kwargs)
    elif format == u'py':
        return writes_py(nb, **kwargs)
    else:
        raise NBFormatError('Unsupported format: %s' % format)


def read(fp, format, **kwargs):
    """Read a notebook from a file and return the NotebookNode object.

    This function properly handles notebooks of any version. The notebook
    returned will always be in the current version's format.

    Parameters
    ----------
    fp : file
        Any file-like object with a read method.
    format : (u'json', u'ipynb', u'py')
        The format that the string is in.

    Returns
    -------
    nb : NotebookNode
        The notebook that was read.
    """
    return reads(fp.read(), format, **kwargs)


def write(nb, fp, format, **kwargs):
    """Write a notebook to a file in a given format in the current nbformat version.

    This function always writes the notebook in the current nbformat version.

    Parameters
    ----------
    nb : NotebookNode
        The notebook to write.
    fp : file
        Any file-like object with a write method.
    format : (u'json', u'ipynb', u'py')
        The format to write the notebook in.

    Returns
    -------
    s : unicode
        The notebook string.
    """
    return fp.write(writes(nb, format, **kwargs))

def _convert_to_metadata():
    """Convert to a notebook having notebook metadata."""
    import glob
    for fname in glob.glob('*.ipynb'):
        print('Converting file:',fname)
        with open(fname,'r') as f:
            nb = read(f,u'json')
        md = new_metadata()
        if u'name' in nb:
            md.name = nb.name
            del nb[u'name']            
        nb.metadata = md
        with open(fname,'w') as f:
            write(nb, f, u'json')

