"""
Simple ipython notebook document tree Writer.

"""

__docformat__ = 'reStructuredText'


import sys
import os
import os.path
import time
import re
import urllib
import docutils
from docutils import frontend, nodes, utils, writers, languages, io
from docutils.error_reporting import SafeString
from docutils.transforms import writer_aux
from docutils.math import unichar2tex, pick_math_environment
from docutils.math.latex2mathml import parse_latex_math
from docutils.math.math2html import math2html
from IPython.nbformat import current as nbformat


class Writer(writers.Writer):

    supported = ('ipynb')
    """Formats this writer supports."""

    visitor_attributes = ()

    def get_transforms(self):
        return writers.Writer.get_transforms(self) + [writer_aux.Admonitions]

    def __init__(self):
        writers.Writer.__init__(self)
        self.translator_class = IPYNBTranslator

    def translate(self):
        self.visitor = visitor = self.translator_class(self.document)
        self.document.walkabout(visitor)
        for attr in self.visitor_attributes:
            setattr(self, attr, getattr(visitor, attr))
        self.output = '{0}'.format(nbformat.writes(visitor.nb, 'ipynb'))


class IPYNBTranslator(nodes.GenericNodeVisitor):

    """
    """

    def __init__(self, document):
        nodes.NodeVisitor.__init__(self, document)
        self.settings = settings = document.settings
        lcode = settings.language_code
        self.language = languages.get_language(lcode, document.reporter)
        # A heterogenous stack used in conjunction with the tree traversal.
        # Make sure that the pops correspond to the pushes:
        self.context = []
        self.body = []
        self.section_level = 0
        ws = nbformat.new_worksheet()
        self.nb = nbformat.new_notebook(worksheets=[ws])

    def astext(self):
        return '{0}'.format(nbformat.writes(self.nb, 'ipynb'))

    def is_ref_error_paragraph(self, p):
        return p == "Unknown interpreted text role \"ref\"."

    def add_cell(self, cell):
        self.nb.worksheets[0].cells.append(cell)

    def visit_literal_block(self, node):
        raw_text = node.astext()
        #only include lines that begin with >>>
        #we want the example code and not the example output
        processed_text = '\n'.join([line.split('>>>')[1][1:]
                                    for line in raw_text.split('\n')
                                    if line.startswith('>>>')])
        c = nbformat.new_code_cell(input=processed_text)
        self.add_cell(c)

    def visit_paragraph(self, node):
        text = node.astext()
        # For every ref directive a paragraph contains
        # docutils will generate a paragraph complaining
        # "Unknown interpreted text role \"ref\"."
        # this is because ref is a sphinx directive
        # that does not exist in docutils
        # looking for a better way to handle this
        # for now filtering such pargraphs from the output

        if not self.is_ref_error_paragraph(text):
            p = nbformat.new_text_cell('markdown', source=text)
            self.add_cell(p)


    def visit_section(self, node):
        self.section_level += 1
        self.default_visit(node)

    def depart_section(self, node):
        self.section_level -= 1
        self.default_departure(node)

    def visit_title(self, node):
        #make sure we have a valid heading level between 1 and 6
        heading_level = min(self.section_level, 5) + 1
        h = nbformat.new_heading_cell(source=node.astext(),
                                      level=heading_level)
        self.add_cell(h)

    def default_visit(self, node):
        node_class = node.__class__.__name__
        #print '*default_visit', node_class
        #if node_class in ['reference','paragraph','literal_block','title']:
        if node_class in []:
            print '*default_visit', node_class
            print node.astext()

    def default_departure(self, node):
        #print '*default depart', node.__class__.__name__
        pass
