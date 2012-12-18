from __future__ import absolute_import

from converters.html import ConverterHTML
from converters.utils import text_cell#, output_container
from converters.utils import highlight, coalesce_streams#, ansi2html

#from IPython.utils import path
#from IPython.utils.text import indent, dedent
from markdown import markdown
import os
import io
import itertools


class ConverterReveal(ConverterHTML):
    #"""
    #Convert a notebook to a html slideshow.

    #It generates a static html slideshow based in markdown and reveal.js.
    #The delimiters for each slide, subslide, and fragment are retrieved
    #from the 'slideshow' metadata.
    #"""

    #def __init__(self):
        #super(ConverterReveal, self).__init__()

    #extension = 'html'
    #blank_symbol = '&nbsp;'

    #def in_tag(self, tag, src, attrs=None):
        #"""Return a list of elements bracketed by the given tag"""
        #attr_s = '' if attrs is None else \
                 #' '.join("%s=%s" % (attr, value)
                          #for attr, value in attrs.iteritems())
        #return ['<%s %s>' % (tag, attr_s), src, '</%s>' % tag]

    #def _ansi_colored(self, text):
        #return ['<pre>%s</pre>' % ansi2html(text)]

    #def _stylesheet(self, fname):
        #with io.open(fname, encoding='utf-8') as f:
            #s = f.read()
        #return self.in_tag('style', s, dict(type='"text/css"'))

    #def _out_prompt(self, output):
        #if output.output_type == 'pyout':
            #content = 'Out[%s]:' % self._get_prompt_number(output)
        #else:
            #content = ''
        #return ['<div class="prompt output_prompt">%s</div>' % content]

    #def header_body(self):
        #"""Return the body of the header as a list of strings."""

        #from pygments.formatters import HtmlFormatter

        #header = []
        #static = os.path.join(path.get_ipython_package_dir(),
        #'frontend', 'html', 'notebook', 'static',
        #)
        #here = os.path.split(os.path.realpath(__file__))[0]
        #css = os.path.join(static, 'css')
        #for sheet in [
            ## do we need jquery and prettify?
            ## os.path.join(static, 'jquery', 'css', 'themes', 'base',
            ## 'jquery-ui.min.css'),
            ## os.path.join(static, 'prettify', 'prettify.css'),
            #os.path.join(css, 'boilerplate.css'),
            #os.path.join(css, 'fbm.css'),
            #os.path.join(css, 'notebook.css'),
            #os.path.join(css, 'renderedhtml.css'),
            ## our overrides:
            #os.path.join(here, '..', 'css', 'static_html.css'),
        #]:
            #header.extend(self._stylesheet(sheet))

        ## pygments css
        #pygments_css = HtmlFormatter().get_style_defs('.highlight')
        #header.extend(['<meta charset="UTF-8">'])
        #header.extend(self.in_tag('style', pygments_css,
                                  #dict(type='"text/css"')))

        ## TODO: this should be allowed to use local mathjax:
        #header.extend(self.in_tag('script', '', {'type': '"text/javascript"',
            #'src': '"https://c328740.ssl.cf1.rackcdn.com/mathjax/'
                   #'latest/MathJax.js?config=TeX-AMS_HTML"',
        #}))
        #with io.open(os.path.join(here, '..', 'js', 'initmathjax.js'),
                     #encoding='utf-8') as f:
            #header.extend(self.in_tag('script', f.read(),
                                      #{'type': '"text/javascript"'}))
        #return header

    #def optional_header(self):
        #return ['<html>', '<head>'] + self.header_body() + \
          #['</head>', '<body>']

    #def optional_footer(self):
        #return ['</body>', '</html>']

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
                    self.in_tag('pre', cell.source)]  # testing
        else:
            return [self.meta2str(cell.metadata), cell.source]

    #@output_container
    #def render_pyout(self, output):
        #for fmt in ['html', 'latex', 'png', 'jpeg', 'svg', 'text']:
            #if fmt in output:
                #conv_fn = self.dispatch_display_format(fmt)
                #return conv_fn(output)
        #return []

    #render_display_data = render_pyout

    #@output_container
    #def render_stream(self, output):
        #return self._ansi_colored(output.text)

    #@output_container
    #def render_pyerr(self, output):
        ## Note: a traceback is a *list* of frames.
        ## lines = []

        ## stb =
        #return self._ansi_colored('\n'.join(output.traceback))

    #def _img_lines(self, img_file):
        #return ['<img src="%s">' % img_file, '</img>']

    #def _unknown_lines(self, data):
        #return ['<h2>Warning:: Unknown cell</h2>'] + self.in_tag('pre', data)

    #def render_display_format_png(self, output):
        #return ['<img src="data:image/png;base64,%s"></img>' % output.png]

    #def render_display_format_svg(self, output):
        #return [output.svg]

    #def render_display_format_jpeg(self, output):
        #return ['<img src="data:image/jpeg;base64,%s"></img>' % output.jpeg]

    #def render_display_format_text(self, output):
        #return self._ansi_colored(output.text)

    #def render_display_format_html(self, output):
        #return [output.html]

    #def render_display_format_latex(self, output):
        #return [output.latex]

    #def render_display_format_json(self, output):
        ## html ignores json
        #return []

    #def render_display_format_javascript(self, output):
        #return [output.javascript]

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
                      u'slide_type = header_slide',
                      u'slide_type = slide',
                      u'slide_type = fragment',
                      u'slide_type = skip']
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
                else:
                    text[i - 1] = self.delim[5]
                text[i] = text_cell_render
        text[0] = u'slide_type = header_slide'  # defensive code
        text.append(u'slide_type = untouched')  # to end search of skipped
        return text

    def build_slides(self):
        "build the slides structure from text list and delimiters"
        text = self.clean_text()
        left = '<section>'
        right = '</section>'
        set_delim = self.delim[:5]
        #elimination of skipped cells
        for i, j in enumerate(text):
            if j == u'slide_type = skip':
                text.pop(i)
                while not text[i] in set_delim:
                    text.pop(i)
        # elimination of none names
        for i, j in enumerate(text):
            if j in [u'slide_type = untouched', u'slide_type = -']:
                text.pop(i)
        #generation of slides as a list of list
        slides = [list(x[1]) for x in itertools.groupby(text,
            lambda x: x == u'slide_type = header_slide') if not x[0]]
        for slide in slides:
            slide.insert(0, left)
            slide.append(right)
            # encapsulation of each fragment
            for i, j in enumerate(slide):
                if j == u'slide_type = fragment':
                    slide.pop(i)
                    slide[i] = slide[i][:4] + ' class="fragment"' + slide[i][4:]
            # encapsulation of each nested slide
            if u'slide_type = slide' in slide:
                slide.insert(0, '<section>')
                slide.append('</section>')
            for i, j in enumerate(slide):
                if j == u'slide_type = slide':
                    slide[i] = right + left
        return list(itertools.chain(*slides))

    def save(self, outfile=None, encoding=None):
        "read and parse notebook into self.nb"
        if outfile is None:
            outfile = self.outbase + '_slides.' + 'html'
        if encoding is None:
            encoding = self.default_encoding
        with io.open(outfile, 'w', encoding=encoding) as f:
            f.write(self.output)
        return os.path.abspath(outfile)

    def template_read(self):
        "read the reveal_template.html"
        here = os.path.split(os.path.realpath(__file__))[0]
        reveal_template = os.path.join(here, '..', 'templates',
            'reveal_base.html')
        with io.open(reveal_template, 'r', encoding='utf-8') as f:
            template = f.readlines()
        template = [s.strip() for s in template]
        return template

    def template_split(self):
        "split the reveal_template.html in header and footer lists"
        temp = self.template_read()
        splitted_temp = [list(x[1]) for x in itertools.groupby(temp,
            lambda x: x == u'%slides%') if not x[0]]
        return splitted_temp

    def optional_header(self):
        optional_header_body = self.template_split()
        return optional_header_body[0]

    def optional_footer(self):
        optional_footer_body = self.template_split()
        return optional_footer_body[1]