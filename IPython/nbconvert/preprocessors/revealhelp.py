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
            # Store a list of slide_type groups which are currently open and in
            # need of closing.
            open_groups = []
            for index, cell in enumerate(worksheet.cells):
                # Make sure the cell has slideshow metadata.
                cell.metadata.align_type = cell.get('metadata', {}).get(
                    'slideshow', {}).get('align_type', 'Left')
                cell.metadata.slide_type = cell.get('metadata', {}).get(
                    'slideshow', {}).get('slide_type', '-')

                if cell.metadata.slide_type not in SLIDE_TYPES:
                    raise ValueError('Unhandled slide type {!}.'.format(
                        cell.metadata.slide_type))

                slide_type = SLIDE_TYPES[cell.metadata.slide_type]

                # Close off any groups that are still open on the previous cell, before we can go
                # ahead and create the new cell.
                worksheet.cells[index - 1].metadata.slide_post_cell_close = slide_type.close(open_groups)
                for closed_group in worksheet.cells[index - 1].metadata.slide_post_cell_close:
                    open_groups.remove(closed_group)

                # Open up any groups needed for this cell.
                cell.metadata.slide_pre_cell_open = slide_type.open(
                    open_groups)
                open_groups.extend(cell.metadata.slide_pre_cell_open)
                if slide_type.name == 'slide':
                    # Reveal's subslide functionalitya requires that the top slide is also a subslide,
                    # so ensure that each new slide is actually created as a
                    # new slide + a new subslide.
                    open_groups.append('subslide')
                    cell.metadata.slide_pre_cell_open.append('subslide')
            else:
                # Close off any remaining sections.
                cell.metadata.slide_post_cell_close = open_groups

        if not isinstance(resources['reveal'], dict):
            resources['reveal'] = {}
        resources['reveal']['url_prefix'] = self.url_prefix
        return nb, resources


class SlideType(object):
    def __init__(self, name, opens, closes=None):
        """
        Parameters
        ----------
        name : str
            The name for the slide type.
        opens : iterable of strings
            The names of the slide types which creating one of these slide types
            should open, if they are not already open.
        closes : iterable of strings, optional
            The names of the slide types which should be closed before a new slide of
            this type can be created.
        """
        self.name = name
        self.opens = opens
        self.closes = closes or []

    def close(self, currently_open_types):
        """
        Close the content which needs closing before a new slide of
        this type can be created.
        """
        closed = []
        for to_close in self.closes + [self.name]:
            if to_close in currently_open_types:
                closed.append(to_close)
        return closed

    def open(self, currently_open_types):
        """
        Start the content for this slide type, also opening up any of the
        necessary slide types from :attr:`.opens` in the given
        ``currently_open_types`` list.

        Ensure the necessary slide types have been closed before calling this
        method with the :meth:`.close` method.
        """
        opened = []
        for to_open in self.opens:
            if to_open not in currently_open_types:
                opened.append(to_open)
        return opened + [self.name]


SLIDE_TYPES = {'slide': SlideType('slide', opens=[],
                                  closes=[
                                      'fragment', 'subslide', 'notes', 'skip']),
               'subslide': SlideType('subslide', opens=['slide'],
                                     closes=['fragment', 'notes', 'skip']),
               'fragment': SlideType('fragment', opens=['slide', 'subslide'],
                                     closes=['notes', 'skip']),
               'notes': SlideType('notes', opens=['slide', 'subslide'],
                                  closes=['notes', 'skip']),
               '-': SlideType('-', opens=['slide', 'subslide'],
                              closes=['notes', 'skip']),
               'skip': SlideType('skip', opens=[],
                                 closes=['notes', 'skip']), }
