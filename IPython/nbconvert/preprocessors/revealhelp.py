"""Module that pre-processes the notebook for export via Reveal.
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

from .base import Preprocessor
from IPython.utils.traitlets import Unicode

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class RevealHelpPreprocessor(Preprocessor):

    url_prefix = Unicode('reveal.js', config=True,
                         help="""The URL prefix for reveal.js.
                         This can be a a relative URL for a local copy of reveal.js,
                         or point to a CDN.
                         
                         For speaker notes to work, a local reveal.js prefix must be used.
                         """
    )

    def preprocess(self, nb, resources):
        """
        Called once to 'preprocess' contents of the notebook.

        Parameters
        ----------
        nb : NotebookNode
            Notebook being converted
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            preprocessors to pass variables into the Jinja engine.
        """

        for worksheet in nb.worksheets:
            for index, cell in enumerate(worksheet.cells):

                #Make sure the cell has slideshow metadata.
                cell.metadata.slide_type = cell.get('metadata', {}).get('slideshow', {}).get('slide_type', '-')

                #Get the slide type.  If type is start of subslide or slide,
                #end the last subslide/slide.
                if cell.metadata.slide_type in ['slide']:
                    worksheet.cells[index - 1].metadata.slide_helper = 'slide_end'
                if cell.metadata.slide_type in ['subslide']:
                    worksheet.cells[index - 1].metadata.slide_helper = 'subslide_end'


        if not isinstance(resources['reveal'], dict):
            resources['reveal'] = {}
        resources['reveal']['url_prefix'] = self.url_prefix
        return nb, resources
