"""
Module containing single call export functions.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from functools import wraps

from IPython.nbformat.v3.nbbase import NotebookNode
from IPython.config import Config

from .exporter import Exporter
from .basichtml import BasicHTMLExporter
from .fullhtml import FullHTMLExporter
from .latex import LatexExporter
from .markdown import MarkdownExporter
from .python import PythonExporter
from .reveal import RevealExporter
from .rst import RSTExporter
from .sphinx_howto import SphinxHowtoExporter
from .sphinx_manual import SphinxManualExporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

def DocDecorator(f):
    
    #Set docstring of function
    f.__doc__ = f.__doc__ + """
    nb : Notebook node
    config : config (optional, keyword arg)
        User configuration instance.
    resources : dict (optional, keyword arg)
        Resources used in the conversion process.
        
    Returns
    ----------
    tuple- output, resources, exporter_instance
    output : str
        Jinja 2 output.  This is the resulting converted notebook.
    resources : dictionary
        Dictionary of resources used prior to and during the conversion 
        process.
    exporter_instance : Exporter
        Instance of the Exporter class used to export the document.  Useful
        to caller because it provides a 'file_extension' property which
        specifies what extension the output should be saved as."""
            
    @wraps(f)
    def decorator(*args, **kwargs):
        return f(*args, **kwargs)
    
    return decorator


#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

__all__ = [
    'export',
    'export_sphinx_manual',
    'export_sphinx_howto',
    'export_basic_html',
    'export_full_html',
    'export_latex',
    'export_markdown',
    'export_python',
    'export_reveal',
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
    
    exporter : Exporter class type or instance
        Class type or instance of the exporter that should be used.  If the 
        method initializes it's own instance of the class, it is ASSUMED that 
        the class type provided exposes a constructor (__init__) with the same 
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
    elif isinstance(nb, basestring):
        output, resources = exporter_instance.from_filename(nb, resources)
    else:
        output, resources = exporter_instance.from_file(nb, resources)
    return output, resources


@DocDecorator
def export_sphinx_manual(nb, **kw):
    """
    Export a notebook object to Sphinx Manual LaTeX
    """
    return export(SphinxManualExporter, nb, **kw)


@DocDecorator
def export_sphinx_howto(nb, **kw):
    """
    Export a notebook object to Sphinx HowTo LaTeX
    """
    return export(SphinxHowtoExporter, nb, **kw)


@DocDecorator
def export_basic_html(nb, **kw):
    """
    Export a notebook object to Basic HTML
    """
    return export(BasicHTMLExporter, nb, **kw)


@DocDecorator
def export_full_html(nb, **kw):
    """
    Export a notebook object to Full HTML
    """
    return export(FullHTMLExporter, nb, **kw)


@DocDecorator
def export_latex(nb, **kw):
    """
    Export a notebook object to LaTeX
    """
    return export(LatexExporter, nb, **kw)


@DocDecorator
def export_markdown(nb, **kw):
    """
    Export a notebook object to Markdown
    """
    return export(MarkdownExporter, nb, **kw)


@DocDecorator
def export_python(nb, **kw):
    """
    Export a notebook object to Python
    """
    return export(PythonExporter, nb, **kw)


@DocDecorator
def export_reveal(nb, **kw):
    """
    Export a notebook object to a Reveal.js presentation
    """
    return export(RevealExporter, nb, **kw)


@DocDecorator
def export_rst(nb, **kw):
    """
    Export a notebook object to reStructuredText
    """
    return export(RSTExporter, nb, **kw)


@DocDecorator
def export_by_name(format_name, nb, **kw):
    """
    Export a notebook object to a template type by its name.  Reflection
    (Inspect) is used to find the template's corresponding explicit export
    method defined in this module.  That method is then called directly.
    
    format_name : str
        Name of the template style to export to.
    """
    
    function_name = "export_" + format_name.lower()
    
    if function_name in globals():
        return globals()[function_name](nb, **kw)
    else:
        raise ExporterNameError("template for `%s` not found" % function_name)


def get_export_names():
    "Return a list of the currently supported export targets"
    # grab everything after 'export_'
    l = [x[len('export_'):] for x in __all__ if x.startswith('export_')]
    
    # filter out the one method that is not a template
    l = [x for x in l if 'by_name' not in x]
    return sorted(l)
