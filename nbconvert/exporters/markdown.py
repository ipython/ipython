"""
Exporter that will export your ipynb to Markdown.
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

class MarkdownExporter(exporter.Exporter):
    """
    Exports to a markdown document (.md)
    """
    
    file_extension = Unicode(
        'md', config=True, 
        help="Extension of the file that should be written to disk")

    template_file = Unicode(
            'markdown', config=True,
            help="Name of the template file to use")
