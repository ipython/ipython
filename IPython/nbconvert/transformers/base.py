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

from ..utils.config import GlobalConfigurable

#-----------------------------------------------------------------------------
# Classes and Functions
#-----------------------------------------------------------------------------

class ConfigurableTransformer(GlobalConfigurable):
    """ A configurable transformer

    Inherit from this class if you wish to have configurability for your
    transformer.

    Any configurable traitlets this class exposed will be configurable in profiles
    using c.SubClassName.atribute=value

    you can overwrite cell_transform to apply a transformation independently on each cell
    or __call__ if you prefer your own logic. See corresponding docstring for informations.
    """
    
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
        
        super(ConfigurableTransformer, self).__init__(config=config, **kw)

       
    def __call__(self, nb, resources):
        return self.call(nb,resources)

    def call(self, nb, resources):
        """
        Transformation to apply on each notebook.
        
        You should return modified nb, resources.
        If you wish to apply your transform on each cell, you might want to 
        overwrite cell_transform method instead.
        
        Parameters
        ----------
        nb : NotebookNode
            Notebook being converted
        resources : dictionary
            Additional resources used in the conversion process.  Allows
            transformers to pass variables into the Jinja engine.
        """
        try :
            for worksheet in nb.worksheets :
                for index, cell in enumerate(worksheet.cells):
                    worksheet.cells[index], resources = self.cell_transform(cell, resources, index)
            return nb, resources
        except NotImplementedError:
            raise NotImplementedError('should be implemented by subclass')


    def cell_transform(self, cell, resources, index):
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

