"""The IPython notebook format

Use this module to read or write notebook files as particular nbformat versions.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
import io
from IPython.utils import py3compat

from IPython.utils.log import get_logger

from . import v1
from . import v2
from . import v3
from . import v4

__all__ = ['versions', 'validate', 'ValidationError', 'convert', 'from_dict',
           'NotebookNode', 'current_nbformat', 'current_nbformat_minor',
           'NBFormatError', 'NO_CONVERT', 'reads', 'read', 'writes', 'write']

versions = {
    1: v1,
    2: v2,
    3: v3,
    4: v4,
}

from .validator import validate, ValidationError
from .converter import convert
from . import reader
from .notebooknode import from_dict, NotebookNode

from .v4 import (
    nbformat as current_nbformat,
    nbformat_minor as current_nbformat_minor,
)

class NBFormatError(ValueError):
    pass

# no-conversion singleton
NO_CONVERT = object()

def reads(s, as_version, **kwargs):
    """Read a notebook from a string and return the NotebookNode object as the given version.
    
    The string can contain a notebook of any version.
    The notebook will be returned `as_version`, converting, if necessary.

    Notebook format errors will be logged.

    Parameters
    ----------
    s : unicode
        The raw unicode string to read the notebook from.
    as_version : int
        The version of the notebook format to return.
        The notebook will be converted, if necessary.
        Pass nbformat.NO_CONVERT to prevent conversion.

    Returns
    -------
    nb : NotebookNode
        The notebook that was read.
    """
    nb = reader.reads(s, **kwargs)
    if as_version is not NO_CONVERT:
        nb = convert(nb, as_version)
    try:
        validate(nb)
    except ValidationError as e:
        get_logger().error("Notebook JSON is invalid: %s", e)
    return nb


def writes(nb, version=NO_CONVERT, **kwargs):
    """Write a notebook to a string in a given format in the given nbformat version.

    Any notebook format errors will be logged.

    Parameters
    ----------
    nb : NotebookNode
        The notebook to write.
    version : int, optional
        The nbformat version to write.
        If unspecified, or specified as nbformat.NO_CONVERT,
        the notebook's own version will be used and no conversion performed.

    Returns
    -------
    s : unicode
        The notebook as a JSON string.
    """
    if version is not NO_CONVERT:
        nb = convert(nb, version)
    else:
        version, _ = reader.get_version(nb)
    try:
        validate(nb)
    except ValidationError as e:
        get_logger().error("Notebook JSON is invalid: %s", e)
    return versions[version].writes_json(nb, **kwargs)


def read(fp, as_version, **kwargs):
    """Read a notebook from a file as a NotebookNode of the given version.

    The string can contain a notebook of any version.
    The notebook will be returned `as_version`, converting, if necessary.

    Notebook format errors will be logged.

    Parameters
    ----------
    fp : file or str
        Any file-like object with a read method, or a path to a file.
    as_version: int
        The version of the notebook format to return.
        The notebook will be converted, if necessary.
        Pass nbformat.NO_CONVERT to prevent conversion.

    Returns
    -------
    nb : NotebookNode
        The notebook that was read.
    """
    if isinstance(fp, py3compat.string_types):
        with io.open(fp, encoding='utf-8') as f:
            return read(f, as_version, **kwargs)

    return reads(fp.read(), as_version, **kwargs)


def write(nb, fp, version=NO_CONVERT, **kwargs):
    """Write a notebook to a file in a given nbformat version.
    
    The file-like object must accept unicode input.
    
    Parameters
    ----------
    nb : NotebookNode
        The notebook to write.
    fp : file or str
        Any file-like object with a write method that accepts unicode, or
        a path to write a file.
    version : int, optional
        The nbformat version to write.
        If nb is not this version, it will be converted.
        If unspecified, or specified as nbformat.NO_CONVERT,
        the notebook's own version will be used and no conversion performed.
    """
    if isinstance(fp, py3compat.string_types):
        with io.open(fp, 'w', encoding='utf-8') as f:
            return write(nb, f, version=version, **kwargs)

    s = writes(nb, version, **kwargs)
    if isinstance(s, bytes):
        s = s.decode('utf8')
    fp.write(s)
    if not s.endswith(u'\n'):
        fp.write(u'\n')
