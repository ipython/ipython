from __future__ import absolute_import

from .html import ConverterHTML
from .utils import text_cell
from .utils import highlight, coalesce_streams

from IPython.utils import path
from markdown import markdown

import os
import io
import itertools


class ConverterReveal(ConverterHTML):
    """
     Convert a ipython notebook to a html slideshow
     based in reveal.js library.
    """

    @text_cell
    def render_heading(self, cell):
        marker = cell.level
        return [self.meta2str(cell.metadata),
                u'<h{1}>\n  {0}\n</h{1}>'.format(cell.source, marker)]

    def render_code(self, cell):
        if not cell.input:
            return []
        lines = []
        meta_code = self.meta2str(cell.metadata)
        lines.extend([meta_code])
        lines.extend(['<div class="cell border-box-sizing code_cell vbox">'])
        lines.append('<div class="input hbox">')
        n = self._get_prompt_number(cell)
        lines.append(
            '<div class="prompt input_prompt">In&nbsp;[%s]:</div>' % n
        )
        lines.append('<div class="input_area box-flex1">')
        lines.append(highlight(cell.input))
        lines.append('</div>')  # input_area
        lines.append('</div>')  # input
        if cell.outputs:
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
        return [self.meta2str(cell.metadata), markdown(cell.source)]

    def render_raw(self, cell):
        if self.raw_as_verbatim:
            return [self.in_tag('pre', self.meta2str(cell.metadata)),
                    self.in_tag('pre', cell.source)]
        else:
            return [self.meta2str(cell.metadata), cell.source]

    def meta2str(self, meta):
        "transform metadata dict (containing slides delimiters) to string "
        try:
            meta_tuple = meta[u'slideshow'].items()
        except KeyError as e:  # if there is not slideshow metadata
            meta_tuple = [(u'slide_type', u'untouched')]
        meta_list = [[x + ' = ' + unicode(y)] for x, y in meta_tuple]
        return u'\n'.join(list(itertools.chain(*meta_list)))

    def convert(self, cell_separator='\n'):
        """
        Specific method to converts notebook to a string representation.

        Parameters
        ----------
        cell_separator : string
          Character or string to join cells with. Default is "\n"

        Returns
        -------
        out : string
        """

        lines = []
        lines.extend(self.optional_header())
        begin = ['<div class="reveal"><div class="slides">']
        lines.extend(begin)
        slides_list = self.build_slides()
        lines.extend(slides_list)
        end = ['</div></div>']
        lines.extend(end)
        lines.extend(self.optional_footer())
        return u'\n'.join(lines)

    def clean_text(self, cell_separator='\n'):
        "clean and reorganize the text list to be slided"
        text = self.main_body(cell_separator)
        self.delim = [u'slide_type = untouched',
                      u'slide_type = -',
                      u'slide_type = slide',
                      u'slide_type = subslide',
                      u'slide_type = fragment',
                      u'slide_type = notes',
                      u'slide_type = skip']  # keep this one the last
        text_cell_render = \
            u'<div class="text_cell_render border-box-sizing rendered_html">'
        for i, j in enumerate(text):
            if j in self.delim and text[i - 1] == text_cell_render:
                if j == self.delim[0]:
                    text[i - 1] = self.delim[0]
                elif j == self.delim[1]:
                    text[i - 1] = self.delim[1]
                elif j == self.delim[2]:
                    text[i - 1] = self.delim[2]
                elif j == self.delim[3]:
                    text[i - 1] = self.delim[3]
                elif j == self.delim[4]:
                    text[i - 1] = self.delim[4]
                elif j == self.delim[5]:
                    text[i - 1] = self.delim[5]
                else:
                    text[i - 1] = self.delim[6]
                text[i] = text_cell_render
        return text

    def build_slides(self):
        "build the slides structure from text list and delimiters"
        text = self.clean_text()
        left = '<section>'
        right = '</section>'
        notes_start = '<aside class="notes">'
        notes_end = '</aside>'
        #encapsulation of skipped cells
        for i, j in enumerate(text):
            if j == u'slide_type = skip':
                text.pop(i)
                text[i] = text[i][:4] + \
                    ' style=display:none' + text[i][4:]
        #encapsulation of notes cells
        for i, j in enumerate(text):
            if j == u'slide_type = notes':
                text.pop(i)
                temp_list = []
                while not text[i] in self.delim[:6]:
                    temp_list.append(text.pop(i))
                else:
                    temp_list.insert(0, notes_start)
                    temp_list.append(notes_end)
                    text[i:i] = temp_list
        # elimination of none names
        for i, j in enumerate(text):
            if j in [u'slide_type = untouched', u'slide_type = -']:
                text.pop(i)
        #generation of slides as a list of list
        slides = [list(x[1]) for x in itertools.groupby(text,
            lambda x: x == u'slide_type = slide') if not x[0]]
        for slide in slides:
            slide.insert(0, left)
            slide.append(right)
            # encapsulation of each fragment
            for i, j in enumerate(slide):
                if j == u'slide_type = fragment':
                    slide.pop(i)
                    slide[i] = slide[i][:4] + \
                        ' class="fragment"' + slide[i][4:]
            # encapsulation of each nested slide
            if u'slide_type = subslide' in slide:
                slide.insert(0, left)
                slide.append(right)
            for i, j in enumerate(slide):
                if j == u'slide_type = subslide':
                    slide[i] = right + left
        return list(itertools.chain(*slides))

    def render(self):
        "read, convert, and save self.infile"
        if not hasattr(self, 'nb'):
            self.read()
        self.output = self.convert()
        assert(type(self.output) == unicode)
        return self.save()

    def save(self, outfile=None, encoding=None):
        "read and parse notebook into self.nb"
        if outfile is None:
            outfile = self.outbase + '_slides.' + 'html'
        if encoding is None:
            encoding = self.default_encoding
        with io.open(outfile, 'w', encoding=encoding) as f:
            f.write(self.output)
        return os.path.abspath(outfile)

    def header_body(self):
        "return the body of the header as a list of strings"
        from pygments.formatters import HtmlFormatter
        header = []
        static = os.path.join(path.get_ipython_package_dir(),
        'frontend', 'html', 'notebook', 'static',)
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
            os.path.join(here, '..', 'css', 'reveal_html.css'),
        ]:
            header.extend(self._stylesheet(sheet))
        # pygments css
        pygments_css = HtmlFormatter().get_style_defs('.highlight')
        header.extend(['<meta charset="UTF-8">'])
        header.extend(self.in_tag('style', pygments_css,
                                  dict(type='"text/css"')))
        return header

    def template_read(self, templ):
        "read the reveal_template.html"
        here = os.path.split(os.path.realpath(__file__))[0]
        reveal_template = os.path.join(here, '..', 'templates',
            templ)
        with io.open(reveal_template, 'r', encoding='utf-8') as f:
            template = f.readlines()
        template = [s.strip() for s in template]
        return template

    def template_split(self):
        "split the reveal_template.html in header and footer lists"
        temp = self.template_read('reveal_base.html')
        splitted_temp = [list(x[1]) for x in itertools.groupby(temp,
            lambda x: x == u'%slides%') if not x[0]]
        return splitted_temp

    def optional_header(self):
        optional_header_body = self.template_split()
        return ['<!DOCTYPE html>', '<html>', '<head>'] + \
                optional_header_body[0] + self.header_body() + \
               ['</head>', '<body>']

    def optional_footer(self):
        optional_footer_body = self.template_split()
        return optional_footer_body[1] + ['</body>', '</html>']
