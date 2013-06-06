"""
Python exporter which exports Notebook code into a PY file.
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

from IPython.utils.traitlets import Unicode

# local import
import exporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class PythonExporter(exporter.Exporter):
    """
    Exports a Python code file.
    """
    
    file_extension = Unicode(
        'py', config=True, 
        help="Extension of the file that should be written to disk")

    template_file = Unicode(
            'python', config=True,
            help="Name of the template file to use")


    def __init__(self, transformers=None, filters=None, config=None, **kw):
        """
        Public constructor
    
        Parameters
        ----------
        transformers : list[of transformer]
            Custom transformers to apply to the notebook prior to engaging
            the Jinja template engine.  Any transformers specified here 
            will override existing transformers if a naming conflict
            occurs.
        filters : dict{of filter}
            Custom filters to make accessible to the Jinja templates.  Any
            filters specified here will override existing filters if a
            naming conflict occurs.
        config : config
            User configuration instance.
        """
        
        #Call base class constructor.
        super(PythonExporter, self).__init__(transformers, filters, config, **kw)
