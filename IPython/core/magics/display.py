"""Simple magics for display formats"""
#-----------------------------------------------------------------------------
#  Copyright (c) 2012 The IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Our own packages
from IPython.core.display import display, Javascript, Latex, SVG
from IPython.core.magic import  (
    Magics, magics_class, cell_magic
)

#-----------------------------------------------------------------------------
# Magic implementation classes
#-----------------------------------------------------------------------------


@magics_class
class DisplayMagics(Magics):
    """Magics for displaying various output types with literals
    
    Defines javascript/latex cell magics for writing blocks in those languages,
    to be rendered in the frontend.
    """
    
    @cell_magic
    def javascript(self, line, cell):
        """Run the cell block of Javascript code"""
        display(Javascript(cell))
        
    
    @cell_magic
    def latex(self, line, cell):
        """Render the cell as a block of latex"""
        display(Latex(cell))

    @cell_magic
    def svg(self, line, cell):
        """Render the cell as an SVG literal"""
        display(SVG(cell))
