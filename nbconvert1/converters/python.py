"""Notebook export to .py source code files.

Since Python export is provided in the notebook itself (provided by classes
in `IPython.nbformat`), this class serves mainly as a base class for other
converters that may wish to implement cell-type-specific behaviors.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2012, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# IPython imports
from IPython.utils.text import indent

# Our own imports
from .base import Converter
from .utils import remove_ansi


#-----------------------------------------------------------------------------
# Class declarations
#-----------------------------------------------------------------------------
class ConverterPy(Converter):
    """
    A converter that takes a notebook and converts it to a .py file.

    What distinguishes this from PyWriter and PyReader in IPython.nbformat is
    that subclasses can specify what to do with each type of cell.
    Additionally, unlike PyWriter, this does not preserve the '# <markdown>'
    opening and closing comments style comments in favor of a cleaner looking
    python program.

    Note:
        Even though this produces a .py file, it is not guaranteed to be valid
        python file, since the notebook may be using magics and even cell
        magics.
    """
    extension = 'py'

    def __init__(self, infile, highlight_source=False, show_prompts=True,
                 show_output=True, **kw):
        # Note that highlight_source is meaningless here, so even if it
        # is passed as True we ignore it and propagate False to the
        # superclass.
        super(ConverterPy, self).__init__(infile,
                                          highlight_source=False, **kw)
        self.show_prompts = show_prompts
        self.show_output = show_output

    @staticmethod
    def comment(input):
        "returns every line in input as commented out"
        return "# " + input.replace("\n", "\n# ")

    def render_heading(self, cell):
        return ['#{0} {1}'.format('#' * cell.level, cell.source), '']

    def render_code(self, cell):
        n = self._get_prompt_number(cell)
        if not cell.input:
            return []
        lines = []
        if self.show_prompts:
            lines.extend(['# In[%s]:' % n])
        src = cell.input
        lines.extend([src, ''])
        if self.show_output:
            if cell.outputs:
                lines.extend(['# Out[%s]:' % n])
            for output in cell.outputs:
                conv_fn = self.dispatch(output.output_type)
                lines.extend(conv_fn(output))
        return lines

    def render_markdown(self, cell):
        return [self.comment(cell.source), '']

    def render_raw(self, cell):
        if self.raw_as_verbatim:
            return [self.comment(indent(cell.source)), '']
        else:
            return [self.comment(cell.source), '']

    def render_pyout(self, output):
        lines = []

        ## if 'text' in output:
        ##     lines.extend(['*Out[%s]:*' % self._get_prompt_number(cell), ''])

        # output is a dictionary like object with type as a key
        if 'latex' in output:
            pass

        if 'text' in output:
            lines.extend([self.comment(indent(output.text)), ''])

        lines.append('')
        return lines

    def render_pyerr(self, output):
        # Note: a traceback is a *list* of frames.
        return [indent(remove_ansi('\n'.join(output.traceback))), '']

    def _img_lines(self, img_file):
        return [self.comment('image file: %s' % img_file), '']

    def render_display_format_text(self, output):
        return [self.comment(indent(output.text))]

    def _unknown_lines(self, data):
        return [self.comment('Warning: Unknown cell' + str(data))]

    def render_display_format_html(self, output):
        return [self.comment(output.html)]

    def render_display_format_latex(self, output):
        return []

    def render_display_format_json(self, output):
        return []

    def render_display_format_javascript(self, output):
        return []
