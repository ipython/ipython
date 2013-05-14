"""TODO: Docstring
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

# local import
import exporter
from IPython.utils.traitlets import Unicode

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class PythonExporter(exporter.Exporter):

    file_extension = Unicode(
        'py', config=True, 
        help="Extension of the file that should be written to disk")

    template_file = Unicode(
            'python', config=True,
            help="Name of the template file to use")

    def __init__(self, preprocessors=None, jinja_filters=None, config=None, armor=False, **kw):
        
        #Call base class constructor.
        super(PythonExporter, self).__init__(preprocessors, jinja_filters, config, **kw)

        #Set defaults
        self.extract_figure_transformer.enabled = False
        
