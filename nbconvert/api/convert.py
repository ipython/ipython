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

def load_class(template_name):
    class_name = template_name[0].upper() + template_name[1:] + "Exporter"
    module = __import__('nbconvert.api.' + template_name, fromlist=[class_name])                                       
    return getattr(module, class_name)

def export_by_name(nb, template_name, config=None, transformers=None, filters=None):
    return export(nb, config, transformers, filters, load_class(template_name))