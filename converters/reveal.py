from converters.markdown import ConverterMarkdown
from IPython.utils.text import indent
import io
import os
import itertools

class ConverterReveal(ConverterMarkdown):
    """
    Convert a notebook to a html slideshow.

    It generates a static html slideshow based in markdown and reveal.js.
    The delimiters for each slide, subslide, and fragment are retrieved
    from the 'slideshow' metadata.
    """

    def __init__(self, infile, highlight_source=False, show_prompts=True,
                 inline_prompt=True):
        super(ConverterReveal, self).__init__(infile)
        self.highlight_source = highlight_source
        self.show_prompts = show_prompts
        self.inline_prompt = inline_prompt

    def switch_meta(self, m_list):
        "sort order m_list to [new_section, new_subsection, new_fragment]"
        if len(m_list) > 1:
        # do not sort when m_list = [new_subsection, new_fragment]
            if not (len(m_list) == 2 and m_list[1] == [u'new_fragment = True']):
                m_list[0], m_list[1] = m_list[1], m_list[0]
        return m_list

    def meta2str(self, meta):
        "transform metadata dict (containing slides delimiters) to string "
        try:
            meta_tuple = meta[u'slideshow'].items()
        except KeyError as e:
            meta_tuple = ()  # if there is not slideshow metadata
        meta_list = [[x + ' = ' + unicode(y)] for x, y in meta_tuple]
        meta_list = self.switch_meta(meta_list)
        return u'\n'.join(list(itertools.chain(*meta_list)))

    def render_heading(self, cell):
        return [self.meta2str(cell.metadata),
            '{0} {1}'.format('#' * cell.level, cell.source), '']

    def render_code(self, cell):
        if not cell.input:
            return []
        lines = []
        meta_code = self.meta2str(cell.metadata)
        lines.extend([meta_code])
        lines.extend(['<!-- hack -->'])  # to be proper parsed         
        n = self._get_prompt_number(cell)
        if self.show_prompts and not self.inline_prompt:
            lines.extend(['*In[%s]:*' % n, ''])
        if self.show_prompts and self.inline_prompt:
            prompt = 'In[%s]: ' % n
            input_lines = cell.input.split('\n')
            src = (prompt + input_lines[0] + '\n' +
                   indent('\n'.join(input_lines[1:]), nspaces=len(prompt)))
        else:
            src = cell.input
        src = highlight(src) if self.highlight_source else indent(src)
        lines.extend([src, ''])
        if cell.outputs and self.show_prompts and not self.inline_prompt:
            lines.extend(['*Out[%s]:*' % n, ''])
        for output in cell.outputs:
            conv_fn = self.dispatch(output.output_type)
            lines.extend(conv_fn(output))
        #lines.append('')
        return lines

    def render_markdown(self, cell):
        return [self.meta2str(cell.metadata), cell.source, '']

    def render_raw(self, cell):
        if self.raw_as_verbatim:
            return [indent(self.meta2str(cell.metadata)),
                indent(cell.source), '']
        else:
            return [self.meta2str(cell.metadata), cell.source, '']

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
        slides_list = self.build_slides(cell_separator)
        lines.extend(slides_list)
        end = ['</div></div>']
        lines.extend(end)
        lines.extend(self.optional_footer())
        return u'\n'.join(lines)

    def build_slides(self, cell_separator='\n'):
        "build the slides structure from text list and delimiters"
        text = self.main_body(cell_separator)
        delim_false = [u'new_section = False',
                       u'new_subsection = False',
                       u'new_fragment = False']
        text = [x for x in text if not x in delim_false]
        left = '<section data-markdown><script type="text/template">'
        right = '</script></section>'
        # build lists representing each slide delimited by new_section
        slides = [list(x[1]) for x in itertools.groupby(text,
            lambda x: x == u'new_section = True') if not x[0]]
        for slide in slides:
            slide.insert(0, u'')  # for proper interline in html file
            slide.insert(0, left)
            slide.append(right)
            # build each vertical slide delimited by new_subsection
            if slide[2] == u'new_subsection = True':
                slide.pop(2)
                slide.insert(0, '<section>')
                slide.append('</section>')
                for i, j in enumerate(slide):
                    if j == u'new_subsection = True':
                        slide[i] = right + left
                        slide.insert(i + 1, u'')  # for proper interline
            #defensive: if user do not begin new_subsection with a new_section
            elif slide[4] == u'new_subsection = True':
                slide[4] = right
                slide.insert(5, u'')  # for proper interline
                slide.insert(5, left)
                slide.insert(5, '<section>')
                slide.append('</section>')
                for i, j in enumerate(slide):
                    if j == u'new_subsection = True':
                        slide[i] = right + left
                        slide.insert(i + 1, u'')  # for proper interline
            # build each fragment delimited by new_fragment
            for i, j in enumerate(slide):
                if j == u'new_fragment = True':
                    slide[i] = '<p class="fragment">'
                    slide[i + 2] = '</p>'
                    slide.insert(i + 3, u'')  # for proper interline
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

