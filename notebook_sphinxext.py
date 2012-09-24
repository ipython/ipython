import sys
import os.path
import re
import time
from docutils import io, nodes, statemachine, utils
from docutils.error_reporting import ErrorString
from docutils.parsers.rst import Directive, convert_directive_function
from docutils.parsers.rst import directives, roles, states
from docutils.parsers.rst.roles import set_classes
from docutils.transforms import misc

from nbconvert import ConverterHTML


class Notebook(Directive):
    """
    Use nbconvert to insert a notebook into the environment.
    This is based on the Raw directive in docutils
    """
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {}
    has_content = False

    def run(self):
        if (not self.state.document.settings.raw_enabled
            or (not self.state.document.settings.file_insertion_enabled
                and ('file' in self.options
                     or 'url' in self.options))):
            raise self.warning('"%s" directive disabled.' % self.name)
        attributes = {'format': 'html'}
        encoding = self.options.get(
            'encoding', self.state.document.settings.input_encoding)
        e_handler = self.state.document.settings.input_encoding_error_handler

        # get path to notebook
        source_dir = os.path.dirname(
            os.path.abspath(self.state.document.current_source))
        path = os.path.normpath(os.path.join(source_dir,
                                             self.arguments[0]))
        path = utils.relative_path(None, path)

        # convert notebook to html
        converter = ConverterHTML(path)
        htmlfname = converter.render()
        htmlpath = utils.relative_path(None, htmlfname)

        try:
            raw_file = io.FileInput(source_path=htmlpath,
                                    encoding=encoding,
                                    error_handler=e_handler)
            # TODO: currently, raw input files are recorded as
            # dependencies even if not used for the chosen output format.
            self.state.document.settings.record_dependencies.add(htmlpath)
        except IOError, error:
            raise self.severe(u'Problems with "%s" directive path:\n%s.'
                              % (self.name, ErrorString(error)))
        try:
            text = raw_file.read()
        except UnicodeError, error:
            raise self.severe(u'Problem with "%s" directive:\n%s'
                              % (self.name, ErrorString(error)))
        attributes['source'] = htmlpath

        nb_node = notebook('', text, **attributes)
        (nb_node.source,
        nb_node.line) = self.state_machine.get_source_and_line(self.lineno)
        return [nb_node]


class notebook(nodes.raw):
    pass


def visit_notebook_node(self, node):
    self.visit_raw(node)


def depart_notebook_node(self, node):
    self.depart_raw(node)


def setup(app):
    app.add_node(notebook,
                 html=(visit_notebook_node, depart_notebook_node))

    app.add_directive('notebook', Notebook)
