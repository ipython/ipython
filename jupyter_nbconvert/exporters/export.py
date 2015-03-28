"""Module containing single call export functions."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from functools import wraps

from IPython.nbformat import NotebookNode
from IPython.utils.decorators import undoc
from IPython.utils.py3compat import string_types

from .exporter import Exporter
from .templateexporter import TemplateExporter
from .html import HTMLExporter
from .slides import SlidesExporter
from .latex import LatexExporter
from .pdf import PDFExporter
from .markdown import MarkdownExporter
from .python import PythonExporter
from .rst import RSTExporter
from .notebook import NotebookExporter
from .script import ScriptExporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

@undoc
def DocDecorator(f):
    
    #Set docstring of function
    f.__doc__ = f.__doc__ + """
    nb : :class:`~IPython.nbformat.NotebookNode`
      The notebook to export.
    config : config (optional, keyword arg)
        User configuration instance.
    resources : dict (optional, keyword arg)
        Resources used in the conversion process.
        
    Returns
    -------
    tuple- output, resources, exporter_instance
    output : str
        Jinja 2 output.  This is the resulting converted notebook.
    resources : dictionary
        Dictionary of resources used prior to and during the conversion 
        process.
    exporter_instance : Exporter
        Instance of the Exporter class used to export the document.  Useful
        to caller because it provides a 'file_extension' property which
        specifies what extension the output should be saved as.

    Notes
    -----
    WARNING: API WILL CHANGE IN FUTURE RELEASES OF NBCONVERT
    """
            
    @wraps(f)
    def decorator(*args, **kwargs):
        return f(*args, **kwargs)
    
    return decorator


#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

__all__ = [
    'export',
    'export_html',
    'export_custom',
    'export_slides',
    'export_latex',
    'export_pdf',
    'export_markdown',
    'export_python',
    'export_script',
    'export_rst',
    'export_by_name',
    'get_export_names',
    'ExporterNameError'
]


class ExporterNameError(NameError):
    pass

@DocDecorator
def export(exporter, nb, **kw):
    """
    Export a notebook object using specific exporter class.
    
    Parameters
    ----------
    exporter : class:`~jupyter_nbconvert.exporters.exporter.Exporter` class or instance
      Class type or instance of the exporter that should be used.  If the
      method initializes it's own instance of the class, it is ASSUMED that
      the class type provided exposes a constructor (``__init__``) with the same
      signature as the base Exporter class.
    """
    
    #Check arguments
    if exporter is None:
        raise TypeError("Exporter is None")
    elif not isinstance(exporter, Exporter) and not issubclass(exporter, Exporter):
        raise TypeError("exporter does not inherit from Exporter (base)")
    if nb is None:
        raise TypeError("nb is None")
    
    #Create the exporter
    resources = kw.pop('resources', None)
    if isinstance(exporter, Exporter):
        exporter_instance = exporter
    else:
        exporter_instance = exporter(**kw)
    
    #Try to convert the notebook using the appropriate conversion function.
    if isinstance(nb, NotebookNode):
        output, resources = exporter_instance.from_notebook_node(nb, resources)
    elif isinstance(nb, string_types):
        output, resources = exporter_instance.from_filename(nb, resources)
    else:
        output, resources = exporter_instance.from_file(nb, resources)
    return output, resources

exporter_map = dict(
    custom=TemplateExporter,
    html=HTMLExporter,
    slides=SlidesExporter,
    latex=LatexExporter,
    pdf=PDFExporter,
    markdown=MarkdownExporter,
    python=PythonExporter,
    rst=RSTExporter,
    notebook=NotebookExporter,
    script=ScriptExporter,
)

def _make_exporter(name, E):
    """make an export_foo function from a short key and Exporter class E"""
    def _export(nb, **kw):
        return export(E, nb, **kw)
    _export.__doc__ = """Export a notebook object to {0} format""".format(name)
    return _export
    
g = globals()

for name, E in exporter_map.items():
    g['export_%s' % name] = DocDecorator(_make_exporter(name, E))

@DocDecorator
def export_by_name(format_name, nb, **kw):
    """
    Export a notebook object to a template type by its name.  Reflection
    (Inspect) is used to find the template's corresponding explicit export
    method defined in this module.  That method is then called directly.
    
    Parameters
    ----------
    format_name : str
        Name of the template style to export to.
    """
    
    function_name = "export_" + format_name.lower()
    
    if function_name in globals():
        return globals()[function_name](nb, **kw)
    else:
        raise ExporterNameError("template for `%s` not found" % function_name)


def get_export_names():
    """Return a list of the currently supported export targets

    WARNING: API WILL CHANGE IN FUTURE RELEASES OF NBCONVERT"""
    return sorted(exporter_map.keys())
