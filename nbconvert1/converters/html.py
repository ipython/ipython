"""Implements conversion to ordinary HTML output.

This file implements a class that handles rendering IPython notebooks as
HTML, suitable for posting to the web.

Converters for more specific HTML generation needs (suitable for posting to
a particular web service) can usefully subclass `ConverterHTML` and override
certain methods. For output tuned to the Blogger blogging platform, see the
`ConverterBloggerHTML` class.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2012, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from __future__ import absolute_import

# Stdlib imports
import io
import os

# Third-party imports
from markdown import markdown

# IPython imports
from IPython.utils import path
from IPython.frontend.html.notebook import notebookapp

# Our own imports
from .base import Converter
from .utils import text_cell, output_container
from .utils import highlight, coalesce_streams, ansi2html


#-----------------------------------------------------------------------------
# Class declarations
#-----------------------------------------------------------------------------

class ConverterHTML(Converter):
    #-------------------------------------------------------------------------
    # Class-level attributes determining the behaviour of the class but
    # probably not varying from instance to instance.
    #-------------------------------------------------------------------------
    extension = 'html'
    blank_symbol = '&nbsp;'

    def in_tag(self, tag, src, attrs=None):
        """Return a list of elements bracketed by the given tag"""
        attr_s = '' if attrs is None else \
                 ' '.join("%s=%s" % (attr, value)
                          for attr, value in attrs.iteritems())
        return ['<%s %s>' % (tag, attr_s), src, '</%s>' % tag]

    def _ansi_colored(self, text):
        return ['<pre>%s</pre>' % ansi2html(text)]

    def _stylesheet(self, fname):
        with io.open(fname, encoding='utf-8') as f:
            s = f.read()
        return self.in_tag('style', s, dict(type='"text/css"'))

    def _out_prompt(self, output):
        if output.output_type == 'pyout':
            content = 'Out[%s]:' % self._get_prompt_number(output)
        else:
            content = ''
        return ['<div class="prompt output_prompt">%s</div>' % content]

    def header_body(self):
        """Return the body of the header as a list of strings."""

        from pygments.formatters import HtmlFormatter

        header = []
        static = getattr(notebookapp, 'DEFAULT_STATIC_FILES_PATH', None)
        # ipython < 1.0
        if static is None:
            static = os.path.join(path.get_ipython_package_dir(),
            'frontend', 'html', 'notebook', 'static',
            )
        here = os.path.split(os.path.realpath(__file__))[0]
        css = os.path.join(static, 'css')
        for sheet in [
            # do we need jquery and prettify?
            # os.path.join(static, 'jquery', 'css', 'themes', 'base',
            # 'jquery-ui.min.css'),
            # os.path.join(static, 'prettify', 'prettify.css'),
            os.path.join(css, 'boilerplate.css'),
            os.path.join(css, 'style.min.css'),
            # our overrides:
            os.path.join(here, '..', 'css', 'static_html.css'),
        ]:
            header.extend(self._stylesheet(sheet))

        # pygments css
        pygments_css = HtmlFormatter().get_style_defs('.highlight')
        header.extend(['<meta charset="UTF-8">'])
        header.extend(self.in_tag('style', pygments_css,
                                  dict(type='"text/css"')))

        # TODO: this should be allowed to use local mathjax:
        header.extend(self.in_tag('script', '', {'type': '"text/javascript"',
            'src': '"https://c328740.ssl.cf1.rackcdn.com/mathjax/'
                   'latest/MathJax.js?config=TeX-AMS_HTML"',
        }))
        with io.open(os.path.join(here, '..', 'js', 'initmathjax.js'),
                     encoding='utf-8') as f:
            header.extend(self.in_tag('script', f.read(),
                                      {'type': '"text/javascript"'}))
        return header

    def optional_header(self):
        return ['<html>', '<head>'] + self.header_body() + \
          ['</head>', '<body>']

    def optional_footer(self):
        return ['</body>', '</html>']

    @text_cell
    def render_heading(self, cell):
        marker = cell.level
        return [u'<h{1}>\n  {0}\n</h{1}>'.format(cell.source, marker)]

    def render_code(self, cell):
        if not cell.input:
            return []

        lines = ['<div class="cell border-box-sizing code_cell vbox">']
        if 'source' not in self.exclude_cells:

            lines.append('<div class="input hbox">')
            n = self._get_prompt_number(cell)
            lines.append(
                '<div class="prompt input_prompt">In&nbsp;[%s]:</div>' % n
            )
            lines.append('<div class="input_area box-flex1">')
            lines.append(highlight(cell.input) if self.highlight_source
                         else cell.input)
            lines.append('</div>')  # input_area
            lines.append('</div>')  # input

        if cell.outputs and 'output' not in self.exclude_cells:
            lines.append('<div class="vbox output_wrapper">')
            lines.append('<div class="output vbox">')

            for output in coalesce_streams(cell.outputs):
                conv_fn = self.dispatch(output.output_type)
                lines.extend(conv_fn(output))

            lines.append('</div>')  # output
            lines.append('</div>')  # output_wrapper

        lines.append('</div>')  # cell

        return lines


    @text_cell
    def render_markdown(self, cell):
        return [markdown(cell.source)]

    def render_raw(self, cell):
        if self.raw_as_verbatim:
            return self.in_tag('pre', cell.source)
        else:
            return [cell.source]

    @output_container
    def render_pyout(self, output):
        for fmt in ['html', 'latex', 'png', 'jpeg', 'svg', 'text']:
            if fmt in output:
                conv_fn = self.dispatch_display_format(fmt)
                return conv_fn(output)
        return []

    render_display_data = render_pyout

    @output_container
    def render_stream(self, output):
        return self._ansi_colored(output.text)

    @output_container
    def render_pyerr(self, output):
        # Note: a traceback is a *list* of frames.
        # lines = []

        # stb =
        return self._ansi_colored('\n'.join(output.traceback))

    def _img_lines(self, img_file):
        return ['<img src="%s">' % img_file, '</img>']

    def _unknown_lines(self, data):
        return ['<h2>Warning:: Unknown cell</h2>'] + self.in_tag('pre', data)

    def render_display_format_png(self, output):
        return ['<img src="data:image/png;base64,%s"></img>' % output.png]

    def render_display_format_svg(self, output):
        return [output.svg]

    def render_display_format_jpeg(self, output):
        return ['<img src="data:image/jpeg;base64,%s"></img>' % output.jpeg]

    def render_display_format_text(self, output):
        return self._ansi_colored(output.text)

    def render_display_format_html(self, output):
        return [output.html]

    def render_display_format_latex(self, output):
        return [output.latex]

    def render_display_format_json(self, output):
        # html ignores json
        return []

    def render_display_format_javascript(self, output):
        return [output.javascript]
