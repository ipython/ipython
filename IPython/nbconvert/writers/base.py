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
#Classes
#-----------------------------------------------------------------------------

class WriterBase(object):
    """Consumes output from nbconvert export...() methods and writes to a
    useful location. """

    def __init__(self):
        super(WriterBase, self).__init__()

    def write(self, notebook_filename, output_extension, output, resources):
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
        
        if 'figures' in resources:
            return resources['figures']
        else:
            return {}
