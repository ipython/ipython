
from .nbbase import (
    NotebookNode,
    new_code_cell, new_text_cell, new_notebook, new_output, new_worksheet
)

from .nbjson import reads as reads_json, writes as writes_json
from .nbjson import reads as read_json, writes as write_json
from .nbjson import to_notebook as to_notebook_json

from .nbxml import reads as reads_xml, writes as writes_xml
from .nbxml import reads as read_xml, writes as write_xml
from .nbxml import to_notebook as to_notebook_xml

from .nbpy import reads as reads_py, writes as writes_py
from .nbpy import reads as read_py, writes as write_py
from .nbpy import to_notebook as to_notebook_py

from .convert import convert_to_this_nbformat


def parse_filename(fname):
    """Parse a notebook filename.

    This function takes a notebook filename and returns the notebook
    format (xml/json/py) and the notebook name. This logic can be
    summarized as follows:

    * notebook.ipynb -> (notebook.ipynb, notebook, xml) 
    * notebook.json  -> (notebook.json, notebook, json)
    * notebook.py    -> (notebook.py, notebook, py)
    * notebook       -> (notebook.ipynb, notebook, xml)

    Parameters
    ----------
    fname : unicode
        The notebook filename. The filename can use a specific filename
        extention (.ipynb, .json, .py) or none, in which case .ipynb will
        be assumed.

    Returns
    -------
    (fname, name, format) : (unicode, unicode, unicode)  
        The filename, notebook name and format.      
    """
    if fname.endswith(u'.ipynb'):
        format = u'xml'
    elif fname.endswith(u'.json'):
        format = u'json'
    elif fname.endswith(u'.py'):
        format = u'py'
    else:
        fname = fname + u'.ipynb'
        format = u'xml'
    name = fname.split('.')[0]
    return fname, name, format

