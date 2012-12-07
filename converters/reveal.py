from converters.markdown import ConverterMarkdown
import io
import os
import itertools

class ConverterReveal(ConverterMarkdown):
    """Convert a notebook to a html slideshow.

    It generates a static html slideshow based in markdown and reveal.js.
    You have four ways to delimit the the slides: 
    ##--- delimit horizontal slides
    ##<<< open vertical slides
    ##>>> close vertical slides
    ##>>><<< close vertical slides and open new vertical slides. 
    """

    def __init__(self, infile, highlight_source=False, show_prompts=True,
                 inline_prompt=True):
        super(ConverterMarkdown, self).__init__(infile)
        self.highlight_source = highlight_source
        self.show_prompts = show_prompts
        self.inline_prompt = inline_prompt

    def convert(self, cell_separator='\n'):
        """
        Generic method to converts notebook to a string representation.

        This is accomplished by dispatching on the cell_type, so subclasses of
        Convereter class do not need to re-implement this method, but just
        need implementation for the methods that will be dispatched.

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
        start = ['<div class="reveal"><div class="slides"><section data-markdown><script type="text/template">']
        lines.extend(start)
        text = self.main_body(cell_separator)
        left = '<section data-markdown><script type="text/template">'
        right = '</script></section>'
        for i,j in enumerate(text):
            if j == u'##---':
                text[i] = right + left
            if j == u'##<<<':
                text[i] = right + '<section>' + left
            if j == u'##>>>':
                text[i] = right + '</section>' + left
            if j == u'##>>><<<':
                text[i] = right + '</section><section>' + left
        lines.extend(text)
        end = ['</script></section></div></div>']
        lines.extend(end)
        lines.extend(self.optional_footer())
        return u'\n'.join(lines)

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
        reveal_template = os.path.join(here, '..', 'templates', 'reveal_base.html')
        with io.open(reveal_template, 'r', encoding='utf-8') as f:
            template = f.readlines()
        template = map(lambda s: s.strip(), template) # cosmetic one to get short html files
        return template

    def template_split(self):
        "split the reveal_template.html in header and footer lists"
        temp = self.template_read()
        splitted_temp = [list(x[1]) for x in itertools.groupby(temp, lambda x: x==u'%slides%') if not x[0]]
        return splitted_temp  

    def optional_header(self):
        optional_header_body = self.template_split()
        return optional_header_body[0]

    def optional_footer(self):
        optional_footer_body = self.template_split()
        return optional_footer_body[1]
