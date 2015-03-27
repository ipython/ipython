"""
Contains debug writer.
"""
from __future__ import print_function
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

from .base import WriterBase
from pprint import pprint

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class DebugWriter(WriterBase):
    """Consumes output from nbconvert export...() methods and writes usefull
    debugging information to the stdout.  The information includes a list of
    resources that were extracted from the notebook(s) during export."""


    def write(self, output, resources, notebook_name='notebook', **kw):
        """
        Consume and write Jinja output.

        See base for more...
        """

        if isinstance(resources['outputs'], dict):
            print("outputs extracted from %s" % notebook_name)
            print('-' * 80)
            pprint(resources['outputs'], indent=2, width=70)
        else:
            print("no outputs extracted from %s" % notebook_name)
        print('=' * 80)
