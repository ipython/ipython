# $Id$
# Author: David Goodger
# Maintainer: docutils-develop@lists.sourceforge.net
# Copyright: This module has been placed in the public domain.

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
try: # check for the Python Imaging Library
    import PIL
except ImportError:
    try:  # sometimes PIL modules are put in PYTHONPATH's root
        import Image
        class PIL(object): pass  # dummy wrapper
        PIL.Image = Image
    except ImportError:
        PIL = None
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
        self.output = '{}'.format(nbformat.writes(visitor.nb,'ipynb'))

    def assemble_parts(self):
        writers.Writer.assemble_parts(self)
        for part in self.visitor_attributes:
            self.parts[part] = ''.join(getattr(self, part))


class IPYNBTranslator(nodes.NodeVisitor):

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
        ws = nbformat.new_worksheet()
        self.nb = nbformat.new_notebook(worksheets=[ws])

    def astext(self):
        return '{}'.format(nbformat.writes(self.nb,'ipynb'))
    
    def add_cell(self, cell):
        self.nb.worksheets[0].cells.append(cell)

    def visit_Text(self, node):
        self.default_visit(node)
        #text = node.astext()
        #self.body.append(text)

    def depart_Text(self, node):
        self.default_depart(node) 

    def visit_block_quote(self, node):
        self.default_visit(node)
    #    self.body.append(self.starttag(node, 'blockquote'))

    def depart_block_quote(self, node):
        self.default_depart(node)
    #    self.body.append('</blockquote>\n')

    def visit_document(self, node):
        self.default_visit(node)
        pass

    def depart_document(self, node):
        self.default_depart(node)    

    def visit_admonition(self, node):
        self.default_visit(node)

    def depart_admonition(self, node):
        self.default_depart(node) 

    def visit_title(self, node):
        h = nbformat.new_heading_cell(source=node.astext())
        self.add_cell(h)

    def depart_title(self, node):
        self.default_depart(node) 
    
    def visit_paragraph(self, node):
        p = nbformat.new_text_cell('markdown', source=node.astext())
        self.add_cell(p)

    def depart_paragraph(self, node):
        self.default_depart(node) 

    def visit_section(self, node):
        self.default_visit(node)

    def depart_section(self, node):
        self.default_depart(node)

    def visit_emphasis(self, node):
        self.default_visit(node)

    def depart_emphasis(self, node):
        self.default_depart(node) 

    def visit_bullet_list(self, node):
        self.default_visit(node)

    def depart_bullet_list(self, node):
        self.default_depart(node) 

    def visit_list_item(self, node):
        self.default_visit(node) 

    def depart_list_item(self, node):
        self.default_depart(node)

    def visit_reference(self, node):
        self.default_visit(node)
  
    def depart_reference(self, node):
        self.default_depart(node)  

    def visit_target(self, node):
        self.default_visit(node)

    def depart_target(self, node):
        self.default_depart(node) 

    def visit_literal_block(self, node):
        raw_text = node.astext()
        #only include lines that begin with <<<<
        #we want the example code and not the example output
        processed_text = '\n'.join([line.split('>>>')[1][1:] for line in raw_text.split('\n') if line.startswith('>>>')]) 
        c = nbformat.new_code_cell(input=processed_text)
        self.add_cell(c)

    def depart_literal_block(self, node):
        self.default_depart(node) 

    def visit_inline(self, node):
        self.default_visit(node)

    def depart_inline(self, node):
        self.default_depart(node) 

    def visit_image(self, node):
        self.default_visit(node)

    def depart_image(self, node):
        self.default_depart(node) 

    def visit_topic(self, node):
        self.default_visit(node)

    def depart_topic(self, node):
        self.default_depart(node)

    def visit_title_reference(self, node):
        self.default_visit(node)

    def depart_title_reference(self, node):
        self.default_depart(node)

    def visit_strong(self, node):
        self.default_visit(node)

    def depart_strong(self, node):
        self.default_depart(node)

    def visit_problematic(self, node):
        self.default_visit(node)

    def depart_problematic(self, node):
        self.default_depart(node)

    def visit_system_message(self, node):
        self.default_visit(node)

    def depart_system_message(self, node):
        self.default_depart(node)

    def visit_literal(self, node):
        self.default_visit(node)

    def depart_literal(self, node):
        self.default_depart(node)

    def default_visit(self, node):
        node_class = node.__class__.__name__
        #print '*default_visit', node_class
        if node_class in ['title','paragraph','literal_block']:
            #print node.astext()
            pass

    def default_depart(self, node):
        #print '*default depart', node.__class__.__name__
        pass
