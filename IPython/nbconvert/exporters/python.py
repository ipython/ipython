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

from .exporter import Exporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class PythonExporter(Exporter):
    """
    Exports a Python code file.
    """
    
    file_extension = Unicode(
        'py', config=True, 
        help="Extension of the file that should be written to disk")
