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

import os
import urllib2

from .base import Transformer
from IPython.utils.traitlets import Unicode, Bool

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class RevealHelpTransformer(Transformer):

    url_prefix = Unicode('//cdn.jsdelivr.net/reveal.js/2.4.0',
                         config=True,
                         help="""If you want to use a local reveal.js library,
                         use 'url_prefix':'reveal.js' in your config object.""")

    speaker_notes = Bool(False, 
                         config=True, 
                         help="""If you want to use the speaker notes 
                         set this to True.""")

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


        if not isinstance(resources['reveal'], dict):
            resources['reveal'] = {}
        resources['reveal']['url_prefix'] = self.url_prefix
        resources['reveal']['notes_prefix'] = self.url_prefix

        cdn = 'http://cdn.jsdelivr.net/reveal.js/2.4.0'
        local = 'local'
        html_path = 'plugin/notes/notes.html'
        js_path = 'plugin/notes/notes.js'

        html_infile = os.path.join(cdn, html_path)
        js_infile = os.path.join(cdn, js_path)
        html_outfile = os.path.join(local, html_path)
        js_outfile = os.path.join(local, js_path)

        if self.speaker_notes:
            if 'outputs' not in resources:
                resources['outputs'] = {}
            resources['outputs'][html_outfile] = self.notes_helper(html_infile)
            resources['outputs'][js_outfile] = self.notes_helper(js_infile)
            resources['reveal']['notes_prefix'] = local

        return nb, resources

    def notes_helper(self, infile):
        """Helper function to get the content from an url."""

        content = urllib2.urlopen(infile).read()

        return content
