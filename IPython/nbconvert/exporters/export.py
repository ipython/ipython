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

from .exporter import Exporter
from .basichtml import BasicHTMLExporter
from .fullhtml import FullHTMLExporter
from .latex import LatexExporter
from .markdown import MarkdownExporter
from .python import PythonExporter
from .python_armor import PythonArmorExporter
from .reveal import RevealExporter
from .rst import RstExporter
from .sphinx_howto import SphinxHowtoExporter
from .sphinx_manual import SphinxManualExporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

def DocDecorator(f):    
    
    #Set docstring of function
    f.__doc__ = f.__doc__ + """
    nb : Notebook node
    config : config
        User configuration instance.
    transformers : list[of transformer]
        Custom transformers to apply to the notebook prior to engaging
        the Jinja template engine.  Any transformers specified here 
        will override existing transformers if a naming conflict
        occurs.
    filters : list[of filter]
        Custom filters to make accessible to the Jinja templates.  Any
        filters specified here will override existing filters if a
        naming conflict occurs.
        
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
    'export_python_armor',
    'export_reveal',
    'export_rst',
    'export_by_name'
]

@DocDecorator
def export(exporter_type, nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object using specific exporter class.
    
    exporter_type : Exporter class type
        Class type of the exporter that should be used.  This method
        will initialize it's own instance of the class.  It is
        ASSUMED that the class type provided exposes a
        constructor (__init__) with the same signature as the
        base Exporter class.}
    """
    
    #Check arguments
    if exporter_type is None:
        raise TypeError("Exporter is None")
    elif not issubclass(exporter_type, Exporter):
        raise TypeError("Exporter type does not inherit from Exporter (base)")
    
    if nb is None:
        raise TypeError("nb is None")
    
    #Create the exporter
    exporter_instance = exporter_type(preprocessors=transformers, 
                                      jinja_filters=filters, config=config)

    #Try to convert the notebook using the appropriate conversion function.
    if isinstance(nb, NotebookNode):
        output, resources = exporter_instance.from_notebook_node(nb)
    elif isinstance(nb, basestring):
        output, resources = exporter_instance.from_filename(nb)
    else:
        output, resources = exporter_instance.from_file(nb)
    return output, resources, exporter_instance


@DocDecorator
def export_sphinx_manual(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to Sphinx Manual LaTeX
    """
    return export(SphinxManualExporter, nb, config, transformers, filters)


@DocDecorator
def export_sphinx_howto(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to Sphinx HowTo LaTeX
    """
    return export(SphinxHowtoExporter, nb, config, transformers, filters)


@DocDecorator
def export_basic_html(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to Basic HTML
    """
    return export(BasicHTMLExporter, nb, config, transformers, filters)


@DocDecorator
def export_full_html(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to Full HTML
    """
    return export(FullHTMLExporter, nb, config, transformers, filters)


@DocDecorator
def export_latex(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to LaTeX
    """
    return export(LatexExporter, nb, config, transformers, filters)


@DocDecorator
def export_markdown(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to Markdown
    """
    return export(MarkdownExporter, nb, config, transformers, filters)


@DocDecorator
def export_python(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to Python
    """
    return export(PythonExporter, nb, config, transformers, filters)


@DocDecorator
def export_python_armor(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to Python (Armor)
    """
    return export(PythonArmorExporter, nb, config, transformers, filters)


@DocDecorator
def export_reveal(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to Reveal
    """
    return export(RevealExporter, nb, config, transformers, filters)


@DocDecorator
def export_rst(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to RST
    """
    return export(RstExporter, nb, config, transformers, filters)


@DocDecorator
def export_by_name(template_name, nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to a template type by its name.  Reflection
    (Inspect) is used to find the template's corresponding explicit export
    method defined in this module.  That method is then called directly.
    
    template_name : str
        Name of the template style to export to.
    """
    
    function_name = "export_" + template_name.lower()
    
    if function_name in globals():
        return globals()[function_name](nb, config, transformers, filters)
    else:
        return None

