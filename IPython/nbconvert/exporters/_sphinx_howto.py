"""
Exporter for exporting notebooks to Sphinx 'HowTo' style latex.  Latex 
formatted for use with PDFLatex.
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

from IPython.utils.traitlets import Unicode, List
from IPython.config import Config

# local import
from .latex import LatexExporter

from IPython.nbconvert import transformers

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class SphinxHowtoExporter(LatexExporter):
    """
    Exports Sphinx "HowTo" LaTeX documents.  The Sphinx "HowTo" exporter 
    produces short document format latex for use with PDFLatex.
    """
    
    template_file = Unicode(
            'sphinx_howto', config=True,
            help="Name of the template file to use")

    
    @property
    def default_config(self):
        c = Config({'SphinxTransformer': {'enabled':True}})
        c.merge(super(SphinxHowtoExporter,self).default_config)
        return c
