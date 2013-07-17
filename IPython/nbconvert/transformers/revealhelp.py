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

from .base import Transformer
from IPython.utils.traitlets import Unicode

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class RevealHelpTransformer(Transformer):

    url_prefix = Unicode('//cdn.jsdelivr.net/reveal.js/2.4.0',
                         config=True,
                         help="""If you want to use a local reveal.js library,
                         use 'url_prefix':'reveal.js' in your config object.""")

    def call(self, nb, resources):
        """
        Called once to 'transform' contents of the notebook.

        Parameters
        ----------
        nb : NotebookNode
            Notebook being converted
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            transformers to pass variables into the Jinja engine.
        """

        for worksheet in nb.worksheets :
            for index, cell in enumerate(worksheet.cells):

                #Make sure the cell has slideshow metadata.
                cell.metadata.align_type = cell.get('metadata', {}).get('slideshow', {}).get('align_type', 'Left')
                cell.metadata.slide_type = cell.get('metadata', {}).get('slideshow', {}).get('slide_type', '-')

                #Get the slide type.  If type is start of subslide or slide,
                #end the last subslide/slide.
                if cell.metadata.slide_type in ['slide']:
                    worksheet.cells[index - 1].metadata.slide_helper = 'slide_end'
                if cell.metadata.slide_type in ['subslide']:
                    worksheet.cells[index - 1].metadata.slide_helper = 'subslide_end'


        if 'reveal' not in resources:
            resources['reveal'] = {}
        resources['reveal']['url_prefix'] = self.url_prefix

        return nb, resources
