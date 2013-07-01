"""
Exporter that exports a Python-Armor code file (.py)
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

from .python import PythonExporter

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class PythonArmorExporter(PythonExporter):
    """
    Exports a Python-Armor code file (.py)
    """

    template_file = Unicode(
            'python_armor', config=True,
            help="Name of the template file to use")
