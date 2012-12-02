from converters.markdown import ConverterMarkdown
import io
import os

class ConverterSlider(ConverterMarkdown):
    """Convert a notebook to a html slideshow suitable for oral presentations.

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
