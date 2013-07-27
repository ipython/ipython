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

from IPython.utils.traitlets import List

from ..utils.base import NbConvertBase

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class WriterBase(NbConvertBase):
    """Consumes output from nbconvert export...() methods and writes to a
    useful location. """


    files = List([], config=True, help="""
        List of the files that the notebook references.  Files will be 
        included with written output.""")


    def __init__(self, config=None, **kw):
        """
        Constructor
        """
        super(WriterBase, self).__init__(config=config, **kw)


    def write(self, output, resources, **kw):
        """
        Consume and write Jinja output.

        Parameters
        ----------
        output : string
            Conversion results.  This string contains the file contents of the
            converted file.
        resources : dict
            Resources created and filled by the nbconvert conversion process.
            Includes output from transformers, such as the extract figure 
            transformer.
        """

        raise NotImplementedError()
