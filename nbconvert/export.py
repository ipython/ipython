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

import sys
import inspect

from IPython.nbformat.v3.nbbase import NotebookNode

from .exporters.exporter import Exporter
from .exporters.basichtml import BasicHtmlExporter
from .exporters.fullhtml import FullHtmlExporter
from .exporters.latex import LatexExporter
from .exporters.markdown import MarkdownExporter
from .exporters.python import PythonExporter
from .exporters.python_armor import PythonArmorExporter
from .exporters.reveal import RevealExporter
from .exporters.rst import RstExporter
from .exporters.sphinx_howto import SphinxHowtoExporter
from .exporters.sphinx_manual import SphinxManualExporter


#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def export(nb, config=None, transformers=None, filters=None, exporter_type=Exporter):
    """
    Export a notebook object using specific exporter class.
    
    Parameters
    ----------
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
    exporter_type:
        Class type of the exporter that should be used.  This method
        will initialize it's own instance of the class.  It is
        ASSUMED that the class type provided exposes a
        constructor (__init__) with the same signature as the
        base Exporter class.
        
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
        specifies what extension the output should be saved as.
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


def export_sphinx_manual(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to Sphinx Manual LaTeX
    
    Parameters
    ----------
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
        specifies what extension the output should be saved as.
    """
    return export(nb, config, transformers, filters, SphinxManualExporter)


def export_sphinx_howto(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to Sphinx HowTo LaTeX
    
    Parameters
    ----------
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
        specifies what extension the output should be saved as.
    """
    return export(nb, config, transformers, filters, SphinxHowtoExporter)


def export_basic_html(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to Basic HTML
    
    Parameters
    ----------
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
        specifies what extension the output should be saved as.
    """
    return export(nb, config, transformers, filters, BasicHtmlExporter)


def export_full_html(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to Full HTML
    
    Parameters
    ----------
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
        specifies what extension the output should be saved as.
    """
    return export(nb, config, transformers, filters, FullHtmlExporter)


def export_latex(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to LaTeX
    
    Parameters
    ----------
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
        specifies what extension the output should be saved as.
    """
    return export(nb, config, transformers, filters, LatexExporter)


def export_markdown(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to Markdown
    
    Parameters
    ----------
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
        specifies what extension the output should be saved as.
    """
    return export(nb, config, transformers, filters, MarkdownExporter)


def export_python(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to Python
    
    Parameters
    ----------
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
        specifies what extension the output should be saved as.
    """
    return export(nb, config, transformers, filters, PythonExporter)


def export_python_armor(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to Python (Armor)
    
    Parameters
    ----------
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
        specifies what extension the output should be saved as.
    """
    return export(nb, config, transformers, filters, PythonArmorExporter)


def export_reveal(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to Reveal
    
    Parameters
    ----------
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
        specifies what extension the output should be saved as.
    """
    return export(nb, config, transformers, filters, RevealExporter)


def export_rst(nb, config=None, transformers=None, filters=None):
    """
    Export a notebook object to RST
    
    Parameters
    ----------
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
        specifies what extension the output should be saved as.
    """
    return export(nb, config, transformers, filters, RstExporter)


def export_by_name(nb, template_name, config=None, transformers=None, filters=None):
    """
    Export a notebook object to a template type by its name.  Reflection
    (Inspect) is used to find the template's corresponding explicit export
    method defined in this module.  That method is then called directly.
    
    Parameters
    ----------
    template_name : str
        Name of the template style to export to.
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
    tuple- (output, resources, exporter_instance)
    None- if template not found
    
    output : str
        Jinja 2 output.  This is the resulting converted notebook.
    resources : dictionary
        Dictionary of resources used prior to and during the conversion 
        process.
    exporter_instance : Exporter
        Instance of the Exporter class used to export the document.  Useful
        to caller because it provides a 'file_extension' property which
        specifies what extension the output should be saved as.
    """
    
    #Use reflection to get functions defined in this module.
    cls_functions = inspect.getmembers(sys.modules[__name__], inspect.isfunction)
    
    #Check if the characters following "export_" (7 char) equals the template name.
    for (function_name, function_handle) in cls_functions:
        function_name = function_name.lower() 
        if (len(function_name) > 7 and function_name[7:] == template_name.lower()):
            return function_handle(nb, config, transformers, filters)
        
    return None
            