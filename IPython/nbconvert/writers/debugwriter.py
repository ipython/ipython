#!/usr/bin/env python
"""
Contains debug writer.
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

from .base import WriterBase
from pprint import pprint

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class DebugWriter(WriterBase):
    """Consumes output from nbconvert export...() methods and writes usefull
    debugging information to the stdout.  The information includes a list of
    resources that were extracted from the notebook(s) during export."""


    def write(self, notebook_name, output_extension, output, resources):
        """
        Consume and write Jinja output.

        See base for more...
        """

        if 'figures' in resources:
            print("Figures extracted from %s" % notebook_name)
            print('-' * 80)
            pprint.pprint(resources['figures'], indent=2, width=70)
        else:
            print("No figures extracted from %s" % notebook_name)
        print('=' * 80)
