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
        self.section_level = 0
        ws = nbformat.new_worksheet()
        self.nb = nbformat.new_notebook(worksheets=[ws])

    def astext(self):
        return '{0}'.format(nbformat.writes(self.nb, 'ipynb'))

    def is_ref_error_paragraph(self, p):
        return p == "Unknown interpreted text role \"ref\"."

    def add_cell(self, cell):
        self.nb.worksheets[0].cells.append(cell)

    def visit_Text(self, node):
        self.default_visit(node)

    def depart_Text(self, node):
        self.default_depart(node)

    def visit_abbreviation(self, node):
        self.default_visit(node)

    def depart_abbreviation(self, node):
        self.default_depart(node)

    def visit_acronym(self, node):
        self.default_visit(node)

    def depart_acronym(self, node):
        self.default_depart(node)

    def visit_address(self, node):
        self.default_visit(node)

    def depart_address(self, node):
        self.default_depart(node)

    def visit_admonition(self, node):
        self.default_visit(node)

    def depart_admonition(self, node):
        self.default_depart(node)

    def visit_attribution(self, node):
        self.default_visit(node)

    def depart_attribution(self, node):
        self.default_depart(node)

    def visit_author(self, node):
        self.default_visit(node)

    def depart_author(self, node):
        self.default_depart(node)

    def visit_authors(self, node):
        self.default_visit(node)

    def depart_authors(self, node):
        self.default_depart(node)

    def visit_block_quote(self, node):
        self.default_visit(node)

    def depart_block_quote(self, node):
        self.default_depart(node)

    def visit_bullet_list(self, node):
        self.default_visit(node)

    def depart_bullet_list(self, node):
        self.default_depart(node)

    def visit_caption(self, node):
        self.default_visit(node)

    def depart_caption(self, node):
        self.default_depart(node)

    def visit_citation(self, node):
        self.default_visit(node)

    def depart_citation(self, node):
        self.default_depart(node)

    def visit_citation_reference(self, node):
        self.default_visit(node)

    def depart_citation_reference(self, node):
        self.default_depart(node)

    def visit_classifier(self, node):
        self.default_visit(node)

    def depart_classifier(self, node):
        self.default_depart(node)

    def visit_colspec(self, node):
        self.default_visit(node)

    def depart_colspec(self, node):
        self.default_depart(node)

    def visit_comment(self, node):
        self.default_visit(node)

    def depart_comment(self, node):
        self.default_depart(node)

    def visit_compound(self, node):
        self.default_visit(node)

    def depart_compound(self, node):
        self.default_depart(node)

    def visit_container(self, node):
        self.default_visit(node)

    def depart_container(self, node):
        self.default_depart(node)

    def visit_contact(self, node):
        self.default_visit(node)

    def depart_contact(self, node):
        self.depart_docinfo_item()

    def visit_copyright(self, node):
        self.default_visit(node)

    def depart_copyright(self, node):
        self.default_depart(node)

    def visit_date(self, node):
        self.default_visit(node)

    def depart_date(self, node):
        self.default_depart(node)

    def visit_decoration(self, node):
        self.default_visit(node)

    def depart_decoration(self, node):
        self.default_depart(node)

    def visit_definition(self, node):
        self.default_visit(node)

    def depart_definition(self, node):
        self.default_depart(node)

    def visit_definition_list(self, node):
        self.default_visit(node)

    def depart_definition_list(self, node):
        self.default_depart(node)

    def visit_definition_list_item(self, node):
        self.default_visit(node)

    def depart_definition_list_item(self, node):
        self.default_depart(node)

    def visit_description(self, node):
        self.default_visit(node)

    def depart_description(self, node):
        self.default_depart(node)

    def visit_docinfo(self, node):
        self.default_visit(node)

    def depart_docinfo(self, node):
        self.default_depart(node)

    def visit_docinfo_item(self, node):
        self.default_visit(node)

    def depart_docinfo_item(self):
        self.default_depart(node)

    def visit_doctest_block(self, node):
        self.default_visit(node)

    def depart_doctest_block(self, node):
        self.default_depart(node)

    def visit_document(self, node):
        self.default_visit(node)

    def depart_document(self, node):
        self.default_depart(node)

    def visit_emphasis(self, node):
        self.default_visit(node)

    def depart_emphasis(self, node):
        self.default_depart(node)

    def visit_entry(self, node):
        self.default_visit(node)

    def depart_entry(self, node):
        self.default_depart(node)

    def visit_enumerated_list(self, node):
        self.default_visit(node)

    def depart_enumerated_list(self, node):
        self.default_depart(node)

    def visit_field(self, node):
        self.default_visit(node)

    def depart_field(self, node):
        self.default_depart(node)

    def visit_field_body(self, node):
        self.default_visit(node)

    def depart_field_body(self, node):
        self.default_depart(node)

    def visit_field_list(self, node):
        self.default_visit(node)

    def depart_field_list(self, node):
        self.default_depart(node)

    def visit_field_name(self, node):
        self.default_visit(node)

    def depart_field_name(self, node):
        self.default_depart(node)

    def visit_figure(self, node):
        self.default_visit(node)

    def depart_figure(self, node):
        self.default_depart(node)

    def visit_footer(self, node):
        self.default_visit(node)

    def depart_footer(self, node):
        self.default_depart(node)

    def visit_footnote(self, node):
        self.default_visit(node)

    def depart_footnote(self, node):
        self.default_depart(node)

    def visit_footnote_reference(self, node):
        self.default_visit(node)

    def depart_footnote_reference(self, node):
        self.default_depart(node)

    def visit_generated(self, node):
        self.default_visit(node)

    def depart_generated(self, node):
        self.default_depart(node)

    def visit_header(self, node):
        self.default_visit(node)

    def depart_header(self, node):
        self.default_depart(node)

    def visit_image(self, node):
        self.default_visit(node)

    def depart_image(self, node):
        self.default_depart(node)

    def visit_inline(self, node):
        self.default_visit(node)

    def depart_inline(self, node):
        self.default_depart(node)

    def visit_label(self, node):
        self.default_visit(node)

    def depart_label(self, node):
        self.default_depart(node)

    def visit_legend(self, node):
        self.default_visit(node)

    def depart_legend(self, node):
        self.default_depart(node)

    def visit_line(self, node):
        self.default_visit(node)

    def depart_line(self, node):
        self.default_depart(node)

    def visit_line_block(self, node):
        self.default_visit(node)

    def depart_line_block(self, node):
        self.default_depart(node)

    def visit_list_item(self, node):
        self.default_visit(node)

    def depart_list_item(self, node):
        self.default_depart(node)

    def visit_literal(self, node):
        self.default_visit(node)

    def depart_literal(self, node):
        self.default_depart(node)

    def visit_literal_block(self, node):
        raw_text = node.astext()
        #only include lines that begin with >>>
        #we want the example code and not the example output
        processed_text = '\n'.join([line.split('>>>')[1][1:]
                                    for line in raw_text.split('\n')
                                    if line.startswith('>>>')])
        c = nbformat.new_code_cell(input=processed_text)
        self.add_cell(c)

    def depart_literal_block(self, node):
        self.default_depart(node)

    def visit_math(self, node):
        self.default_visit(node)

    def depart_math(self, node):
        self.default_depart(node)

    def visit_math_block(self, node):
        self.default_visit(node)

    def depart_math_block(self, node):
        self.default_depart(node)

    def visit_meta(self, node):
        self.default_visit(node)

    def depart_meta(self, node):
        self.default_depart(node)

    def visit_option(self, node):
        self.default_visit(node)

    def depart_option(self, node):
        self.default_depart(node)

    def visit_option_argument(self, node):
        self.default_visit(node)

    def depart_option_argument(self, node):
        self.default_depart(node)

    def visit_option_group(self, node):
        self.default_visit(node)

    def depart_option_group(self, node):
        self.default_depart(node)

    def visit_option_list(self, node):
        self.default_visit(node)

    def depart_option_list(self, node):
        self.default_depart(node)

    def visit_option_list_item(self, node):
        self.default_visit(node)

    def depart_option_list_item(self, node):
        self.default_depart(node)

    def visit_option_string(self, node):
        self.default_visit(node)

    def depart_option_string(self, node):
        self.default_depart(node)

    def visit_organization(self, node):
        self.default_visit(node)

    def depart_organization(self, node):
        self.default_depart(node)

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

    def depart_paragraph(self, node):
        self.default_depart(node)

    def visit_problematic(self, node):
        self.default_visit(node)

    def depart_problematic(self, node):
        self.default_depart(node)

    def visit_raw(self, node):
        self.default_visit(node)

    def depart_raw(self, node):
        self.default_depart(node)

    def visit_reference(self, node):
        self.default_visit(node)

    def depart_reference(self, node):
        self.default_depart(node)

    def visit_revision(self, node):
        self.default_visit(node)

    def depart_revision(self, node):
        self.default_depart(node)

    def visit_row(self, node):
        self.default_visit(node)

    def depart_row(self, node):
        self.default_depart(node)

    def visit_rubric(self, node):
        self.default_visit(node)

    def depart_rubric(self, node):
        self.default_depart(node)

    def visit_section(self, node):
        self.section_level += 1
        self.default_visit(node)

    def depart_section(self, node):
        self.section_level -= 1
        self.default_depart(node)

    def visit_sidebar(self, node):
        self.default_visit(node)

    def depart_sidebar(self, node):
        self.default_depart(node)

    def visit_status(self, node):
        self.default_visit(node)

    def depart_status(self, node):
        self.default_depart(node)

    def visit_strong(self, node):
        self.default_visit(node)

    def depart_strong(self, node):
        self.default_depart(node)

    def visit_subscript(self, node):
        self.default_visit(node)

    def depart_subscript(self, node):
        self.default_depart(node)

    def visit_substitution_definition(self, node):
        self.default_visit(node)

    def depart_substitution_definition(self, node):
        self.default_depart(node)

    def visit_substitution_reference(self, node):
        self.default_visit(node)

    def depart_substitution_reference(self, node):
        self.default_depart(node)

    def visit_subtitle(self, node):
        self.default_visit(node)

    def depart_subtitle(self, node):
        self.default_depart(node)

    def visit_superscript(self, node):
        self.default_visit(node)

    def depart_superscript(self, node):
        self.default_depart(node)

    def visit_system_message(self, node):
        self.default_visit(node)

    def depart_system_message(self, node):
        self.default_depart(node)

    def visit_table(self, node):
        self.default_visit(node)

    def depart_table(self, node):
        self.default_depart(node)

    def visit_target(self, node):
        self.default_visit(node)

    def depart_target(self, node):
        self.default_depart(node)

    def visit_tbody(self, node):
        self.default_visit(node)

    def depart_tbody(self, node):
        self.default_depart(node)

    def visit_term(self, node):
        self.default_visit(node)

    def depart_term(self, node):
        self.default_depart(node)

    def visit_tgroup(self, node):
        self.default_visit(node)

    def depart_tgroup(self, node):
        self.default_depart(node)

    def visit_thead(self, node):
        self.default_visit(node)

    def depart_thead(self, node):
        self.default_depart(node)

    def visit_title(self, node):
        #make sure we have a valid heading level between 1 and 6
        heading_level = min(self.section_level, 5) + 1
        h = nbformat.new_heading_cell(source=node.astext(),
                                      level=heading_level)
        self.add_cell(h)

    def depart_title(self, node):
        self.default_depart(node)

    def visit_title_reference(self, node):
        self.default_visit(node)

    def depart_title_reference(self, node):
        self.default_depart(node)

    def visit_topic(self, node):
        self.default_visit(node)

    def depart_topic(self, node):
        self.default_depart(node)

    def visit_transition(self, node):
        self.default_visit(node)

    def depart_transition(self, node):
        self.default_depart(node)

    def visit_version(self, node):
        self.default_visit(node)

    def depart_version(self, node):
        self.default_depart(node)

    def default_visit(self, node):
        node_class = node.__class__.__name__
        #print '*default_visit', node_class
        #if node_class in ['reference','paragraph','literal_block','title']:
        if node_class in []:
            print '*default_visit', node_class
            print node.astext()

    def default_depart(self, node):
        #print '*default depart', node.__class__.__name__
        pass
