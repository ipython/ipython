
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

# local import
import latex
from IPython.utils.traitlets import Unicode
from transformers.sphinx import SphinxTransformer
#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class SphinxExporter(latex.LatexExporter):

    template_file = Unicode(
            'sphinxhowto', config=True,
            help="Name of the template file to use")
    
    def _register_transformers(self):
        
        #Register the transformers of the base class.
        super(latex.LatexExporter, self)._register_transformers()
        
        #Register sphinx latex transformer
        self.register_transformer(SphinxTransformer) 
                    
