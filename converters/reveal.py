from converters.markdown import ConverterMarkdown
import io
import os

class ConverterReveal(ConverterMarkdown):
    """Convert a notebook to a html slideshow.

    It generates a static html slideshow based in markdown and reveal.js. 
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
        top = '<section data-markdown><script type="text/template">'
        bottom = '</script></section>'
        text = self.main_body(cell_separator)
        for i,j in enumerate(text):
            if j == u'---':
                text[i] = bottom + top 
        lines.extend(text)
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
        text.append(u'slide_type = untouched')  # to end search of skipped
        return text

    def build_slides(self):
        "build the slides structure from text list and delimiters"
        text = self.clean_text()
        left = '<section>'
        right = '</section>'
        notes_start = '<aside class="notes">'
        notes_end = '</aside>'
        set_delim_skip = self.delim[:6]  # to skip adjacent skkiped cells
        #elimination of skipped cells
        for i, j in enumerate(text):
            if j == u'slide_type = skip':
                text.pop(i)
                while not text[i] in set_delim_skip:
                    text.pop(i)
        #encapsulation of notes cells
        for i, j in enumerate(text):
            if j == u'slide_type = notes':
                text.pop(i)
                temp_list = []
                while not text[i] in set_delim_skip:
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

    def optional_header(self):
        optional_header_body = [\
'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta http-equiv="X-UA-Compatible" content="chrome=1">

    <meta name="apple-mobile-web-app-capable" content="yes" />
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />

    <link rel="stylesheet" href="reveal/css/reveal.css">
    <link rel="stylesheet" href="reveal/css/theme/default.css" id="theme">

    <!-- For syntax highlighting -->
    <link rel="stylesheet" href="reveal/lib/css/zenburn.css">

    <!-- If the query includes 'print-pdf', use the PDF print sheet -->
    <script>
        document.write( '<link rel="stylesheet" href="reveal/css/print/' + ( window.location.search.match( /print-pdf/gi ) ? 'pdf' : 'paper' ) + '.css" type="text/css" media="print">' );
    </script>

    <!--[if lt IE 9]>
    <script src="reveal/lib/js/html5shiv.js"></script>
    <![endif]-->

</head>
<body><div class="reveal"><div class="slides">
<section data-markdown><script type="text/template">
'''] 
        return optional_header_body

    def optional_footer(self):
        optional_footer_body = [\
'''
</script></section>
</div></div>

    <script src="reveal/lib/js/head.min.js"></script>

    <script src="reveal/js/reveal.min.js"></script>

    <script>

        // Full list of configuration options available here: https://github.com/hakimel/reveal.js#configuration
        Reveal.initialize({
            controls: true,
            progress: true,
            history: true,

            theme: Reveal.getQueryHash().theme, // available themes are in /css/theme
            transition: Reveal.getQueryHash().transition || 'page', // default/cube/page/concave/zoom/linear/none

            // Optional libraries used to extend on reveal.js
            dependencies: [
                { src: 'reveal/lib/js/classList.js', condition: function() { return !document.body.classList; } },
                { src: 'reveal/plugin/markdown/showdown.js', condition: function() { return !!document.querySelector( '[data-markdown]' ); } },
                { src: 'reveal/plugin/markdown/markdown.js', condition: function() { return !!document.querySelector( '[data-markdown]' ); } },
                { src: 'reveal/plugin/highlight/highlight.js', async: true, callback: function() { hljs.initHighlightingOnLoad(); } },
                { src: 'reveal/plugin/zoom-js/zoom.js', async: true, condition: function() { return !!document.body.classList; } },
                { src: 'reveal/plugin/notes/notes.js', async: true, condition: function() { return !!document.body.classList; } },
                { src: 'https://c328740.ssl.cf1.rackcdn.com/mathjax/latest/MathJax.js?config=TeX-AMS_HTML', async: true },                                     
                { src: 'js/initmathjax.js', async: true}
                ]
                });
    </script>

    <script>
        Reveal.addEventListener( 'slidechanged', function( event ) {   
        MathJax.Hub.Rerender();
        });
    </script>

</body>
</html>
''']
        return optional_footer_body
