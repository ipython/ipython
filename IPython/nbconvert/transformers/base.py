"""
Module that re-groups transformer that would be applied to ipynb files
before going through the templating machinery.

It exposes a convenient class to inherit from to access configurability.
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

from ..utils.base import NbConvertBase
from IPython.utils.traitlets import Bool

#-----------------------------------------------------------------------------
# Classes and Functions
#-----------------------------------------------------------------------------

class Transformer(NbConvertBase):
    """ A configurable transformer

    Inherit from this class if you wish to have configurability for your
    transformer.

    Any configurable traitlets this class exposed will be configurable in profiles
    using c.SubClassName.atribute=value

    you can overwrite :meth:`transform_cell` to apply a transformation independently on each cell
    or :meth:`call` if you prefer your own logic. See corresponding docstring for informations.

    Disabled by default and can be enabled via the config by
        'c.YourTransformerName.enabled = True'
    """
    
    enabled = Bool(False, config=True)

    def __init__(self, **kw):
        """
        Public constructor
        
        Parameters
        ----------
        config : Config
            Configuration file structure
        **kw : misc
            Additional arguments
        """
        
        super(Transformer, self).__init__(**kw)

       
    def __call__(self, nb, resources):
        if self.enabled:
            return self.call(nb,resources)
        else:
            return nb, resources


    def call(self, nb, resources):
        """
        Transformation to apply on each notebook.
        
        You should return modified nb, resources.
        If you wish to apply your transform on each cell, you might want to 
        overwrite transform_cell method instead.
        
        Parameters
        ----------
        nb : NotebookNode
            Notebook being converted
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            transformers to pass variables into the Jinja engine.
        """
        self.log.debug("Applying transform: %s", self.__class__.__name__)
        try :
            for worksheet in nb.worksheets:
                for index, cell in enumerate(worksheet.cells):
                    worksheet.cells[index], resources = self.transform_cell(cell, resources, index)
            return nb, resources
        except NotImplementedError:
            raise NotImplementedError('should be implemented by subclass')


    def transform_cell(self, cell, resources, index):
        """
        Overwrite if you want to apply a transformation on each cell.  You 
        should return modified cell and resource dictionary.
        
        Parameters
        ----------
        cell : NotebookNode cell
            Notebook cell being processed
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            transformers to pass variables into the Jinja engine.
        index : int
            Index of the cell being processed
        """

        raise NotImplementedError('should be implemented by subclass')
        return cell, resources

