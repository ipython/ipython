"""
Exporter for exporting full HTML documents.
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
import basichtml

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class FullHtmlExporter(basichtml.BasicHtmlExporter):
    """
    Exports a full HTML document.
    """
    
    template_file = Unicode(
            'fullhtml', config=True,
            help="Name of the template file to use")    