"""Latex transformer.

Module that allows latex output notebooks to be conditioned before
they are converted.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from .exporter import Exporter

from .html import HtmlExporter
from .latex import LatexExporter
from .markdown import MarkdownExporter
from .python import PythonExporter
from .reveal import RevealExporter
from .rst import RstExporter
from .sphinx import SphinxExporter

from IPython.nbformat.v3.nbbase import NotebookNode

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def export(nb, config=None, transformers=None, filters=None, exporter_type=Exporter):
    
    #Check arguments
    if exporter_type is None:
        raise TypeError("Exporter is None")
    elif not issubclass(exporter_type, Exporter):
        raise TypeError("Exporter type does not inherit from Exporter (base)")
    
    if nb is None:
        raise TypeError("nb is None")
    
    #Create the exporter
    exporter_instance = exporter_type(preprocessors=transformers, jinja_filters=filters, config=config)

    #Try to convert the notebook using the appropriate conversion function.
    if isinstance(nb, NotebookNode):
        output, resources = exporter_instance.from_notebook_node(nb)
    elif isinstance(nb, basestring):
        output, resources = exporter_instance.from_filename(nb)
    else:
        output, resources = exporter_instance.from_file(nb)
    return output, resources, exporter_instance


def export_sphinx(nb, config=None, transformers=None, filters=None):
    return export(nb, config, transformers, filters, SphinxExporter)

def export_html(nb, config=None, transformers=None, filters=None):
    return export(nb, config, transformers, filters, HtmlExporter)

def export_latex(nb, config=None, transformers=None, filters=None):
    return export(nb, config, transformers, filters, LatexExporter)

def export_markdown(nb, config=None, transformers=None, filters=None):
    return export(nb, config, transformers, filters, MarkdownExporter)

def export_python(nb, config=None, transformers=None, filters=None):
    return export(nb, config, transformers, filters, PythonExporter)

def export_reveal(nb, config=None, transformers=None, filters=None):
    return export(nb, config, transformers, filters, RevealExporter)

def export_rst(nb, config=None, transformers=None, filters=None):
    return export(nb, config, transformers, filters, RstExporter)

EXPORT_FUNCTIONS = {"sphinx": export_sphinx,
                    "html": export_html,
                    "latex": export_latex,
                    "markdown": export_markdown,
                    "python": export_python,
                    "reveal": export_reveal,
                    "rst": export_rst}

def export_by_name(nb, template_name, config=None, transformers=None, filters=None):
    return EXPORT_FUNCTIONS[template_name](nb, config, transformers, filters)