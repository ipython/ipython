"""
Module with tests for the revealhelp preprocessor
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

from nose.tools import assert_equal

from IPython.nbformat import current as nbformat

from .base import PreprocessorTestsBase
from ..revealhelp import RevealHelpPreprocessor


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class Testrevealhelp(PreprocessorTestsBase):
    """Contains test functions for revealhelp.py"""

    def build_notebook(self):
        """Build a reveal slides notebook in memory for use with tests.
        Overrides base in PreprocessorTestsBase"""

        outputs = [nbformat.new_output(
            output_type="stream", stream="stdout", output_text="a")]

        slide = {'slideshow': {'slide_type': 'slide'}}
        subslide = {'slideshow': {'slide_type': 'subslide'}}
        notes = {'slideshow': {'slide_type': 'notes'}}
        skip = {'slideshow': {'slide_type': 'skip'}}
        continuation = {'slideshow': {'slide_type': '-'}}
        fragment = {'slideshow': {'slide_type': 'fragment'}}

        cells = [nbformat.new_code_cell(
            input="", prompt_number=1, outputs=outputs),
            nbformat.new_text_cell(
                'markdown', source="new slide", metadata=slide),
            nbformat.new_code_cell(
                input="", prompt_number=2, outputs=outputs),
            nbformat.new_text_cell(
                'markdown', source="new fragment", metadata=fragment),
            nbformat.new_text_cell(
                'markdown', source="notes", metadata=notes),
            nbformat.new_text_cell('markdown', source="with last fragment",
                                   metadata=continuation),
            nbformat.new_text_cell(
                'markdown', source="new fragment", metadata=fragment),
            nbformat.new_text_cell(
                'markdown', source="skipped", metadata=skip),
            nbformat.new_text_cell(
                'markdown', source="new subslide", metadata=subslide),
            nbformat.new_text_cell('markdown', source="with last subslide",
                                   metadata=continuation),
        ]
        worksheets = [nbformat.new_worksheet(name="worksheet1", cells=cells)]

        return nbformat.new_notebook(name="notebook1", worksheets=worksheets)

    def build_preprocessor(self):
        """Make an instance of a preprocessor"""
        preprocessor = RevealHelpPreprocessor()
        preprocessor.enabled = True
        return preprocessor

    def test_constructor(self):
        """Can a RevealHelpPreprocessor be constructed?"""
        self.build_preprocessor()

    def test_reveal_attribute(self):
        """Make sure the reveal url_prefix resources is set"""
        nb = self.build_notebook()
        res = self.build_resources()
        preprocessor = self.build_preprocessor()
        nb, res = preprocessor(nb, res)
        assert 'reveal' in res
        assert  'url_prefix' in res['reveal']

    def test_reveal_output(self):
        """
        Make sure that the reveal preprocessor adds the appropriate metadata
        to slide_post_cell_close and slide_pre_cell_open.
        """
        nb = self.build_notebook()
        res = self.build_resources()
        preprocessor = self.build_preprocessor()
        nb, res = preprocessor(nb, res)
        cells = nb.worksheets[0].cells

        # Make sure correct metadata tags are available on every cell.
        for cell in cells:
            assert 'slide_pre_cell_open' in cell.metadata
            assert 'slide_post_cell_close' in cell.metadata

        # Check that the appropriate groups are being opened by the pre-processor
        # for certain slide type combinations. Notice how the first cell has a
        # slide type of '-' and yet still opens a new slide.
        expected_pre_cell_open = [['slide', 'subslide', '-'],
                                  ['slide', 'subslide'],
                                  ['-'],
                                  ['fragment'],
                                  ['notes'],
                                  ['-'],
                                  ['fragment'],
                                  ['skip'],
                                  ['subslide'],
                                  ['-'], ]
        for cell, expected_open in zip(cells, expected_pre_cell_open):
            assert_equal(cell.metadata.slide_pre_cell_open, expected_open)

        expected_post_cell_close = [['subslide', 'slide'],
                                    ['-'],
                                    [],
                                    [],
                                    ['notes', '-'],
                                    ['fragment'],
                                    [],
                                    ['fragment', 'skip', 'subslide'],
                                    ['-'],
                                    ['slide', 'subslide', '-'],
                                    ]
        for cell, expected_close in zip(cells, expected_post_cell_close):
            assert_equal(cell.metadata.slide_post_cell_close, expected_close)


class TestSlideTypes(Testrevealhelp):
    def create_cells(self, slide_type, pre_cell_slide_types=(), post_cell_slide_types=()):
        def build_cell(slide_type):
            if slide_type is None:
                return nbformat.new_text_cell('Slide type {!r}'.format(slide_type))
            else:
                metadata = {'slideshow': {'slide_type': slide_type}}
                return nbformat.new_text_cell(
                    'Slide type {!r}'.format(slide_type),
                    metadata=metadata)

        complete_cell_types = list(
            pre_cell_slide_types) + [slide_type] + list(post_cell_slide_types)
        cells = [build_cell(slide_type) for slide_type in complete_cell_types]
        worksheets = [nbformat.new_worksheet(name="worksheet1", cells=cells)]

        nb = nbformat.new_notebook(name="notebook1", worksheets=worksheets)
        res = self.build_resources()
        preprocessor = self.build_preprocessor()
        nb, res = preprocessor(nb, res)
        cells = nb.worksheets[0].cells
        return cells

    def assert_preprocessed_meta(self, slide_type, pre_types, post_types, opens, closes):
        cells = self.create_cells(slide_type, pre_types, post_types)
        cell = cells[len(pre_types)]
        assert_equal(cell.metadata.slide_pre_cell_open, opens)
        assert_equal(cell.metadata.slide_post_cell_close, closes)

    def test_slide_type(self):
        # Because of the reveal.js interface, a new slide should always make a
        # new subslide too.
        self.assert_preprocessed_meta('slide', [], [],
                                      opens=['slide', 'subslide'], closes=['slide', 'subslide'])
        # A slide followed by a subslide should create just one top level
        # slide.
        self.assert_preprocessed_meta('slide', [], ['subslide'],
                                      opens=['slide', 'subslide'], closes=['subslide'])
        self.assert_preprocessed_meta('slide', ['slide'], [],
                                      opens=['slide', 'subslide'], closes=['slide', 'subslide'])

    def test_subslide_type(self):
        self.assert_preprocessed_meta('subslide', [], [],
                                      opens=['slide', 'subslide'], closes=['slide', 'subslide'])
        # A subslide followed by a subslide should create just one top level
        # slide.
        self.assert_preprocessed_meta('subslide', [], ['subslide'],
                                      opens=['slide', 'subslide'], closes=['subslide'])
        self.assert_preprocessed_meta('subslide', ['subslide'], [],
                                      opens=['subslide'], closes=['slide', 'subslide'])

    def test_fragment_type(self):
        self.assert_preprocessed_meta('fragment', [], [],
                                      opens=['slide', 'subslide', 'fragment'],
                                      closes=['slide', 'subslide', 'fragment'])
        self.assert_preprocessed_meta('fragment', ['slide'], ['fragment'],
                                      opens=['fragment'], closes=['fragment'])

    def test_continuation_type(self):
        self.assert_preprocessed_meta('-', [], [],
                                      opens=['slide', 'subslide', '-'],
                                      closes=['slide', 'subslide', '-'])
        self.assert_preprocessed_meta('-', ['fragment'], ['fragment'],
                                      opens=['-'], closes=['fragment'])

    def test_notes_type(self):
        self.assert_preprocessed_meta('notes', [], [],
                                      opens=['slide', 'subslide', 'notes'],
                                      closes=['slide', 'subslide', 'notes'])
        # Fragment doesn't get closed until after the notes have been created.
        self.assert_preprocessed_meta('notes', ['fragment'], ['fragment'],
                                      opens=['notes'], closes=['notes', 'fragment'])

    def test_skip_type(self):
        self.assert_preprocessed_meta('skip', [], [],
                                      opens=['skip'],
                                      closes=['skip'])
        self.assert_preprocessed_meta('skip', ['fragment'], ['fragment'],
                                      opens=['skip'], closes=['skip', 'fragment'])
