"""Module that pre-processes the notebook for export to HTML.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
import os
import io
import shutil

from IPython.utils.traitlets import Unicode, Bool
from .base import Preprocessor

class InlineHTMLPreprocessor(Preprocessor):
    """Preprocessor used to pre-process notebooks for HTML output.  

    Adds IPython notebook front-end CSS, Pygments CSS, and Widget JS to the 
    resources dictionary."""

    highlight_class = Unicode('.highlight', config=True, help="CSS highlight class identifier")
    inline_js = Bool(False, config=True, help="Inline IPython JS")

    css = []
    js_code = [] # (filename, contents)
    js_urls = []

    def preprocess(self, nb, resources):
        """Fetch and add CSS & JS to the resource dictionary

        Fetch CSS from IPython and Pygments to add at the beginning
        of the html files.  Add this css in resources in the 
        "inlining.css" key.  Add either CDN/local references to JS or inline
        the required JS too.
        
        Parameters
        ----------
        nb : NotebookNode
            Notebook being converted
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            preprocessors to pass variables into the Jinja engine.
        """
        # Look through the notebook to see if any widgets are displayed.  If at
        # least one widget is displayed somewhere, we should include the widget
        # JS one way or another.
        has_widgets = False
        for worksheet in nb.worksheets:
            for cell in worksheet.cells:
                has_widgets = 'widgets' in cell and len(cell['widgets']) > 0
                if has_widgets: break
            if has_widgets: break

        # Inlined CSS
        self._generate_css(has_widgets)
        resources['inlining'] = {}
        resources['inlining']['css'] = self.css

        # Inlined/referenced JS
        resources = self._generate_js(has_widgets, resources)
        if len(self.js_code) > 0:
            resources['inlining']['js'] = self.js_code
        if len(self.js_urls) > 0:
            resources['references'] = {}
            resources['references']['js'] = self.js_urls
        return nb, resources

    def _generate_css(self, has_widgets):
        """Fills self.css with lines of CSS extracted from IPython 
        and Pygments.
        """
        from pygments.formatters import HtmlFormatter
        css = []
        
        # Load IPython CSS dependencies.
        from IPython.html import DEFAULT_STATIC_FILES_PATH
        paths = [('style', 'style.min.css')]
        if has_widgets:
            paths.append(('components', 'jquery-ui', 'themes', 'smoothness', 'jquery-ui.min.css'))
            
        for path in paths:
            sheet_filename = os.path.join(DEFAULT_STATIC_FILES_PATH, *path)
            with io.open(sheet_filename, encoding='utf-8') as f:
                css.append(f.read())

        # Add pygments CSS
        formatter = HtmlFormatter()
        pygments_css = formatter.get_style_defs(self.highlight_class)
        css.append(pygments_css)

        # Set css        
        self.css = css

    def _generate_js(self, has_widgets, resources):
        """Fills self.js_code with the widget JS.
        """
        from IPython.html import DEFAULT_STATIC_FILES_PATH
        if has_widgets:
            src_staticwidgets = os.path.join(DEFAULT_STATIC_FILES_PATH, 'widgets', 'js', 'staticwidgets.min.js')
                
        self.js_urls = []
        self.js_code = []
        if self.inline_js:
            # Inline require.min.js & jquery.min.js
            for path in [
                ('components', 'requirejs', 'require.js'),
                ('components', 'jquery', 'jquery.min.js')]:
                with io.open(os.path.join(DEFAULT_STATIC_FILES_PATH, *path), encoding='utf-8') as f:
                    self.js_code.append((path[-1] ,f.read()))

            # Inline staticwidgets.min.js
            if has_widgets:
                with io.open(src_staticwidgets, encoding='utf-8') as f:
                    self.js_code.append(('IPython static widgets', f.read()))

            else:
            self.js_urls += [
            "https://cdnjs.cloudflare.com/ajax/libs/require.js/2.1.10/require.min.js",
            "https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js",
            ]

            if has_widgets:
                dest_staticwidgets = 'staticwidgets.min.js'

                #Make sure outputs key exists
                if not isinstance(resources['outputs'], dict):
                    resources['outputs'] = {}

                with open(src_staticwidgets, 'rb') as f:
                    resources['outputs'][dest_staticwidgets] = f.read()
                self.js_urls.append(dest_staticwidgets)
        return resources
