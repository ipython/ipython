"""Module that pre-processes the notebook for export to HTML.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import warnings
import os
import io
import hashlib
from io import TextIOWrapper, BytesIO

from IPython.utils import path
from IPython.utils.traitlets import Unicode, Bool
from IPython.utils.py3compat import str_to_bytes

from .base import Preprocessor
from ..utils.node import get_node_cmd, NodeJSMissing

class InlineHTMLPreprocessor(Preprocessor):
    """Preprocessor used to pre-process notebooks for HTML output.  

    Adds IPython notebook front-end CSS, Pygments CSS, and Widget JS to the 
    resources dictionary."""

    highlight_class = Unicode('.highlight', config=True,
                              help="CSS highlight class identifier")

    def __init__(self, *pargs, **kwargs):
        Preprocessor.__init__(self, *pargs, **kwargs)
        self._default_css_hash = None

    def preprocess(self, nb, resources):
        """Fetch and add CSS to the resource dictionary

        Fetch CSS from IPython and Pygments to add at the beginning
        of the html files.  Add this css in resources in the 
        "inlining.css" key
        
        Parameters
        ----------
        nb : NotebookNode
            Notebook being converted
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            preprocessors to pass variables into the Jinja engine.
        """
        resources['inlining'] = {}
        resources['inlining']['css'] = self._generate_css(resources)
        js = self._generate_js()
        if js and len(js) > 0:
            resources['inlining']['js'] = js
        return nb, resources

    def _generate_css(self, resources):
        """Fills self.css with lines of CSS extracted from IPython 
        and Pygments.
        """
        from pygments.formatters import HtmlFormatter
        css = []
        
        # Construct path to IPy CSS
        from IPython.html import DEFAULT_STATIC_FILES_PATH
        sheet_filename = os.path.join(DEFAULT_STATIC_FILES_PATH,
            'style', 'style.min.css')
        
        # Load style CSS file.
        with io.open(sheet_filename, encoding='utf-8') as f:
            css.append(f.read())

        # Add pygments CSS
        formatter = HtmlFormatter()
        pygments_css = formatter.get_style_defs(self.highlight_class)
        css.append(pygments_css)

        # Load the user's custom CSS and IPython's default custom CSS.  If they
        # differ, assume the user has made modifications to his/her custom CSS
        # and that we should inline it in the nbconvert output.
        profile_dir = resources['profile_dir']
        custom_css_filename = os.path.join(profile_dir, 'static', 'custom', 'custom.css')
        if os.path.isfile(custom_css_filename):
            if self._default_css_hash is None:
                self._default_css_hash = self._hash(os.path.join(DEFAULT_STATIC_FILES_PATH, 'custom', 'custom.css'))
            if self._hash(custom_css_filename) != self._default_css_hash:
                with io.open(custom_css_filename, encoding='utf-8') as f:
                    css.append(f.read())

        return css

    def _generate_js(self):
        """Fills self.js with the widget JS.
        """
        js = []
        if self.inline_js:

            global _node
            if not _node:
                _node = get_node_cmd()

            # Run r.js on the widget init file to build a single, minimized js
            # file containing all of the JS that needs to be embeded on the 
            # page.
            ipythonjs = '.ipython.js'
            if not _node:
                warnings.warn("Node.js not found.  Cannot inline notebook JS.  " +
                    "Using CDN references instead (inline_js=False).")
            else:
                # Embed require.js
                from IPython.html import DEFAULT_STATIC_FILES_PATH
                with open(os.path.join(DEFAULT_STATIC_FILES_PATH, 'components', 'requirejs', 'require.js'), 'r') as f:
                    js.append(('require.js', f.read()))

                # CD into the static files path.  Remember the current path so
                # we can direct the output to it.
                cwd = os.getcwd()
                try:
                    os.chdir(DEFAULT_STATIC_FILES_PATH)

                    command = [
                        _node, 
                        os.path.join('components', 'r.js', 'dist', 'r.js'),
                        '-o',
                        'build.js',
                        'out=' + os.path.join(cwd, ipythonjs),
                    ]
                    try:
                        out, err, return_code = get_output_error_code(command)
                    except OSError as e:
                        # Command not found
                        warnings.warn("The command '%s' returned an error: %s.\n" % (" ".join(command), e) +
                            "Please check that Node.js is installed."
                        )
                    if return_code:
                        # Command error
                        warnings.warn("The command '%s' returned an error code: %s.\n" % (" ".join(command), return_code))

                    # Log r.js output.
                    from IPython.config import Application
                    if Application.initialized():
                        Application.instance().log.info("node r.js output")
                        for line in out.strip().split('\n'):
                            Application.instance().log.info("    %s" % line)
                finally:
                    # Return to original path.
                    os.chdir(cwd)
                    
                # Read the file into the JS dict.
                with open(ipythonjs, 'r') as f:
                    js.append((ipythonjs, f.read()))
                os.remove(ipythonjs)
        return js

    def _hash(self, filename):
        """Compute the hash of a file."""
        md5 = hashlib.md5()
        with open(filename) as f:
            md5.update(str_to_bytes(f.read()))
        return md5.digest()
