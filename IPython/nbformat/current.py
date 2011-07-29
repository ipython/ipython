import json
from xml.etree import ElementTree as ET
import re

from IPython.nbformat import v2
from IPython.nbformat import v1


current_nbformat = 2


class NBFormatError(Exception):
    pass


def parse_json(s, **kwargs):
    """Parse a string into a (nbformat, dict) tuple."""
    d = json.loads(s, **kwargs)
    nbformat = d.get('nbformat',1)
    return nbformat, d


def parse_xml(s, **kwargs):
    """Parse a string into a (nbformat, etree) tuple."""
    root = ET.fromstring(s)
    nbformat_e = root.find('nbformat')
    if nbformat_e is not None:
        nbformat = int(nbformat_e.text)
    else:
        raise NBFormatError('No nbformat version found')
    return nbformat, root


def parse_py(s, **kwargs):
    """Parse a string into a (nbformat, string) tuple."""
    pattern = r'# <nbformat>(?P<nbformat>\d+)</nbformat>'
    m = re.search(pattern,s)
    if m is not None:
        nbformat = int(m.group('nbformat'))
    else:
        raise NBFormatError('No nbformat version found')
    return nbformat, s


def reads_json(s, **kwargs):
    """Read a JSON notebook from a string and return the NotebookNode object."""
    nbformat, d = parse_json(s, **kwargs)
    if nbformat == 1:
        nb = v1.to_notebook_json(d, **kwargs)
        nb = v2.convert_to_this_nbformat(nb, orig_version=1)
    elif nbformat == 2:
        nb = v2.to_notebook_json(d, **kwargs)
    else:
        raise NBFormatError('Unsupported JSON nbformat version: %i' % nbformat)
    return nb


def writes_json(nb, **kwargs):
    return v2.writes_json(nb, **kwargs)


def reads_xml(s, **kwargs):
    """Read an XML notebook from a string and return the NotebookNode object."""
    nbformat, root = parse_xml(s, **kwargs)
    if nbformat == 2:
        nb = v2.to_notebook_xml(root, **kwargs)
    else:
        raise NBFormatError('Unsupported XML nbformat version: %i' % nbformat)
    return nb


def writes_xml(nb, **kwargs):
    return v2.writes_xml(nb, **kwargs)


def reads_py(s, **kwargs):
    """Read a .py notebook from a string and return the NotebookNode object."""
    nbformat, s = parse_py(s, **kwargs)
    if nbformat == 2:
        nb = v2.to_notebook_py(s, **kwargs)
    else:
        raise NBFormatError('Unsupported PY nbformat version: %i' % nbformat)
    return nb


def writes_py(nb, **kwargs):
    return v2.writes_py(nb, **kwargs)


# High level API


def reads(s, format, **kwargs):
    """Read a notebook from a string and return the NotebookNode object.

    This function properly handles notebooks of any version. The notebook
    returned will always be in the current version's format.

    Parameters
    ----------
    s : str
        The raw string to read the notebook from.
    format : ('xml','json','py')
        The format that the string is in.

    Returns
    -------
    nb : NotebookNode
        The notebook that was read.
    """
    if format == 'xml':
        return reads_xml(s, **kwargs)
    elif format == 'json':
        return reads_json(s, **kwargs)
    elif format == 'py':
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
    format : ('xml','json','py')
        The format to write the notebook in.

    Returns
    -------
    s : str
        The notebook string.
    """
    if format == 'xml':
        return writes_xml(nb, **kwargs)
    elif format == 'json':
        return writes_json(nb, **kwargs)
    elif format == 'py':
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
    format : ('xml','json','py')
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
    format : ('xml','json','py')
        The format to write the notebook in.

    Returns
    -------
    s : str
        The notebook string.
    """
    return fp.write(writes(nb, format, **kwargs))


