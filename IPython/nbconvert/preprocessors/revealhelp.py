"""Module that pre-processes the notebook for export via Reveal."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .base import Preprocessor
from IPython.utils.traitlets import Unicode


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

        for index, cell in enumerate(nb.cells):

            #Make sure the cell has slideshow metadata.
            cell.metadata.slide_type = cell.get('metadata', {}).get('slideshow', {}).get('slide_type', '-')

            # Get the slide type. If type is start, subslide, or slide,
            # end the last subslide/slide.
            if cell.metadata.slide_type in ['slide']:
                nb.cells[index - 1].metadata.slide_helper = 'slide_end'
            if cell.metadata.slide_type in ['subslide']:
                nb.cells[index - 1].metadata.slide_helper = 'subslide_end'
            # Prevent the rendering of "do nothing" cells before fragments
            # Group fragments passing frag_number to the data-fragment-index
            if cell.metadata.slide_type in ['fragment']:
                nb.cells[index].metadata.frag_number = index
                i = 1
                while i < len(nb.cells) - index:
                    nb.cells[index + i].metadata.frag_helper = 'fragment_end'
                    nb.cells[index + i].metadata.frag_number = index
                    i += 1
            # Restart the slide_helper when the cell status is changed
            # to other types.
            if cell.metadata.slide_type in ['-', 'skip', 'notes', 'fragment']:
                nb.cells[index - 1].metadata.slide_helper = '-'

        if not isinstance(resources['reveal'], dict):
            resources['reveal'] = {}
        resources['reveal']['url_prefix'] = self.url_prefix
        return nb, resources
