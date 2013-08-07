"""Module that pre-processes the notebook for export to HTML.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import io

from pygments.formatters import HtmlFormatter

from IPython.utils import path

from .base import Transformer

from IPython.utils.traitlets import Unicode

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class CSSHTMLHeaderTransformer(Transformer):
    """
    Transformer used to pre-process notebook for HTML output.  Adds IPython notebook
    front-end CSS and Pygments CSS to HTML output.
    """

    header = []

    highlight_class = Unicode('.highlight', config=True,
                              help="CSS highlight class identifier")

    def __init__(self, config=None, **kw):
        """
        Public constructor
        
        Parameters
        ----------
        config : Config
            Configuration file structure
        **kw : misc
            Additional arguments
        """
        
        super(CSSHTMLHeaderTransformer, self).__init__(config=config, **kw)

        if self.enabled :
            self._regen_header()


    def call(self, nb, resources):
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
            transformers to pass variables into the Jinja engine.
        """
        
        resources['inlining'] = {}
        resources['inlining']['css'] = self.header
        
        return nb, resources


    def _regen_header(self):
        """ 
        Fills self.header with lines of CSS extracted from IPython 
        and Pygments.
        """
        
        #Clear existing header.
        header = []
        
        #Construct path to IPy CSS
        sheet_filename = os.path.join(path.get_ipython_package_dir(), 
            'html', 'static', 'style', 'style.min.css')
        
        #Load style CSS file.
        with io.open(sheet_filename, encoding='utf-8') as file:
            file_text = file.read()
            header.append(file_text)

        #Add pygments CSS
        formatter = HtmlFormatter()
        pygments_css = formatter.get_style_defs(self.highlight_class)
        header.append(pygments_css)

        #Set header        
        self.header = header

