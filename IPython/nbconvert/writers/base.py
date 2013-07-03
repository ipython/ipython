#!/usr/bin/env python
"""
Contains writer base class.
"""
#-----------------------------------------------------------------------------
#Copyright (c) 2013, the IPython Development Team.
#
#Distributed under the terms of the Modified BSD License.
#
#The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from ..transformers.extractfigure import FIGURES_KEY
from ..utils.config import GlobalConfigurable

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class WriterBase(GlobalConfigurable):
    """Consumes output from nbconvert export...() methods and writes to a
    useful location. """


    def __init__(self, config=None, **kw):
        """
        Constructor
        """
        super(WriterBase, self).__init__(config=config, **kw)


    def write(self, notebook_name, output_extension, output, resources, 
              referenced_files=[]):
        """
        Consume and write Jinja output.

        Parameters
        ----------
        notebook_filename : string
            Name of the notebook file that was converted.
        output_extension : string
            Extension to give the output when written to the destination.
        output : string
            Conversion results.  This string contains the file contents of the
            converted file.
        resources : dict
            Resources created and filled by the nbconvert conversion process.
            Includes output from transformers, such as the extract figure 
            transformer.
        referenced_files : list [of string]
            List of the files that the notebook references.  Files will be 
            included with written output.
        """

        raise NotImplementedError()


    def _get_extracted_figures(self, resources):
        """
        Get the figures extracted via the extract figures transformer.

        Parameters
        ----------
        resources : dict
            Resources created and filled by the nbconvert conversion process.
            Includes output from transformers, such as the extract figure 
            transformer.
        """
        
        if FIGURES_KEY in resources:
            return resources[FIGURES_KEY]
        else:
            return {}
